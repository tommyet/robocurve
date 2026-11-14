"""Native flexible-hair/dryer dynamics probe. No successful robot demo yet."""
import argparse,json,os,shutil,hashlib
from pathlib import Path
from config import *
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False);(a.out/'source').mkdir()
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
  from airflow import HairThermal
  import task
  wrapper._APP=app
  assets={s.name:export(a.out/(s.name+'.usda'),s.name) for s in task.OBJECTS if s.name not in ('mat','dryer_pad')}
  original=sc.task_object
  def make(spec):
   if spec.name not in assets:return original(spec)
   cfg=sim.UsdFileCfg(usd_path=assets[spec.name])
   if spec.name==f'hair_{LOCKS-1}_{SEGMENTS-1}':
    spawn=cfg.func
    def with_joints(path,cfg,translation=None,orientation=None,**kwargs):
     prim=spawn(path,cfg,translation=translation,orientation=orientation,**kwargs);install_joints(prim.GetStage(),str(prim.GetPath()).rsplit('/',1)[0]);return prim
    cfg.func=with_joints
   return sc.Object(name=spec.name,object_type=sc.ObjectType.BASE if spec.name=='head' else sc.ObjectType.RIGID,spawner_cfg=cfg,initial_pose=sc.Pose(position_xyz=spec.pos,rotation_xyzw=(0,0,0,1)))
  sc.task_object=make
  try:
   env=wrapper.YamArenaEmbodiment(task=str(Path(__file__).with_name('task.py')),object_jitter=0.,control_hz=20,headless=True,cam_width=320,cam_height=180);env._ensure_sim(None)
  finally:sc.task_object=original
  base=env._base;env._env.reset();env._instruction='Hair dynamics validation, unscored';env._t=0.
  for name,eye in zip(['top_cam','left_cam','right_cam'],[(.04,-.28,1.32),(.09,.24,1.18),(.10,-.24,1.15)]):base.scene[name].set_world_poses_from_view(torch.tensor([eye],device=base.device),torch.tensor([[.42,0,.99]],device=base.device))
  def arr(v):
   v=v.torch if hasattr(v,'torch') else v
   return v.detach().cpu().numpy()
  def pose(name):return arr(base.arena_world.get_pose_w(name))[0]
  def force(name,f):base.scene[name].permanent_wrench_composer.set_forces_and_torques_index(forces=torch.tensor([[f]],device=base.device,dtype=torch.float32),torques=torch.zeros((1,1,3),device=base.device),is_global=True)
  video=imageio.get_writer(str(a.out/'diagnostic.mp4'),fps=20,codec='libx264',pixelformat='yuv420p',macro_block_size=1,ffmpeg_params=['-movflags','+faststart']);samples=[];thermal=HairThermal();worst_sep=0.;max_motion=0.
  with (a.out/'trajectory.jsonl').open('w') as trace:
   for step in range(180):
    phase='settle' if step<60 else 'lateral_force_probe' if step<100 else 'passive_return'
    force('hair_8_8',(.004 if phase=='lateral_force_probe' else 0.,0,0))
    env._env.step(env._ready);env._t=(step+1)*.05
    segments=[];sep=0.
    for k in range(LOCKS):
     previous=None
     for j in range(SEGMENTS):
      p0=pose(f'hair_{k}_{j}');r=quat_xyzw_to_matrix(p0[3:]);pos=p0[:3];tip0=pos+r@np.array((0,0,LENGTH/2));tip1=pos+r@np.array((0,0,-LENGTH/2))
      sep=max(sep,float(np.linalg.norm(tip0-(np.array(root(k)) if previous is None else previous))));previous=tip1
      segments.append({'pos':pos.tolist(),'rotation':r.tolist()})
    dryer=pose('dryer');switch=pose('switch');r=quat_xyzw_to_matrix(dryer[3:]);local=r.T@(switch[:3]-dryer[:3]);power=float(np.clip((local[2]+.055)/SWITCH_TRAVEL,0,1))
    m=thermal.step(.05,segments,(dryer[:3]+r@np.array((.088,0,0))).tolist(),r[:,0].tolist(),power)
    worst_sep=max(worst_sep,sep);max_motion=max(max_motion,float(np.linalg.norm(np.array(segments[88]['pos'])-np.array(segment(8,8)))))
    row={'time':env._t,'phase':phase,'hair':segments,'dryer_pose':dryer.tolist(),'switch_pose':switch.tolist(),'power_slider_fraction':power,'crease_separation':sep,'thermal':m};trace.write(json.dumps(row)+'\n');samples.append(row)
    if not np.isfinite(dryer).all() or sep>.03:raise RuntimeError('unstable native hair dynamics')
    panels=[cv2.resize(arr(base.scene[n].data.output['rgb'])[0,:,:,:3].astype(np.uint8),(480,270)) for n in ['top_cam','left_cam','right_cam']];canvas=np.zeros((594,960,3),dtype=np.uint8);canvas[36:306,240:720]=panels[0];canvas[306:576,:480]=panels[1];canvas[306:576,480:]=panels[2]
    cv2.putText(canvas,'NATIVE FLEXIBLE HAIR | '+phase,(12,25),cv2.FONT_HERSHEY_SIMPLEX,.6,(255,255,255),1,cv2.LINE_AA);cv2.putText(canvas,'Diagnostic force test, not robot drying. Actual moisture/geometry measured.',(12,590),cv2.FONT_HERSHEY_SIMPLEX,.45,(255,205,120),1,cv2.LINE_AA);video.append_data(canvas)
    if step in (59,99,179):imageio.imwrite(a.out/f'step-{step}.png',canvas)
  result={'diagnostic':True,'task_score':None,'robot_demo':False,'max_joint_separation_m':worst_sep,'max_lock_motion_m':max_motion,'thermal':thermal.result(),'checks':{'joints_intact':worst_sep<.005,'locks_move':max_motion>.005,'power_off_no_drying':all(s['thermal']['water_removed_step_kg']==0 for s in samples if s['power_slider_fraction']<.5)}}
  (a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 except BaseException as error:
  import traceback;traceback.print_exc();(a.out/'error.json').write_text(json.dumps({'error':str(error),'type':type(error).__name__},indent=2));raise
 finally:
  if video is not None:video.close()
  app.close()
if __name__=='__main__':main()
