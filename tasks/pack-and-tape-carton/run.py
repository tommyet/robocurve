"""Native wound-ribbon bench probe; fixture/drive diagnostic, never robot credit."""
import argparse,os,json,shutil,hashlib,math
from pathlib import Path
from config import *
from carton_scene import layout

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False);(a.out/'source').mkdir()
 for f in Path(__file__).parent.glob('*.py'):shutil.copy2(f,a.out/'source'/f.name)
 (a.out/'source-sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in Path(__file__).parent.glob('*.py')},indent=2));os.environ.setdefault('OMNI_KIT_ACCEPT_EULA','YES')
 from isaaclab.app import AppLauncher
 app=AppLauncher(headless=True,enable_cameras=True).app;video=None
 try:
  import numpy as np,torch,cv2,imageio.v2 as imageio
  from yam_arena import inspect_embodiment as wrapper
  from yam_arena import scene as sc
  from yam_arena.urdf import quat_xyzw_to_matrix
  from pxr import UsdPhysics,Gf
  import isaaclab.sim as sim
  from carton_native import export as cexport
  from tape_native import export as texport,install_joints
  import task
  wrapper._APP=app;parts,hs=layout();byname={p['name']:p for p in parts};assets={}
  for spec in task.OBJECTS:
   if spec.name in byname or spec.name=='cutter':assets[spec.name]=cexport(a.out/(spec.name+'.usda'),spec.name)
   elif spec.name=='roll' or spec.name.startswith('tape_'):assets[spec.name]=texport(a.out/(spec.name+'.usda'),spec.name)
  original=sc.task_object;original_dt=sc.PHYSICS_DT;sc.PHYSICS_DT=.0005
  def make(spec):
   if spec.name not in assets:return original(spec)
   q=byname[spec.name]['quat'] if spec.name in byname else (math.cos(spec.yaw/2),0,0,math.sin(spec.yaw/2))
   cfg=sim.UsdFileCfg(usd_path=assets[spec.name])
   if spec.name=='cutter':
    spawn=cfg.func
    def with_joints(path,cfg,translation=None,orientation=None,**kwargs):
     prim=spawn(path,cfg,translation=translation,orientation=orientation,**kwargs);s=prim.GetStage();parent=str(prim.GetPath()).rsplit('/',1)[0];install_joints(s,parent)
     # Explicit test-bench fixtures only. Not present in a real task episode.
     j=UsdPhysics.FixedJoint.Define(s,parent+'/roll/bench_fixture');j.CreateBody1Rel().SetTargets([parent+'/roll']);j.CreateLocalPos0Attr(Gf.Vec3f(*ROLL_START));j.CreateLocalPos1Attr(Gf.Vec3f(0,0,0));j.CreateExcludeFromArticulationAttr(True)
     point,yaw=tape_cell(CELLS-1);j=UsdPhysics.PrismaticJoint.Define(s,parent+f'/tape_{CELLS-1}/bench_peel');j.CreateBody1Rel().SetTargets([parent+f'/tape_{CELLS-1}']);j.CreateAxisAttr('X');j.CreateLocalPos0Attr(Gf.Vec3f(*point));j.CreateLocalPos1Attr(Gf.Vec3f(0,0,0));j.CreateLocalRot1Attr(Gf.Quatf(math.cos(yaw/2),Gf.Vec3f(0,0,-math.sin(yaw/2))));j.CreateLowerLimitAttr(0.);j.CreateUpperLimitAttr(.07);j.CreateExcludeFromArticulationAttr(True)
     d=UsdPhysics.DriveAPI.Apply(j.GetPrim(),'linear');d.CreateTypeAttr('force');d.CreateStiffnessAttr(30.);d.CreateDampingAttr(.1);d.CreateMaxForceAttr(3.);d.CreateTargetPositionAttr(0.)
     return prim
    cfg.func=with_joints
   return sc.Object(name=spec.name,object_type=sc.ObjectType.RIGID,spawner_cfg=cfg,initial_pose=sc.Pose(position_xyz=spec.pos,rotation_xyzw=(*q[1:],q[0])))
  sc.task_object=make
  try:
   env=wrapper.YamArenaEmbodiment(task=str(Path(__file__).with_name('task.py')),object_jitter=0.,control_hz=20,headless=True,cam_width=320,cam_height=180);env._ensure_sim(None)
  finally:sc.task_object=original;sc.PHYSICS_DT=original_dt
  base=env._base;env._env.reset();env._instruction='Finite wound-ribbon material probe';env._t=0.
  for n,eye in zip(['top_cam','left_cam','right_cam'],[(.0,-.32,1.18),(.03,.20,1.04),(.04,-.24,1.02)]):base.scene[n].set_world_poses_from_view(torch.tensor([eye],device=base.device),torch.tensor([[.20,-.08,.81]],device=base.device))
  drive=UsdPhysics.DriveAPI(base.scene.stage.GetPrimAtPath(f'/World/envs/env_0/tape_{CELLS-1}/bench_peel'),'linear')
  def arr(v):
   v=v.torch if hasattr(v,'torch') else v
   return v.detach().cpu().numpy()
  def pose(name):return arr(base.arena_world.get_pose_w(name))[0]
  # Keep exact native break payloads for interpretation; never infer from phase.
  events=[];subscription=None
  try:
   import omni.physx
   stream=omni.physx.get_physx_interface().get_simulation_event_stream_v2()
   def event(e):events.append({'time':env._t,'type':int(e.type),'payload':str(e.payload)})
   subscription=stream.create_subscription_to_pop(event)
  except Exception as error:events.append({'subscription_error':str(error)})
  video=imageio.get_writer(str(a.out/'diagnostic.mp4'),fps=20,codec='libx264',pixelformat='yuv420p',macro_block_size=1,ffmpeg_params=['-movflags','+faststart']);worst=0.;max_unwound=0.;allposes=[];initial_displacement=0.
  with (a.out/'trajectory.jsonl').open('w') as trace:
   for step in range(100):
    phase='settle' if step<20 else 'peel_bench' if step<60 else 'hold'
    target=.06*min(1.,max(0.,(step-20)/40))
    drive.GetTargetPositionAttr().Set(target)
    env._env.step(env._ready);env._t=(step+1)*.05
    roll=pose('roll');rr=quat_xyzw_to_matrix(roll[3:]);states=[pose(f'tape_{i}') for i in range(CELLS)];local=[rr.T@(v[:3]-roll[:3]) for v in states];displaced=[];sep=0.
    for i,v in enumerate(local):
     pos,_=tape_cell(i);displaced.append(float(np.linalg.norm(v-(np.array(pos)-np.array(ROLL_START)))))
     if i:
      # Recompute the actual authored anchors in each measured film frame.
      p0,y0=tape_cell(i-1);p1,y1=tape_cell(i);anchor=(np.array(p0)+p1)/2
      def localpoint(origin,yaw):
       r=np.array([[np.cos(yaw),-np.sin(yaw),0],[np.sin(yaw),np.cos(yaw),0],[0,0,1]])
       return r.T@(anchor-np.array(origin))
      a0=states[i-1][:3]+quat_xyzw_to_matrix(states[i-1][3:])@localpoint(p0,y0);a1=states[i][:3]+quat_xyzw_to_matrix(states[i][3:])@localpoint(p1,y1);sep=max(sep,float(np.linalg.norm(a0-a1)))
    if step<20:initial_displacement=max(initial_displacement,max(displaced))
    if step==19 and initial_displacement>.0005:raise RuntimeError('tape shifted before peel loading; initial wrap invalid')
    worst=max(worst,sep);unwound=sum(d>.003 for d in displaced)*CELL_LENGTH;max_unwound=max(max_unwound,unwound)
    row={'time':env._t,'phase':phase,'bench_target_m':target,'roll_pose':roll.tolist(),'film_poses':[s.tolist() for s in states],'native_cell_displacement_m':displaced,'material_anchor_separation_m':sep,'unwound_length_estimate_m':unwound};trace.write(json.dumps(row)+'\n')
    if not np.isfinite(states).all() or sep>.02:raise RuntimeError('unstable ribbon or disconnected material')
    panels=[cv2.resize(arr(base.scene[n].data.output['rgb'])[0,:,:,:3].astype(np.uint8),(480,270)) for n in ['top_cam','left_cam','right_cam']];canvas=np.zeros((594,960,3),dtype=np.uint8);canvas[36:306,240:720]=panels[0];canvas[306:576,:480]=panels[1];canvas[306:576,480:]=panels[2]
    cv2.putText(canvas,'NATIVE WOUND TAPE | '+phase,(12,25),cv2.FONT_HERSHEY_SIMPLEX,.6,(255,255,255),1,cv2.LINE_AA);cv2.putText(canvas,'Clamped material bench, not robot packing. No tape pose animation.',(12,590),cv2.FONT_HERSHEY_SIMPLEX,.46,(255,205,120),1,cv2.LINE_AA);video.append_data(canvas)
    if step in (19,59,99):imageio.imwrite(a.out/f'step-{step}.png',canvas)
  result={'diagnostic':True,'robot_demo':False,'task_score':None,'bench_fixtures':True,'physics_dt_s':float(base.sim.get_physics_dt()),'explicit_material_length_m':ACTIVE_LENGTH,'initial_wrap_displacement_m':initial_displacement,'max_anchor_separation_m':worst,'max_displaced_material_estimate_m':max_unwound,'checks':{'stays_wound_before_pull':initial_displacement<.0005,'material_connected':worst<CELL_LENGTH*MAX_STRAIN,'material_peels':max_unwound>.025}}
  (a.out/'native-events.json').write_text(json.dumps(events,indent=2)+'\n');(a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 except BaseException as error:
  import traceback;traceback.print_exc();(a.out/'error.json').write_text(json.dumps({'error':str(error),'type':type(error).__name__},indent=2));raise
 finally:
  if video is not None:video.close()
  app.close()
if __name__=='__main__':main()
