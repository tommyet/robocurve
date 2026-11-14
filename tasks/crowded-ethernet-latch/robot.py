"""Bounded ordinary YAM commands; no object-state writes or external forces."""
import numpy as np
from yam_arena import ik
from yam_arena.constants import FINGER_OPEN
from yam_arena.urdf import axis_angle_matrix
_angle=np.radians(80.)
R_GRIP=np.array([[0.,np.cos(_angle),np.sin(_angle)],[0.,-np.sin(_angle),np.cos(_angle)],[1.,0.,0.]])
class GraspProbe:
 def __init__(self,env,plug):
  self.env=env;self.base=env._base;self.start_time=None;self.q=None;self.p0=None;self.r0=None;self.bias=np.zeros(3);self.previous=env._ready.detach().cpu().numpy().reshape(-1).copy();self.plug=plug
 def command(self,time):
  env=self.env;ids,fids=env._ids['right_robot'];qdata=self.base.scene['right_robot'].data.joint_pos
  qdata=qdata.torch if hasattr(qdata,'torch') else qdata;qa=qdata.detach().cpu().numpy()[0,ids]
  tcp,rot=ik.tcp_pose(qa,env.rig.bases['right'])
  if self.start_time is None:
   self.start_time=time;self.q=qa.copy();self.p0=tcp.copy();self.r0=rot.copy()
   self.goal=self.plug+np.array((-.0205,.0005,0.));self.r=R_GRIP
  elapsed=time-self.start_time
  if elapsed<3.:
   phase='approach_boot';s=ik.smoothstep(elapsed/3.);p=self.p0+s*(self.goal+(-.060,-.035,.025)-self.p0);r=ik.slerp_matrix(self.r0,self.r,s);g=1.
  elif elapsed<6.:
   phase='enter_boot';s=ik.smoothstep((elapsed-3.)/3.);p=self.goal+(1-s)*np.array((-.060,-.035,.025));r=self.r;g=1.
  elif elapsed<8.:
   phase='close_on_boot';p=self.goal;r=self.r;g=1.-ik.smoothstep((elapsed-6.)/2.)*(1.-.0015/abs(FINGER_OPEN))
  elif getattr(self,'release',False):
   phase,p,r,g=self.released_goal(elapsed)
  elif elapsed<10.:
   phase='hold_boot';p=self.goal;r=self.r;g=.0015/abs(FINGER_OPEN)
  elif elapsed<13.:
   phase='small_engaged_pull';p=self.goal+np.array((-.010*ik.smoothstep((elapsed-10.)/3.),0,0));r=self.r;g=.0015/abs(FINGER_OPEN)
  elif elapsed<15.:
   phase='return_boot';p=self.goal+np.array((-.010*(1-ik.smoothstep((elapsed-13.)/2.)),0,0));r=self.r;g=.0015/abs(FINGER_OPEN)
  else:
   phase='release_boot';p=self.goal;r=self.r;g=min(1.,.0015/abs(FINGER_OPEN)+(elapsed-15.)/2.)
  self.bias=np.clip(self.bias+.08*(p-tcp),-.020,.020)
  self.q,pe,re=ik.solve(p+self.bias,ik.matrix_to_quat_xyzw(r),self.q,base_pos=env.rig.bases['right'],iters=90)
  target=env._ready.detach().cpu().numpy().reshape(-1).copy();target[7:13]=self.q;target[13]=g
  delta=np.array([.04]*6+[.05]+[.04]*6+[.05]);target=np.clip(target,self.previous-delta,self.previous+delta);target=np.clip(target,env._low,env._high);self.previous=target
  return target,{'phase':phase,'right_tcp':tcp.tolist(),'right_target':p.tolist(),'position_error':float(np.linalg.norm(p-tcp)),'ik_position_error':pe,'ik_rotation_error':re,'grip_target':g,'actual_joints':qa.tolist()}

