"""Native free-carton crease/stability probe. No robot completion is claimed."""
import argparse,os,json,shutil,hashlib
from pathlib import Path
from config import *
from scene import layout
from model import WIDTH,HEIGHT
from crease import physical_bottom_angle,joint_parameters

def main():
 p=argparse.ArgumentParser(description='SYNTHETIC POSTCUT OPENING COUPON; unsealed restored state, scorer0/mediafalse')
 p.add_argument('--out',type=Path,required=True);p.add_argument('--snapshot',type=Path,required=True)
 p.add_argument('--route',type=Path);p.add_argument('--active-hand',choices=['left','right']);p.add_argument('--seconds',type=int,choices=range(5,241),default=5);a=p.parse_args()
 from coupon_support import load_snapshot
 from open_coupon import load_route,CONTROLLERS
 snapshot=load_snapshot(a.snapshot);route=load_route(a.route,a.snapshot)
 if route and route['controller'] not in CONTROLLERS:p.error('no reviewed opening controller registered')
 active_hand=route['active_hand'] if route else (a.active_hand or 'left')
 if route and a.active_hand and a.active_hand!=active_hand:p.error('active hand disagrees with reviewed route')
 a.mode='restored-open';a.unsealed=True;a.no_video=True
 a.out=a.out.resolve();a.out.mkdir(parents=True,exist_ok=False);(a.out/'source').mkdir()
 for f in Path(__file__).parent.glob('*.py'):shutil.copy2(f,a.out/'source'/f.name)
 (a.out/'source-sha256.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in Path(__file__).parent.glob('*.py')},indent=2))
 os.environ.setdefault('OMNI_KIT_ACCEPT_EULA','YES')
 from isaaclab.app import AppLauncher
 app=AppLauncher(headless=True,enable_cameras=not a.no_video).app;video=None
 try:
  import numpy as np,torch
  if not a.no_video:import cv2,imageio.v2 as imageio
  from yam_arena import inspect_embodiment as wrapper
  from yam_arena import scene as sc
  from yam_arena.urdf import quat_xyzw_to_matrix
  import isaaclab.sim as sim
  from native import export,install_joints
  from yam_arena import ik
  from yam_arena.constants import FINGER_OPEN
  import task
  wrapper._APP=app;parts,hs=layout();byname={s['name']:s for s in parts};assets={s.name:export(a.out/(s.name+'.usda'),s.name) for s in task.OBJECTS if s.name!='cutter_pad'};original=sc.task_object
  def make(spec):
   if spec.name not in assets:return original(spec)
   cfg=sim.UsdFileCfg(usd_path=assets[spec.name],activate_contact_sensors=spec.name=='cutter');pos,q=starting_pose(byname[spec.name],upright=a.mode=='grip-probe') if spec.name in byname else (spec.pos,(1,0,0,0))
   if spec.name=='cutter':
    spawn=cfg.func
    def with_joints(path,cfg,translation=None,orientation=None,**kwargs):
     prim=spawn(path,cfg,translation=translation,orientation=orientation,**kwargs);install_joints(prim.GetStage(),str(prim.GetPath()).rsplit('/',1)[0],sealed=not a.unsealed);return prim
    cfg.func=with_joints
   return sc.Object(name=spec.name,object_type=sc.ObjectType.RIGID,spawner_cfg=cfg,initial_pose=sc.Pose(position_xyz=pos,rotation_xyzw=(*q[1:],q[0])))
  from yam_arena.embodiment import BimanualYamEmbodiment
  import review
  import capture
  original_init=BimanualYamEmbodiment.__init__
  def with_reviews(instance,*args,**kwargs):
   kwargs['contact_sensors']=False
   capture.configure_embodiment(instance,args,kwargs,original_init,review,no_video=True)
   from isaaclab.sensors import ContactSensorCfg
   from isaaclab_arena.utils.configclass import make_configclass
   from yam_arena.robot import asset_link_paths
   from open_coupon import contact_sensor_specs
   cfg=instance.scene_config
   fields=[(n,type(getattr(cfg,n)),getattr(cfg,n)) for n in cfg.__class__.__annotations__]
   for name,spec in contact_sensor_specs(active_hand,asset_link_paths(),[part['name']for part in parts]).items():
    fields.append(('open_contact_'+name,ContactSensorCfg,ContactSensorCfg(**spec,history_length=0,track_contact_points=True,track_friction_forces=True,max_contact_data_count_per_prim=64)))
   instance.scene_config=make_configclass('OpeningCouponContactSceneCfg',fields)()
  BimanualYamEmbodiment.__init__=with_reviews
  sc.task_object=make
  try:
   env=wrapper.YamArenaEmbodiment(task=str(Path(__file__).with_name('task.py')),object_jitter=0.,control_hz=20,headless=True,cam_width=320,cam_height=180);env._ensure_sim(None)
  finally:sc.task_object=original;BimanualYamEmbodiment.__init__=original_init
  base=env._base
  capture.suppress_state_only_rendering(base,no_video=a.no_video)
  env._env.reset();env._instruction='Synthetic restored POSTCUT opening engineering coupon; scorer0, not fresh task';env._t=0.
  from coupon_support import restore_once
  restoration=restore_once(env,snapshot,lambda x:torch.tensor(x,device=base.device,dtype=torch.float32))
  from native_angle_binding import install as install_angle_observer
  angle_observer=install_angle_observer(base)
  (a.out/'angle-tracking-reset.json').write_text(json.dumps(dict(initial_state=angle_observer.initial_state,caps_deg_s=angle_observer.tracker.caps,authored_zero=False,scope='UNSCORED_RESTORED_DIAGNOSTIC_ONLY'),indent=2)+'\n')
  (a.out/'restore-readback.json').write_text(json.dumps(restoration,indent=2)+'\n')
  shutil.copy2(a.snapshot,a.out/'restore-snapshot.json');shutil.copy2(a.snapshot.with_name(snapshot['source_row_file']),a.out/snapshot['source_row_file'])
  if a.route:shutil.copy2(a.route,a.out/'reviewed-route.json')
  if not a.no_video:review.place(base,(.32,0.,.82))
  from yam_arena.robot import asset_link_paths
  owners=capture.native_body_owners(base.scene,asset_link_paths(),[part['name'] for part in parts])
  for path in owners:
   if not base.scene.stage.GetPrimAtPath(path):raise RuntimeError('missing native capture owner '+path)
  view_cfg=sim.PinholeCameraCfg(focal_length=18.,clipping_range=(.03,20.)) if a.no_video else base.scene[review.NAMES[0]].cfg.spawn
  manifest=capture.capture_manifest(capture.export_scene(base.scene.stage,a.out/'capture-scene.usdc'),owners,
      json.loads((a.out/'source-sha256.json').read_text()),capture.virtual_review_views(view_cfg),no_video=a.no_video)
  manifest.update(synthetic_restored_start=True,scorer_enabled=False,media_eligible=False,restoration=restoration,
      joint_limits_unsealed=True,native_physics_dt_s=float(base.cfg.sim.dt),active_hand=active_hand,
      restore_snapshot_sha256=hashlib.sha256(a.snapshot.read_bytes()).hexdigest(),source_trace_sha256=snapshot['source_trace_sha256'],
      source_row_sha256=snapshot['source_row_sha256'],route_sha256=hashlib.sha256(a.route.read_bytes()).hexdigest() if a.route else None)
  (a.out/'capture-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
  (a.out/'mode.json').write_text(json.dumps(dict(mode='synthetic-postcut-opening-coupon',synthetic_restored_start=True,scorer_enabled=False,task_score=0.,media_eligible=False,state_only=True,maximum_seconds=a.seconds,active_hand=active_hand,unsealed_start=True,source_time_s=snapshot['source_time_s']),indent=2)+'\n')
  def arr(v):
   v=v.torch if hasattr(v,'torch') else v
   return v.detach().cpu().numpy()
  def pose(name):return arr(base.arena_world.get_pose_w(name))[0]
  if not a.no_video:video=imageio.get_writer(str(a.out/'diagnostic.mp4'),fps=20,codec='libx264',pixelformat='yuv420p',macro_block_size=1,ffmpeg_params=['-movflags','+faststart'])
  from open_coupon import OpeningCoupon
  from native_contact_reader import read_sensor_native_contacts,ContactReadError
  robot=OpeningCoupon(env,snapshot,route);task._diagnostic=True;task._tracker=None
  worst=0.;minz=10.;bestflat=10.
  with (a.out/'trajectory.jsonl').open('w')as trace:
   for step in range(a.seconds*20):
    target,control=robot.command(step*.05)
    if robot.failure:
     (a.out/'prestep-rejection.json').write_text(json.dumps(dict(time_s=step*.05,failure=robot.failure,control=control),indent=2)+'\n')
     break
    action=torch.tensor(target[None,:],device=base.device,dtype=torch.float32)
    angle_observer.begin_control()
    env._env.step(action);env._t=(step+1)*.05
    if len(base._reset_env_ids):angle_observer.tracker.invalidate('native episode reset')
    angle_evidence=angle_observer.end_control()
    if not angle_evidence['valid']:raise RuntimeError(angle_evidence['failure'])
    pp={part['name']:pose(part['name'])for part in parts};rr={n:quat_xyzw_to_matrix(v[3:])for n,v in pp.items()};sep=0.;angles={}
    for h in hs:
     pa=pp[h['a']][:3]+rr[h['a']]@np.array(h['anchor_a']);pb=pp[h['b']][:3]+rr[h['b']]@np.array(h['anchor_b']);sep=max(sep,float(np.linalg.norm(pa-pb)))
     rel=rr[h['a']].T@rr[h['b']];raw=float(np.degrees(np.arctan2(rel[2,1],rel[1,1])if h['axis']=='X'else np.arctan2(rel[1,0],rel[0,0])));angles[h['name']]=float(angle_observer.tracker.angles[['north','south','east','west'].index(h['a'])])if h['b'].endswith('_bottom')else raw
    vertices=np.array([pp[part['name']][:3]+rr[part['name']]@(.5*np.array(part['size'])*np.array((x,y,z)))for part in parts for x in (-1,1)for y in (-1,1)for z in (-1,1)])
    low=float(vertices[:,2].min()-TOP);high=float(vertices[:,2].max()-TOP);worst=max(worst,sep);minz=min(minz,low);bestflat=min(bestflat,high-low)
    velocities={name:arr(base.scene[name].data.root_com_vel_w)[0].tolist()for name in [*pp,'cutter']}
    hands=[]
    for side in ('left','right'):
     ids,fids=env._ids[side+'_robot'];q=arr(base.scene[side+'_robot'].data.joint_pos)[0];tcp,R=ik.tcp_pose(q[ids],env.rig.bases[side]);hands.append(dict(side=side,joints=q[ids].tolist(),finger_joints=q[fids].tolist(),tcp=tcp.tolist(),tcp_rotation=R.tolist(),opening=float(np.clip(q[fids].mean()/FINGER_OPEN,0,1))))
    row=dict(time=env._t,phase=control[0]['phase'],robot_control=control,action_14d=arr(action)[0].tolist(),native_hands=hands,cutter_pose=pose('cutter').tolist(),poses={n:v.tolist()for n,v in pp.items()},angles_deg=angles,max_crease_separation_m=sep,lowest_vertex_m=low,highest_vertex_m=high,native_object_com_velocities_w=velocities,synthetic_restored_start=True,scorer_enabled=False)
    row['angle_evidence']=angle_evidence
    row['angle_substeps']=angle_observer.samples
    row['native_owner_poses']=capture.native_body_world_poses(base.scene,owners,{**pp,'cutter':row['cutter_pose']})
    row['native_hand_panel_contacts']={}
    for name in ('gripper','tip_left','tip_right'):
     try:row['native_hand_panel_contacts'][name]=read_sensor_native_contacts(base.scene['open_contact_'+name],physics_dt=float(base.cfg.sim.dt))
     except ContactReadError as error:row['native_hand_panel_contacts'][name]=error.as_dict();robot.failure='native hand-panel contact snapshot invalid: '+str(error)
    mismatch=angular=0.
    if step==0:
     mismatch=max(float(np.linalg.norm(pp[n][:3]-np.array(snapshot['poses'][n][:3])))for n in pp)
     angular=max(float(np.linalg.norm(ik._rot_error(rr[n],quat_xyzw_to_matrix(snapshot['poses'][n][3:]))))for n in pp)
     row.update(first_step_panel_pose_displacement_m=mismatch,first_step_panel_orientation_displacement_rad=angular)
    robot.observe(time=env._t,crease_separation=sep,velocities=velocities,first_step_translation=mismatch,first_step_rotation=angular)
    row['poststep_failure']=robot.failure
    trace.write(json.dumps(row,allow_nan=False)+'\n')
    if not np.isfinite(vertices).all() or low<-.03:robot.failure='native restored carton unstable/below table'
    if robot.failure or robot.done:break
  (a.out/'coupon-events.json').write_text(json.dumps(robot.events,indent=2)+'\n')
  result=dict(synthetic_restored_start=True,unsealed_start=True,scorer_enabled=False,task_score=0.,media_eligible=False,state_only=True,diagnostic=True,controller_failure=robot.failure,safe_start_passed=robot.safe_start_passed,route_completed=robot.done,max_crease_separation_m=worst,lowest_vertex_m=minz,smallest_height_span_m=bestflat)
  (a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 except BaseException as error:
  import traceback;traceback.print_exc();(a.out/'error.json').write_text(json.dumps(dict(error=str(error),type=type(error).__name__)));raise
 finally:
  app.close()
if __name__=='__main__':main()
