"""Bimanual plain-rim grip/lift diagnostic, using ordinary YAM targets only."""
import numpy as np
from yam_arena import ik
from yam_arena.demo import grip_rotation
from yam_arena.constants import FINGER_OPEN
from config import *
class CartonGripProbe:
 def __init__(self,env):
  self.env=env;self.q=[];self.starts=[];self.bias=[np.zeros(3),np.zeros(3)];self.previous=env._ready.detach().cpu().numpy().reshape(-1).copy();self.down=grip_rotation()
  for side in ['left','right']:
   ids,_=env._ids[side+'_robot'];d=env._base.scene[side+'_robot'].data.joint_pos;d=d.torch if hasattr(d,'torch') else d;q=d.detach().cpu().numpy()[0,ids];self.q.append(q.copy());self.starts.append(ik.tcp_pose(q,env.rig.bases[side]))
 def command(self,time):
  out=self.env._ready.detach().cpu().numpy().reshape(-1).copy();report=[]
  for i,side in enumerate(['left','right']):
   sign=1 if i==0 else -1;goal=np.array((CENTER[0],sign*.09,TOP+.087));hover=goal+np.array((0,0,.10));start,rstart=self.starts[i]
   if time<3:
    phase='approach_rim';s=ik.smoothstep(time/3);p=start+s*(hover-start);r=ik.slerp_matrix(rstart,self.down,s);g=1-s*.70
   elif time<6:
    phase='enter_rim';s=ik.smoothstep((time-3)/3);p=hover+s*(goal-hover);r=self.down;g=.30
   elif time<8:
    phase='pinch_plain_rim';p=goal;r=self.down;g=.30*(1-ik.smoothstep((time-6)/2))
   elif time<11:
    phase='lift_carton';p=goal+np.array((0,0,.09*ik.smoothstep((time-8)/3)));r=self.down;g=0.
   elif time<13:
    phase='hold_carton';p=goal+np.array((0,0,.09));r=self.down;g=0.
   elif time<16:
    phase='lower_carton';p=goal+np.array((0,0,.09*(1-ik.smoothstep((time-13)/3))));r=self.down;g=0.
   elif time<18:
    phase='release_rim';p=goal;r=self.down;g=.30*ik.smoothstep((time-16)/2)
   else:
    phase='retreat';p=goal+np.array((0,0,.10*ik.smoothstep((time-18)/3)));r=self.down;g=.30
   ids,_=self.env._ids[side+'_robot'];d=self.env._base.scene[side+'_robot'].data.joint_pos;d=d.torch if hasattr(d,'torch') else d;qa=d.detach().cpu().numpy()[0,ids];tcp,_=ik.tcp_pose(qa,self.env.rig.bases[side]);self.bias[i]=np.clip(self.bias[i]+.08*(p-tcp),-.020,.020)
   self.q[i],pe,re=ik.solve(p+self.bias[i],ik.matrix_to_quat_xyzw(r),self.q[i],base_pos=self.env.rig.bases[side],iters=90);off=i*7;out[off:off+6]=self.q[i];out[off+6]=g;report.append({'side':side,'phase':phase,'target':p.tolist(),'tcp':tcp.tolist(),'position_error':float(np.linalg.norm(p-tcp)),'ik_error':pe,'ik_rotation_error':re,'grip':g})
  delta=np.array([.04]*6+[.05]+[.04]*6+[.05]);out=np.clip(out,self.previous-delta,self.previous+delta);out=np.clip(out,self.env._low,self.env._high);self.previous=out
  return out,report