class ReleaseProbe(GraspProbe):
 """Actual two-arm release/reinsert attempt, privileged measured-state demo."""
 def __init__(self,env,plug):
  super().__init__(env,plug)
  import json
  from pathlib import Path
  from yam_arena.urdf import quat_xyzw_to_matrix
  self.quat=quat_xyzw_to_matrix;f=json.loads(Path(__file__).with_name('press_point.json').read_text());self.point=np.array(f['point_tcp']);self.pressR=np.array(f['rotation']);self.press_depth=.0019;self.release=True;self.hold_offset=None;self.hold_rotation=None;self.pull_t0=None;self.last_travel=0.;self.failure=None
  ids,_=env._ids['left_robot'];d=self.base.scene['left_robot'].data.joint_pos;d=d.torch if hasattr(d,'torch') else d;self.leftq=d.detach().cpu().numpy()[0,ids].copy();self.leftp,self.leftr=ik.tcp_pose(self.leftq,env.rig.bases['left']);self.leftbias=np.zeros(3)
 def object_pose(self,name):
  d=self.base.arena_world.get_pose_w(name);d=d.torch if hasattr(d,'torch') else d;return d.detach().cpu().numpy()[0]
 def released_goal(self,t):
  from config import SERVICE,TARGET,port
  if self.hold_offset is None:
   p=self.object_pose(f'plug_{SERVICE}');ids,_=self.env._ids['right_robot'];d=self.base.scene['right_robot'].data.joint_pos;d=d.torch if hasattr(d,'torch') else d;q=d.detach().cpu().numpy()[0,ids];tcp,r=ik.tcp_pose(q,self.env.rig.bases['right']);rp=self.quat(p[3:]);self.hold_offset=rp.T@(tcp-p[:3]);self.hold_rotation=rp.T@r;self.held_origin=p[:3].copy();self.goal=tcp.copy();self.r=r.copy()
  g=.0015/abs(FINGER_OPEN);target=np.array(port(TARGET));source=self.held_origin
  if t>=15 and self.pull_t0 is None:
   if self.last_travel>=.0018:self.pull_t0=t
   elif t>=21:self.failure='clip did not reach release travel'
   return 'wait_for_measured_clip',self.goal,self.r,g
  if self.pull_t0 is not None:t=15+(t-self.pull_t0)
  if t<15:return 'hold_for_clip',self.goal,self.r,g
  if t<18:return 'withdraw_released_plug',self.goal+np.array((-.035*ik.smoothstep((t-15)/3),0,0)),self.r,g
  if t<20:return 'hold_unplugged',self.goal+np.array((-.035,0,0)),self.r,g
  alignment=target+self.hold_offset+np.array((-.035,0,0))
  if t<23:
   s=ik.smoothstep((t-20)/3);return 'align_target',self.goal+(-.035,0,0)+s*(alignment-self.goal-(-.035,0,0)),ik.slerp_matrix(self.r,self.hold_rotation,s),g
  if t<27:return 'insert_target',alignment+np.array((.035*ik.smoothstep((t-23)/4),0,0)),self.hold_rotation,g
  if t<29:return 'settle_target',target+self.hold_offset,self.hold_rotation,g
  if t<31:return 'release_target',target+self.hold_offset,self.hold_rotation,g+(1-g)*ik.smoothstep((t-29)/2)
  return 'retreat_target',target+self.hold_offset+np.array((-.10*ik.smoothstep((t-31)/3),0,.02)),self.hold_rotation,1.
 def command(self,time):
  from config import SERVICE,CLIP_Z
  old=self.previous.copy();target,report=super().command(time);t=time-self.start_time
  p0=self.object_pose(f'plug_{SERVICE}');rp=self.quat(p0[3:]);clip=self.object_pose(f'clip_{SERVICE}');travel=CLIP_Z-(rp.T@(clip[:3]-p0[:3]))[2];self.last_travel=float(travel)
  ids,fids=self.env._ids['left_robot'];d=self.base.scene['left_robot'].data.joint_pos;d=d.torch if hasattr(d,'torch') else d;qa=d.detach().cpu().numpy()[0];actual,r=ik.tcp_pose(qa[ids],self.env.rig.bases['left']);point=self.point.copy();point[0]+=qa[fids[0]]+.028
  contact=p0[:3]+rp@np.array((-.009,0,CLIP_Z+.0005));rotation=rp@self.pressR
  hover=contact+np.array((-.025,.030,.045))-rotation@point
  if t<8:pos=self.leftp;rgoal=self.leftr;g=1.
  elif t<11:
   s=ik.smoothstep((t-8)/3);pos=self.leftp+s*(hover-self.leftp);rgoal=ik.slerp_matrix(self.leftr,rotation,s);g=1+s*(.028/abs(FINGER_OPEN)-1)
  elif t<13:
   s=ik.smoothstep((t-11)/2);pos=hover+s*(contact+rp@np.array((0,0,.004))-rotation@point-hover);rgoal=rotation;g=.028/abs(FINGER_OPEN)
  elif t<(self.pull_t0+3 if self.pull_t0 is not None else 23):
   if t>=14:self.press_depth=float(np.clip(self.press_depth+.1*(.0019-travel),.0015,.0023))
   depth=self.press_depth*ik.smoothstep(min(1.,(t-13)/1.))
   pos=contact-rp@np.array((0,0,depth))-rotation@point;rgoal=rotation;g=.028/abs(FINGER_OPEN);self.retreat_start=pos.copy();self.retreat_rotation=rgoal.copy()
  else:
   s=ik.smoothstep(min(1.,(t-(self.pull_t0+3 if self.pull_t0 is not None else 23))/2));pos=self.retreat_start+np.array((-.03,.10,.06))*s;rgoal=self.retreat_rotation;g=.028/abs(FINGER_OPEN)
  self.leftbias=np.clip(self.leftbias+.08*(pos-actual),-.018,.018);self.leftq,pe,re=ik.solve(pos+self.leftbias,ik.matrix_to_quat_xyzw(rgoal),self.leftq,base_pos=self.env.rig.bases['left'],iters=90);target[:6]=self.leftq;target[6]=g;target[:7]=np.clip(target[:7],old[:7]-np.array([.04]*6+[.05]),old[:7]+np.array([.04]*6+[.05]));self.previous=target
  if self.pull_t0 is not None and t>=self.pull_t0+3 and p0[0]>.391:self.failure='plug did not withdraw from source jack'
  report|={'failure':self.failure,'left_tcp':actual.tolist(),'left_target':pos.tolist(),'left_position_error':float(np.linalg.norm(pos-actual)),'left_ik_error':pe,'left_ik_rotation_error':re,'clip_travel_m':float(travel)}
  return target,report
