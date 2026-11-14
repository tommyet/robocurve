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