class CartonCutProbe:
 """Proven ordinary cutter prefix adapted to an actually bottom-up free carton."""
 def __init__(self,env):
  from yam_arena.demo import ArmPlan,Waypoint as W
  self.env=env;self.previous=env._ready.detach().cpu().numpy().reshape(-1).copy();grip=-.011;O=FINGER_OPEN;lid=TOP+.1015;hover=TOP+.17;zcut=lid+.029;zhigh=lid+.06;x,y,z=CUTTER_START
  path=[W(2.,(x,y,hover),O),W(2.,(x,y,z+.006),O),W(1.,(x,y,z+.006),grip),W(2.,(x,y,hover),grip),W(2.,(CENTER[0]-.11-.070,-.002,zhigh),grip),W(2.,(CENTER[0]-.11-.070,-.002,zcut),grip),W(6.,(CENTER[0]+.11-.045,-.002,zcut),grip),W(1.,(CENTER[0]+.11-.045,-.002,lid+.036),grip)]
  for xx in [CENTER[0]-.11,CENTER[0]+.11]:path += [W(2.,(xx,.100,lid+.036),grip,yaw=-np.pi/2),W(1.5,(xx,.100,zcut),grip,yaw=-np.pi/2),W(2.,(xx,.025,zcut),grip,yaw=-np.pi/2),W(1.,(xx,.025,lid+.036),grip,yaw=-np.pi/2)]
  path += [W(2.,(x,y,hover),grip),W(2.,(x,y,z+.006),grip),W(1.,(x,y,z+.006),O),W(2.,(x,y,hover),O)]
  self.plan=ArmPlan(path,env.rig.bases['left']);self.park=ArmPlan([W(3.,(.13,-.24,TOP+.17),O)],env.rig.bases['right']);self.duration=self.plan.duration;self.failure=None
 def command(self,time):
  from yam_arena.urdf import quat_xyzw_to_matrix,axis_angle_matrix
  from model import WIDTH,HEIGHT
  def pose(name):
   d=self.env._base.arena_world.get_pose_w(name);d=d.torch if hasattr(d,'torch') else d;return d.detach().cpu().numpy()[0]
  if time<7. or time>=41.:
   t=time if time<7. else self.plan.duration-7.+time-41.
   a,la=self.plan.action7(t+.05);b,_=self.park.action7(time+.05);out=np.r_[a,b];phase='pickup_cutter' if time<7 else 'park_cutter'
   report=[{'side':'left','phase':phase,'position_error':0.,'ik_error':self.plan.worst_ik_mm/1000},{'side':'right','phase':'park','position_error':0.}]
  else:
   ids,_=self.env._ids['left_robot'];d=self.env._base.scene['left_robot'].data.joint_pos;d=d.torch if hasattr(d,'torch') else d;qa=d.detach().cpu().numpy()[0,ids];tcp,rhand=ik.tcp_pose(qa,self.env.rig.bases['left']);cutter=pose('cutter');rc=quat_xyzw_to_matrix(cutter[3:]);actualtip=cutter[:3]+rc@np.array((.062,0,-.020));north=pose('north');reference=quat_xyzw_to_matrix(north[3:]);origin=north[:3]-reference@np.array((0,WIDTH/2,HEIGHT/2))
   segments=[(7.0, 11.0, (-0.12, 0, -0.05), (-0.12, 0, -0.025), 0.0, 'seam_hover'), (11.0, 13.0, (-0.12, 0, -0.025), (-0.12, 0, -0.001), 0.0, 'seam_lower'), (13.0, 21.0, (-0.12, 0, -0.001), (0.12, 0, -0.001), 0.0, 'seam_cut'), (21.0, 22.0, (0.12, 0, -0.001), (0.12, 0, -0.025), 0.0, 'seam_lift'), (22.0, 25.0, (0.12, 0, -0.025), (-0.11, -0.034, -0.025), -1.5707963267948966, 'front_hover'), (25.0, 26.5, (-0.11, -0.034, -0.025), (-0.11, -0.034, -0.001), -1.5707963267948966, 'front_lower'), (26.5, 30.5, (-0.11, -0.034, -0.001), (-0.11, 0.034, -0.001), -1.5707963267948966, 'front_cut'), (30.5, 31.5, (-0.11, 0.034, -0.001), (-0.11, 0.034, -0.025), -1.5707963267948966, 'front_lift'), (31.5, 34.5, (-0.11, 0.034, -0.025), (0.11, -0.034, -0.025), -1.5707963267948966, 'back_hover'), (34.5, 36.0, (0.11, -0.034, -0.025), (0.11, -0.034, -0.001), -1.5707963267948966, 'back_lower'), (36.0, 40.0, (0.11, -0.034, -0.001), (0.11, 0.034, -0.001), -1.5707963267948966, 'back_cut'), (40.0, 41.0, (0.11, 0.034, -0.001), (0.11, 0.034, -0.025), -1.5707963267948966, 'back_lift')]
   for t0,t1,p0,p1,yaw,phase in segments:
    if t0<=time<t1:break
   s=ik.smoothstep((time-t0)/(t1-t0));point=np.array(p0)+s*(np.array(p1)-p0);goal=origin+reference@point;error=goal-actualtip
   if not hasattr(self,'tip_bias'):self.tip_bias=np.zeros(3)
   self.tip_bias=np.clip(self.tip_bias+.12*error,-.030,.030) if np.linalg.norm(error)<.008 else self.tip_bias*.95;p=tcp+np.clip(.65*error+self.tip_bias,-.004,.004);toolR=reference@np.diag([1.,-1.,-1.])@axis_angle_matrix(np.array([0.,0.,1.]),yaw);r=toolR@rc.T@rhand
   q,pe,re=ik.solve(p,ik.matrix_to_quat_xyzw(r),qa,base_pos=self.env.rig.bases['left'],iters=90);self.plan.q=q;g=-.011/FINGER_OPEN;b,_=self.park.action7(time+.05);out=np.r_[q,g,b];report=[{'side':'left','phase':phase,'position_error':float(np.linalg.norm(error)),'blade_target':goal.tolist(),'blade_actual':actualtip.tolist(),'ik_error':pe,'ik_rotation_error':re},{'side':'right','phase':'park','position_error':0.}]
  delta=np.array([.04]*6+[.05]+[.04]*6+[.05]);out=np.clip(out,self.previous-delta,self.previous+delta);out=np.clip(out,self.env._low,self.env._high);self.previous=out
  return out,report

