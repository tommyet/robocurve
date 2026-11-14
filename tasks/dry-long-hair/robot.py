"""Bimanual dryer brace, real slider actuation, handle lift and airflow probe."""
import json
from pathlib import Path
import numpy as np
from yam_arena import ik
from yam_arena.constants import FINGER_OPEN
from yam_arena.urdf import quat_xyzw_to_matrix,axis_angle_matrix
from config import *
LEFT_R=np.array([[-1.,0.,0.],[0.,0.,-1.],[0.,-1.,0.]])
class DryerProbe:
 def __init__(self,env):
  self.env=env;self.base=env._base;self.previous=env._ready.detach().cpu().numpy().reshape(-1).copy();self.bias=[np.zeros(3),np.zeros(3)];self.failure=None;self.hold_offset=None
  f=json.loads(Path(__file__).with_name('switch_point.json').read_text());self.point=np.array(f['point_tcp']);self.switchR=np.array(f['rotation']);self.q=[];self.starts=[]
  for side in ['left','right']:
   ids,_=env._ids[side+'_robot'];d=self.base.scene[side+'_robot'].data.joint_pos;d=d.torch if hasattr(d,'torch') else d;q=d.detach().cpu().numpy()[0,ids];self.q.append(q.copy());self.starts.append(ik.tcp_pose(q,env.rig.bases[side]))
 def pose(self,name):
  d=self.base.arena_world.get_pose_w(name);d=d.torch if hasattr(d,'torch') else d;return d.detach().cpu().numpy()[0]
 def command(self,t):
  dryer=self.pose('dryer');switch=self.pose('switch');rd=quat_xyzw_to_matrix(dryer[3:]);local=rd.T@(switch[:3]-dryer[:3]);power=float(np.clip((local[2]+.045)/SWITCH_TRAVEL,0,1));hold=np.array(DRYER_START)+np.array((-.019,-.003,-.065));grip=.006/abs(FINGER_OPEN)
  lp0,lr0=self.starts[0];rp0,rr0=self.starts[1]
  if t<3:
   phase='approach_handle_brace';s=ik.smoothstep(t/3);lp=lp0+s*(hold+np.array((0,.08,0.))-lp0);lr=ik.slerp_matrix(lr0,LEFT_R,s);lg=1-.55*s
  elif t<5:
   phase='enter_handle_brace';s=ik.smoothstep((t-3)/2);lp=hold+np.array((0,.08,0.))*(1-s);lr=LEFT_R;lg=.45
  elif t<7:
   phase='grip_and_brace';lp=hold;lr=LEFT_R;lg=.45+(grip-.45)*ik.smoothstep((t-5)/2)
  elif t<16:phase='operate_real_slider';lp=hold;lr=LEFT_R;lg=grip
  elif t<19:phase='lift_dryer';lp=hold+np.array((0,0,.10*ik.smoothstep((t-16)/3)));lr=LEFT_R;lg=grip
  else:
   if self.hold_offset is None:
    ids,_=self.env._ids['left_robot'];d=self.base.scene['left_robot'].data.joint_pos;d=d.torch if hasattr(d,'torch') else d;tcp,r=ik.tcp_pose(d.detach().cpu().numpy()[0,ids],self.env.rig.bases['left']);self.hold_offset=rd.T@(tcp-dryer[:3]);self.hold_rotation=rd.T@r;self.lift_p=tcp.copy();self.lift_r=r.copy()
    if dryer[2]<DRYER_START[2]+.05:self.failure='handle grasp did not lift dryer'
   direction=np.array((.17,-.09,0.));direction/=np.linalg.norm(direction);bodyR=axis_angle_matrix(np.array([0.,0.,1.]),np.arctan2(direction[1],direction[0]));nozzle=np.array((.26,.12,.92));body=nozzle-bodyR@np.array((.088,0,0));goal=body+bodyR@self.hold_offset;goalr=bodyR@self.hold_rotation;s=ik.smoothstep(min(1.,(t-19)/3));lp=self.lift_p+s*(goal-self.lift_p);lr=ik.slerp_matrix(self.lift_r,goalr,s);lg=grip;phase='aim_and_hold_airflow'
  ids,fids=self.env._ids['right_robot'];d=self.base.scene['right_robot'].data.joint_pos;d=d.torch if hasattr(d,'torch') else d;qa=d.detach().cpu().numpy()[0];point=self.point.copy();point[0]-=qa[fids[1]]+.028;rotation=rd@self.switchR;contact=dryer[:3]+rd@np.array((-.039,0,-.047));press=contact-rotation@point;hover=press+np.array((-.035,0,.020))
  if t<7:rp=rp0;rr=rr0;rg=1.
  elif t<10:
   s=ik.smoothstep((t-7)/3);rp=rp0+s*(hover-rp0);rr=ik.slerp_matrix(rr0,rotation,s);rg=1+s*(.028/abs(FINGER_OPEN)-1)
  elif t<12:
   s=ik.smoothstep((t-10)/2);rp=hover+s*(press-hover);rr=rotation;rg=.028/abs(FINGER_OPEN)
  elif t<14:
   rp=press+rd@np.array((0,0,.0048*ik.smoothstep((t-12)/2)));rr=rotation;rg=.028/abs(FINGER_OPEN);self.slide_end=rp.copy();self.slide_rotation=rr.copy()
  elif t<16:
   rp=self.slide_end+np.array((-.04,0,.06))*ik.smoothstep((t-14)/2);rr=self.slide_rotation;rg=.028/abs(FINGER_OPEN);self.retreat_p=rp.copy();self.retreat_r=rr.copy()
   if t>15.5 and power<.7:self.failure='physical slider did not remain on'
  else:
   s=ik.smoothstep(min(1.,(t-16)/3));rp=self.retreat_p+s*(rp0-self.retreat_p);rr=ik.slerp_matrix(self.retreat_r,rr0,s);rg=.6+.4*s
  targets=[(lp,lr,lg),(rp,rr,rg)];out=self.env._ready.detach().cpu().numpy().reshape(-1).copy();errors=[]
  for i,side in enumerate(['left','right']):
   p,r,g=targets[i];ids,_=self.env._ids[side+'_robot'];d=self.base.scene[side+'_robot'].data.joint_pos;d=d.torch if hasattr(d,'torch') else d;actual,_=ik.tcp_pose(d.detach().cpu().numpy()[0,ids],self.env.rig.bases[side]);self.bias[i]=np.clip(self.bias[i]+.08*(p-actual),-.018,.018);self.q[i],pe,re=ik.solve(p+self.bias[i],ik.matrix_to_quat_xyzw(r),self.q[i],base_pos=self.env.rig.bases[side],iters=90);out[7*i:7*i+6]=self.q[i];out[7*i+6]=g;errors.append({'side':side,'tcp':actual.tolist(),'target':p.tolist(),'tracking_error':float(np.linalg.norm(p-actual)),'ik_error':pe,'ik_rotation_error':re})
  delta=np.array([.04]*6+[.05]+[.04]*6+[.05]);out=np.clip(out,self.previous-delta,self.previous+delta);out=np.clip(out,self.env._low,self.env._high);self.previous=out
  return out,{'phase':phase,'arms':errors,'measured_power_fraction':power,'failure':self.failure}
