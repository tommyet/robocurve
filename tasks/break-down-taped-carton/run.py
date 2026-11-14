"""Native free-carton crease/stability probe. No robot completion is claimed."""
import argparse,os,json,shutil,hashlib
from pathlib import Path
from config import *
from scene import layout

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',choices=['dynamics','grip-probe'],default='dynamics');p.add_argument('--unsealed',action='store_true',help='Explicit unscored starting condition for folding diagnostics');a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False);(a.out/'source').mkdir()
 for f in Path(__file__).parent.glob('*.py'):shutil.copy2(f,a.out/'source'/f.name)
 (a.out/'source-sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in Path(__file__).parent.glob('*.py')},indent=2))
 os.environ.setdefault('OMNI_KIT_ACCEPT_EULA','YES')
 from isaaclab.app import AppLauncher
 app=AppLauncher(headless=True,enable_cameras=True).app;video=None
 try:
  import numpy as np,torch,cv2,imageio.v2 as imageio
  from yam_arena import inspect_embodiment as wrapper
  from yam_arena import scene as sc
  from yam_arena.urdf import quat_xyzw_to_matrix
  import isaaclab.sim as sim
  from native import export,install_joints
  import task
  wrapper._APP=app;parts,hs=layout();byname={s['name']:s for s in parts};assets={s.name:export(a.out/(s.name+'.usda'),s.name) for s in task.OBJECTS if s.name!='cutter_pad'};original=sc.task_object
  def make(spec):
   if spec.name not in assets:return original(spec)
   cfg=sim.UsdFileCfg(usd_path=assets[spec.name]);q=byname[spec.name]['quat'] if spec.name in byname else (1,0,0,0)
   if spec.name=='cutter':
    spawn=cfg.func
    def with_joints(path,cfg,translation=None,orientation=None,**kwargs):
     prim=spawn(path,cfg,translation=translation,orientation=orientation,**kwargs);install_joints(prim.GetStage(),str(prim.GetPath()).rsplit('/',1)[0],sealed=not a.unsealed);return prim
    cfg.func=with_joints
   return sc.Object(name=spec.name,object_type=sc.ObjectType.RIGID,spawner_cfg=cfg,initial_pose=sc.Pose(position_xyz=spec.pos,rotation_xyzw=(*q[1:],q[0])))
  sc.task_object=make
  try:
   env=wrapper.YamArenaEmbodiment(task=str(Path(__file__).with_name('task.py')),object_jitter=0.,control_hz=20,headless=True,cam_width=320,cam_height=180);env._ensure_sim(None)
  finally:sc.task_object=original
  base=env._base;env._env.reset();env._instruction='Native carton mechanics probe';env._t=0.
  for name,eye in zip(['top_cam','left_cam','right_cam'],[(.04,-.32,1.25),(.06,.22,1.1),(.07,-.22,1.1)]):base.scene[name].set_world_poses_from_view(torch.tensor([eye],device=base.device),torch.tensor([[.32,0,.81]],device=base.device))
  def arr(v):
   v=v.torch if hasattr(v,'torch') else v
   return v.detach().cpu().numpy()
  def pose(name):return arr(base.arena_world.get_pose_w(name))[0]
  video=imageio.get_writer(str(a.out/'diagnostic.mp4'),fps=20,codec='libx264',pixelformat='yuv420p',macro_block_size=1,ffmpeg_params=['-movflags','+faststart']);worst=0.;minz=10.;bestflat=10.;robot=None
  if a.mode=='grip-probe':
   from robot import CartonGripProbe
   robot=CartonGripProbe(env)
  with (a.out/'trajectory.jsonl').open('w') as trace:
   for step in range(440 if robot else 180):
    phase='settle' if step<60 else 'wall_load' if step<120 else 'release'
    f=(0.,-.25,0.) if phase=='wall_load' and not robot else (0.,0.,0.)
    base.scene['east'].permanent_wrench_composer.set_forces_and_torques_index(forces=torch.tensor([[f]],device=base.device),torques=torch.zeros((1,1,3),device=base.device),is_global=True)
    control=None
    if robot:
     target,control=robot.command(step*.05);phase=control[0]['phase'];action=torch.tensor(target[None,:],device=base.device,dtype=torch.float32)
    else:action=env._ready
    env._env.step(action);env._t=(step+1)*.05
    pp={s['name']:pose(s['name']) for s in parts};rr={n:quat_xyzw_to_matrix(v[3:]) for n,v in pp.items()};sep=0.
    angles={}
    for h in hs:
     pa=pp[h['a']][:3]+rr[h['a']]@np.array(h['anchor_a']);pb=pp[h['b']][:3]+rr[h['b']]@np.array(h['anchor_b']);sep=max(sep,float(np.linalg.norm(pa-pb)))
     rel=rr[h['a']].T@rr[h['b']]
     angles[h['name']]=float(np.degrees(np.arctan2(rel[2,1],rel[1,1]) if h['axis']=='X' else np.arctan2(rel[1,0],rel[0,0])))
    vertices=[]
    for s in parts:
     for x in [-1,1]:
      for y in [-1,1]:
       for z in [-1,1]:vertices.append(pp[s['name']][:3]+rr[s['name']]@(.5*np.array(s['size'])*np.array((x,y,z))))
    vertices=np.array(vertices);low=float(vertices[:,2].min()-TOP);high=float(vertices[:,2].max()-TOP);worst=max(worst,sep);minz=min(minz,low);bestflat=min(bestflat,high-low)
    row={'time':env._t,'phase':phase,'robot_control':control,'poses':{n:v.tolist() for n,v in pp.items()},'angles_deg':angles,'max_crease_separation_m':sep,'lowest_vertex_m':low,'highest_vertex_m':high,'force_N':f};trace.write(json.dumps(row)+'\n')
    if not np.isfinite(vertices).all() or sep>.03:raise RuntimeError('unstable carton/crease failure')
    panels=[cv2.resize(arr(base.scene[n].data.output['rgb'])[0,:,:,:3].astype(np.uint8),(480,270)) for n in ['top_cam','left_cam','right_cam']];canvas=np.zeros((594,960,3),dtype=np.uint8);canvas[36:306,240:720]=panels[0];canvas[306:576,:480]=panels[1];canvas[306:576,480:]=panels[2]
    cv2.putText(canvas,('CARTON ROBOT GRIP PROBE | ' if robot else 'NATIVE CARTON | ')+phase+(' | unsealed diagnostic' if a.unsealed else ' | sealed bottom'),(12,25),cv2.FONT_HERSHEY_SIMPLEX,.57,(255,255,255),1,cv2.LINE_AA);cv2.putText(canvas,('Ordinary robot commands. Rim grip/lift diagnostic, not task completion.' if robot else 'Free rigid panels and physical creases. Force probe, not robot completion.'),(12,590),cv2.FONT_HERSHEY_SIMPLEX,.45,(255,205,120),1,cv2.LINE_AA);video.append_data(canvas)
    if step in (59,119,179):imageio.imwrite(a.out/f'step-{step}.png',canvas)
  result={'diagnostic':True,'task_score':None,'unsealed_start':a.unsealed,'max_crease_separation_m':worst,'lowest_vertex_m':minz,'smallest_height_span_m':bestflat,'checks':{'creases_intact':worst<.004,'above_table':minz>-.004}}
  (a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 except BaseException as error:
  import traceback;traceback.print_exc();(a.out/'error.json').write_text(json.dumps({'error':str(error),'type':type(error).__name__},indent=2));raise
 finally:
  if video is not None:video.close()
  app.close()
if __name__=='__main__':main()
