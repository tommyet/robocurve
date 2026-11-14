"""Native latch/cable mechanics probe. External test forces are NOT a robot demo."""
import argparse,os,json,hashlib,time,shutil
from pathlib import Path
from config import *

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=['retention-probe','grasp-probe','release-probe'],default='retention-probe');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False)
 (a.out/'source').mkdir()
 for f in [*Path(__file__).parent.glob('*.py'),Path(__file__).with_name('press_point.json')]:shutil.copy2(f,a.out/'source'/f.name)
 (a.out/'source-sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [*Path(__file__).parent.glob('*.py'),*Path(__file__).parent.glob('*point.json')]},indent=2))
 os.environ.setdefault('OMNI_KIT_ACCEPT_EULA','YES')
 from isaaclab.app import AppLauncher
 app=AppLauncher(headless=True,enable_cameras=True).app
 video=None
 try:
  import numpy as np,torch,cv2,imageio.v2 as imageio
  from yam_arena import inspect_embodiment as wrapper
  from yam_arena import scene as sc
  from yam_arena.urdf import quat_xyzw_to_matrix
  import isaaclab.sim as sim
  from native import export,install_joints
  import task
  wrapper._APP=app
  assets={s.name:export(a.out/(s.name+'.usda'),s.name) for s in task.OBJECTS if s.name!='mat'}
  original=sc.task_object
  def make(spec):
   if spec.name not in assets:return original(spec)
   cfg=sim.UsdFileCfg(usd_path=assets[spec.name])
   if spec.name==f'wire_{USED[-1]}_{LINKS-1}':
    spawn=cfg.func
    def with_joints(path,cfg,translation=None,orientation=None,**kwargs):
     prim=spawn(path,cfg,translation=translation,orientation=orientation,**kwargs)
     install_joints(prim.GetStage(),str(prim.GetPath()).rsplit('/',1)[0]);return prim
    cfg.func=with_joints
   return sc.Object(name=spec.name,object_type=sc.ObjectType.BASE if spec.name=='switch' else sc.ObjectType.RIGID,spawner_cfg=cfg,initial_pose=sc.Pose(position_xyz=spec.pos,rotation_xyzw=(0,0,0,1)))
  from yam_arena.embodiment import BimanualYamEmbodiment
  import review
  original_init=BimanualYamEmbodiment.__init__
  def with_reviews(instance,*args,**kwargs):
   kwargs['cam_width']=320;kwargs['cam_height']=180;original_init(instance,*args,**kwargs);review.add_cameras(instance)
  BimanualYamEmbodiment.__init__=with_reviews
  sc.task_object=make
  try:
   env=wrapper.YamArenaEmbodiment(task=str(Path(__file__).with_name('task.py')),object_jitter=0.,control_hz=20,headless=True,cam_width=320,cam_height=180)
   env._ensure_sim(None)
  finally:sc.task_object=original;BimanualYamEmbodiment.__init__=original_init
  base=env._base;env._env.reset();env._instruction='Native retention force probe; no task score';env._t=0.
  review.place(base,(.41,0.,.96))
  def arr(v):
   v=v.torch if hasattr(v,'torch') else v
   return v.detach().cpu().numpy()
  def pose(name):return arr(base.arena_world.get_pose_w(name))[0]
  def force(name,f):
   base.scene[name].permanent_wrench_composer.set_forces_and_torques_index(forces=torch.tensor([[f]],device=base.device,dtype=torch.float32),torques=torch.zeros((1,1,3),device=base.device),is_global=True)
  video=imageio.get_writer(str(a.out/'diagnostic.mp4'),fps=20,codec='libx264',pixelformat='yuv420p',macro_block_size=1,ffmpeg_params=['-movflags','+faststart'])
  samples=[]
  robot=None
  if a.mode in ('grasp-probe','release-probe'):
   from robot import GraspProbe,ReleaseProbe,MAX_RELEASE_STEPS
   robot=(ReleaseProbe if a.mode=='release-probe' else GraspProbe)(env,pose(f'plug_{SERVICE}')[:3])
  scorer=None;previous_plug=None
  if a.mode=='release-probe':
   from scoring import EthernetScorer
   scorer=EthernetScorer();task._tracker=scorer;task._diagnostic=False
  with (a.out/'trajectory.jsonl').open('w') as trace:
   for step in range(MAX_RELEASE_STEPS if a.mode=='release-probe' else 600 if robot else 180):
    phase='settle' if step<40 else 'pull_engaged' if step<60 else 'press_clip' if step<80 else 'pull_pressed' if step<120 else 'release'
    pull=-1.0 if phase in ('pull_engaged','pull_pressed') else 0.
    if phase=='pull_pressed' and pose(f'plug_{SERVICE}')[0]<PLUG_X-.035:pull=0.
    press=-.70 if phase in ('press_clip','pull_pressed') else 0.
    control=None
    if robot:
     target,control=robot.command(step*.05);phase=control['phase'];pull=press=0.
     action=torch.tensor(target[None,:],device=base.device,dtype=torch.float32)
    else:
     force(f'plug_{SERVICE}',(pull,0,0));force(f'clip_{SERVICE}',(0,0,press));action=env._ready
    env._env.step(action);env._t=(step+1)*.05
    p0=pose(f'plug_{SERVICE}');c=pose(f'clip_{SERVICE}')
    row={'time':env._t,'phase':phase,'robot_control':control,'plug_pose':p0.tolist(),'clip_pose':c.tolist(),'pull_N':pull,'press_N':press,'neighbours':{str(i):pose(f'plug_{i}').tolist() for i in USED if i!=SERVICE}}
    if scorer is not None:
     rp=quat_xyzw_to_matrix(p0[3:]);local_clip=rp.T@(c[:3]-p0[:3]);travel=float(CLIP_Z-local_clip[2]);tip=p0[:3]+rp@np.array((.012,0,0))
     def insertion(i):
      center=np.array(port(i));lateral=np.linalg.norm(p0[1:3]-center[1:3]);return float(tip[0]-(.412-.027/2)) if lateral<.007 and rp[0,0]>.8 else -.020
     target=np.array(port(TARGET));hook=p0[:3]+rp@np.array((.006,0,CLIP_Z+.0025-travel));hand_positions=[]
     from yam_arena import ik
     for side in ('left','right'):
      ids,_=env._ids[side+'_robot'];d=arr(base.scene[side+'_robot'].data.joint_pos)[0,ids];hand_positions.append(ik.tcp_pose(d,env.rig.bases[side])[0])
     sample={'time':env._t,'clip_travel':travel,'source_insertion':insertion(SERVICE),'target_insertion':insertion(TARGET),'target_lateral_error':float(np.linalg.norm(p0[1:3]-target[1:3])),'target_angle':float(np.arccos(np.clip(rp[0,0],-1,1))),'speed':0. if previous_plug is None else float(np.linalg.norm(p0[:3]-previous_plug)/.05),'height':float(p0[2]),'max_neighbour_withdrawal':max(max(0.,PLUG_X-v[0]) for v in row['neighbours'].values()),'hands_clear':all(np.linalg.norm(h-p0[:3])>.070 for h in hand_positions),'hook_retained':bool(.409-.0002<hook[0]<.423 and abs(hook[1]-target[1])<.003 and target[2]+.005<hook[2]<target[2]+.0075)}
     previous_plug=p0[:3].copy();row['score_sample']=sample;row['metrics']=scorer.update(sample)
    if not np.isfinite([*p0,*c]).all():raise RuntimeError('nonfinite rigid body state')
    trace.write(json.dumps(row)+'\n');samples.append(row)
    panels=review.panels(base)
    canvas=np.zeros((594,960,3),dtype=np.uint8);canvas[36:306,240:720]=panels[0];canvas[306:576,:480]=panels[1];canvas[306:576,480:]=panels[2]
    cv2.putText(canvas,(('ETHERNET ROBOT RELEASE ATTEMPT | ' if scorer else 'ETHERNET ROBOT GRASP PROBE | ') if robot else 'ETHERNET NATIVE FORCE PROBE | ')+phase,(12,25),cv2.FONT_HERSHEY_SIMPLEX,.60,(255,255,255),1,cv2.LINE_AA)
    cv2.putText(canvas,(('Ordinary robot commands. Measured score: '+str(scorer.value) if scorer else 'Ordinary robot commands, grasp diagnostic only. Task score: unscored') if robot else 'External test forces, not a robot demonstration. Task score: unscored'),(12,590),cv2.FONT_HERSHEY_SIMPLEX,.46,(255,205,120),1,cv2.LINE_AA);video.append_data(canvas)
    if step in (39,59,79,119,179,259,299,359,459,539,619,719,819):imageio.imwrite(a.out/f'step-{step}.png',canvas)
    if control is not None and (control.get('failure') or control.get('complete')):break
  # Report actual measured behaviour, never infer passing from a scripted phase.
  x0=samples[39]['plug_pose'][0];xe=samples[59]['plug_pose'][0];xr=min(r['plug_pose'][0] for r in samples[80:120])
  cliptravel=max(CLIP_Z-(quat_xyzw_to_matrix(np.array(r['plug_pose'][3:])).T@(np.array(r['clip_pose'][:3])-np.array(r['plug_pose'][:3])))[2] for r in samples[60:120])
  tips=[r['plug_pose'][0]+float((quat_xyzw_to_matrix(np.array(r['plug_pose'][3:]))@np.array((.012,0,0)))[0]) for r in samples[40:60]]
  settled_span=float(np.ptp([r['plug_pose'][0] for r in samples[50:60]]))
  result={'diagnostic':True,'task_score':None,'robot_demo':False,'engaged_pull_displacement_m':x0-xe,'pressed_withdrawal_m':x0-xr,'max_clip_travel_m':cliptravel,'engaged_tip_min_x_m':min(tips),'engaged_end_x_span_m':settled_span,'checks':{'retains_engaged':min(tips)>(.412-.027/2)+.005 and settled_span<.0015,'releases_pressed':x0-xr>.020,'clip_depresses':cliptravel>RELEASE_TRAVEL}}
  if robot:result={'diagnostic':True,'task_score':None,'robot_demo':False,'robot_grasp_probe':True,'max_tracking_error_m':max(r['robot_control']['position_error'] for r in samples),'final_plug_pose':samples[-1]['plug_pose'],'controller_failure':samples[-1]['robot_control'].get('failure'),'controller_complete':samples[-1]['robot_control'].get('complete',False)}
  if scorer is not None:result|={'diagnostic':False,'privileged_robot_attempt':True,'task_score':scorer.value,'metrics':samples[-1]['metrics']}
  (a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
 except BaseException as error:
  import traceback
  traceback.print_exc()
  (a.out/'error.json').write_text(json.dumps({'error':str(error),'type':type(error).__name__},indent=2))
  raise
 finally:
  if video is not None:video.close()
  app.close()
if __name__=='__main__':main()
