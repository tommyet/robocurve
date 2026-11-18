"""Robot-only tracking correction; never changes task objects."""
import numpy as np
from scipy.optimize import least_squares
class DemoControl:
 def __init__(self):self.grasp=None;self.phase_id=None;self.grasps={};self.last_goal=None
 def action(self,k,wanted,m,observed,hands):
  from yam_arena import ik,station
  from geometry import FC
  from scipy.spatial.transform import Rotation as Rot
  if k>=200 and self.grasp is None:
   H=hands['right'];self.grasp=(H['rotation'].T@(m.p('screwdriver')-H['tcp']),H['rotation'].T@m.orientation('screwdriver'),m.p('screwdriver',[0,.119,0]),m.orientation('screwdriver').copy())
  out=wanted.copy()
  for side,o in [('left',0),('right',7)]:
   target,R=ik.tcp_pose(wanted[o:o+6],station.BASES[side]);tool_tip_local=None;tip_target=None
   if side=='right' and self.grasp is not None and k<=480:
    t_rel,r_rel,start_tip,start_R=self.grasp;H=hands['right'];t_rel=H['rotation'].T@(m.p('screwdriver')-H['tcp']);r_rel=H['rotation'].T@m.orientation('screwdriver');P=m.orientation('plug');base=m.p('plug');Rtool=P@Rot.from_euler('z',90,degrees=True).as_matrix()
    insert=base+P@(FC+np.array([.0155,0,-.0005]));outside=insert+P@np.array([.009,0,0]);fulcrum=base+P@(FC+np.array([.023,0,-.0006]))
    if k<=260:
     u=ik.smoothstep((k-200)/60);tip=start_tip+u*(outside-start_tip);Rtool=ik.slerp_matrix(start_R,Rtool,u)
    elif k<=300:
     u=ik.smoothstep((k-260)/40);tip=outside+u*(insert-outside)
    else:
     u=ik.smoothstep(min(1.,(k-300)/80));turn=Rot.from_euler('y',45*u,degrees=True).as_matrix();tip=fulcrum+P@turn@P.T@(insert-fulcrum);Rtool=P@turn@P.T@Rtool
    if k>380:tip+=P@np.array([0,0,.008*ik.smoothstep(min(1.,(k-380)/60))])
    tool_tip_local=t_rel+r_rel@np.array([0,.119,0]);tip_target=tip.copy()
    R=Rtool@r_rel.T;target=tip-R@tool_tip_local
   if side=='right' and k>480:
    from sequence import PHASES
    start=480
    for index,phase in enumerate(PHASES):
     end=start+phase['n']
     if k<=end:break
     start=end
    if self.phase_id!=index:
     self.phase_id=index;self.phase_start=(hands[side]['tcp'].copy(),hands[side]['rotation'].copy())
     obj=phase['obj'];pos=m.p(obj);OR=m.orientation(obj);kind=phase['kind']
     if kind=='pick':
      from common import down
      goalR=OR@down(-90) if obj=='carrier' else phase['rotation'];goal=pos+OR@phase['point']+phase['delta'];self.grasps.pop(obj,None)
     elif kind in ['move','lift']:
      H=hands[side]
      if obj not in self.grasps:self.grasps[obj]=(H['rotation'].T@(pos-H['tcp']),H['rotation'].T@OR)
      tr,rr=self.grasps[obj];goalObj=pos+phase['delta'] if kind=='lift' else phase['position'];objR=phase['rotation'] if phase['rotation'] is not None else OR
      if phase.get('relative')=='plug':goalObj=m.p('plug')+m.orientation('plug')@goalObj;objR=m.orientation('plug')@objR
      goalR=objR@rr.T;goal=goalObj-goalR@tr
     elif kind=='withdraw':goal=self.phase_start[0]+phase['delta'];goalR=self.phase_start[1]
     else:goal,goalR=self.last_goal
     self.phase_goal=(goal,goalR);self.last_goal=self.phase_goal
    u=ik.smoothstep((k-start)/phase['n']);target=self.phase_start[0]+u*(self.phase_goal[0]-self.phase_start[0]);R=ik.slerp_matrix(self.phase_start[1],self.phase_goal[1],u)
   seed=np.clip(observed[o:o+6],ik.LOWER+1e-6,ik.UPPER-1e-6)
   p0,R0=ik.tcp_pose(seed,station.BASES[side]);bias=hands[side]['tcp']-p0;rbias=hands[side]['rotation']@R0.T
   def residual(q):
    pp,rr=ik.tcp_pose(q,station.BASES[side]);actual_R=rbias@rr
    position=pp+bias-target if tool_tip_local is None else pp+bias+actual_R@tool_tip_local-tip_target
    return np.r_[position*(3. if tool_tip_local is not None else 1.),.05*ik._rot_error(R,actual_R),.001*(q-seed)]
   out[o:o+6]=least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=25).x
  return out