class CartonOpenProbe(CartonGripProbe):
 """Grip each ordinary free flap edge and verify native angular progress.

 This diagnostic requires an explicitly unsealed starting carton. It never
 edits hinges or object state; completion of it is not full task completion.
 """
 def __init__(self,env):
  super().__init__(env)
  from scene import layout
  self.hinges={h['a']:h for h in layout()[1] if h['b'].endswith('_bottom')}
  self.order=['south','north','east','west'];self.index=0;self.stage='approach';self.started=0.;self.failure=None;self.offset=None;self.last_progress=0.;self.last_angle=-180.;self.command_angle=0.;self.entered=False
 def pose(self,name):
  from yam_arena.urdf import quat_xyzw_to_matrix
  d=self.env._base.arena_world.get_pose_w(name);d=d.torch if hasattr(d,'torch') else d;p=d.detach().cpu().numpy()[0];return p[:3],quat_xyzw_to_matrix(p[3:])
 def edge(self,name,angle=None):
  from yam_arena.urdf import axis_angle_matrix
  h=self.hinges[name];wp,wr=self.pose(name);fp,fr=self.pose(name+'_bottom')
  a=float(np.degrees(np.arctan2((wr.T@fr)[2,1],(wr.T@fr)[1,1])))
  if angle is not None:
   fr=wr@axis_angle_matrix(np.array([1.,0,0]),np.radians(angle));fp=wp+wr@np.array(h['anchor_a'])-fr@np.array(h['anchor_b'])
  offset=np.array((0.,-(.18/2-.003)/2+.010,-.006)) if self.offset is None else self.offset
  p=fp+fr@offset;outward=wr[:,1].copy();outward[2]=0.;outward/=np.linalg.norm(outward)
  theta=np.radians(max(35.,50.-(a if angle is None else angle)));approach=outward*np.sin(theta)-np.array([0.,0.,1.])*np.cos(theta);sign=1 if name in ['south','east'] else -1;x=sign*np.cross(np.array([0.,0.,1.]),outward);y=np.cross(approach,x);r=np.column_stack([x,y,approach]);return p,r,a
 def command(self,time):
  out=self.env._ready.detach().cpu().numpy().reshape(-1).copy();report=[]
  if self.index>=4 or self.failure:
   return self.previous.copy(),[{'side':'left','phase':'failed' if self.failure else 'flaps_opened','failure':self.failure},{'side':'right','phase':'hold'}]
  name=self.order[self.index];i=1 if name in ['south','east'] else 0;side=['left','right'][i];p,r,angle=self.edge(name);elapsed=time-self.started;opened=.018/(2*abs(FINGER_OPEN));closed=.002/(2*abs(FINGER_OPEN))
  ids,fids=self.env._ids[side+'_robot'];d=self.env._base.scene[side+'_robot'].data.joint_pos;d=d.torch if hasattr(d,'torch') else d;actualq=d.detach().cpu().numpy()[0];actual,actualR=ik.tcp_pose(actualq[ids],self.env.rig.bases[side])
  if not self.entered:self.startp=actual.copy();self.startr=actualR.copy();self.entered=True
  if self.stage=='approach':
   s=ik.smoothstep(min(1.,elapsed/3));target=self.startp+s*(p-r[:,2]*.075-self.startp);rotation=ik.slerp_matrix(self.startr,r,s);g=opened
   if elapsed>=3:self.stage='enter';self.started=time;self.startp=actual.copy()
  elif self.stage=='enter':
   s=ik.smoothstep(min(1.,elapsed/2));target=self.startp+s*(p-self.startp);rotation=r;g=opened
   if elapsed>=2:self.stage='pinch';self.started=time
  elif self.stage=='pinch':
   target=p;rotation=r;g=opened+(closed-opened)*ik.smoothstep(min(1.,elapsed))
   if elapsed>=1.4:
    fp,fr=self.pose(name+'_bottom');self.offset=fr.T@(actual-fp);self.stage='rotate';self.started=time;self.command_angle=angle;self.last_angle=angle;self.last_progress=time
  elif self.stage=='rotate':
   if angle>self.last_angle+2:self.last_progress=time;self.last_angle=angle
   if time-self.last_progress>4:self.failure=name+' flap did not follow the gripper'
   self.command_angle=min(165.,angle+12.,self.command_angle+.8);target,rotation,_=self.edge(name,self.command_angle);g=closed
   if angle>=155:self.stage='release';self.started=time;self.startp=actual.copy();self.startr=actualR.copy()
  elif self.stage=='release':
   target=self.startp;rotation=self.startr;g=closed+(opened-closed)*ik.smoothstep(min(1.,elapsed))
   if elapsed>=1.3:self.stage='retreat';self.started=time
  else:
   target=self.startp-self.startr[:,2]*.075*ik.smoothstep(min(1.,elapsed/2));rotation=self.startr;g=opened
   if elapsed>=2:
    if angle<150:self.failure=name+' flap did not remain open after release'
    else:self.index+=1;self.offset=None;self.entered=False;self.stage='approach';self.started=time
  error=target-actual;self.bias[i]=np.clip(self.bias[i]+.06*error,-.015,.015);q,pe,re=ik.solve(target+self.bias[i],ik.matrix_to_quat_xyzw(rotation),actualq[ids],base_pos=self.env.rig.bases[side],iters=90);out[7*i:7*i+6]=q;out[7*i+6]=g
  # The idle arm holds its previous ordinary target rather than crossing the carton.
  j=1-i;out[7*j:7*j+7]=self.previous[7*j:7*j+7]
  delta=np.array([.04]*6+[.05]+[.04]*6+[.05]);out=np.clip(out,self.previous-delta,self.previous+delta);out=np.clip(out,self.env._low,self.env._high);self.previous=out
  return out,[{'side':side,'phase':name+':'+self.stage,'angle_deg':angle,'position_error':float(np.linalg.norm(error)),'failure':self.failure},{'side':['left','right'][j],'phase':'hold'}]
