"""Robot-only tracking correction; never changes task objects."""
import numpy as np
from scipy.optimize import least_squares
class DemoControl:
 def __init__(self):self.grasp=None;self.phase_id=None;self.grasps={};self.last_goal=None;self.plug_hold=None
 def action(self,k,wanted,m,observed,hands):
  from yam_arena import ik,station
  from geometry import FC
  from scipy.spatial.transform import Rotation as Rot
  if k>=200 and self.grasp is None:
   H=hands['right'];self.grasp=(H['rotation'].T@(m.p('screwdriver')-H['tcp']),H['rotation'].T@m.orientation('screwdriver'),m.p('screwdriver',[0,.119,0]),m.orientation('screwdriver').copy())
  if k>=200 and self.plug_hold is None:
   H=hands['left'];nominal,_=ik.tcp_pose(wanted[:6],station.BASES['left'])
   self.plug_hold=(m.p('plug').copy(),m.orientation('plug').copy(),nominal)
  out=wanted.copy()
  for side,o in [('left',0),('right',7)]:
   target,R=ik.tcp_pose(wanted[o:o+6],station.BASES[side]);tool_tip_local=None;tip_target=None
   if side=='left' and self.plug_hold is not None and wanted[o+6]<.2:
    from geometry import PLUG_ROT
    centre,start_R,nominal=self.plug_hold;H=hands['left'];P=m.orientation('plug')
    desired_R=ik.slerp_matrix(start_R,PLUG_ROT.as_matrix(),ik.smoothstep(min(1.,(k-200)/60)))
    desired_centre=centre+(target-nominal)
    relative=H['rotation'].T@P;offset=H['rotation'].T@(m.p('plug')-H['tcp'])
    R=desired_R@relative.T;target=desired_centre-R@offset
   if side=='right' and self.grasp is not None and k<=520:
    t_rel,r_rel,start_tip,start_R=self.grasp;H=hands['right'];t_rel=H['rotation'].T@(m.p('screwdriver')-H['tcp']);r_rel=H['rotation'].T@m.orientation('screwdriver');P=m.orientation('plug');base=m.p('plug');Rtool=P@Rot.from_euler('z',90,degrees=True).as_matrix()
    insert=base+P@(FC+np.array([.0155,0,0.]));outside=insert+P@np.array([.009,0,0]);fulcrum=base+P@(FC+np.array([.023,0,-.0006]))
    if k<=300:
     u=ik.smoothstep((k-200)/100);tip=start_tip+u*(outside-start_tip);Rtool=ik.slerp_matrix(start_R,Rtool,u)
    elif k<=340:tip=outside
    elif k<=420:
     u=ik.smoothstep((k-340)/80);tip=outside+u*(insert-outside)
    else:
     # Raise the blade under the carrier lip while keeping the handle level.
     tip=insert+P@np.array([0,0,.012*ik.smoothstep(min(1.,(k-420)/60))])
    tool_tip_local=t_rel+r_rel@np.array([0,.119,0]);tip_target=tip.copy()
    R=Rtool@r_rel.T;target=tip-R@tool_tip_local
   if side=='right' and k>520:
    from sequence import PHASES
    start=520
    for index,phase in enumerate(PHASES):
     end=start+phase['n']
     if k<=end:break
     start=end
    if self.phase_id!=index:
     self.phase_id=index;self.phase_start=(hands[side]['tcp'].copy(),hands[side]['rotation'].copy())
     obj=phase['obj'];pos=m.p(obj);OR=m.orientation(obj);kind=phase['kind'];self.phase_object_start=pos.copy()
     if kind=='pick':
      from common import down
      axis=OR[:,0];yaw=np.arctan2(axis[1],axis[0]);goalR=Rot.from_euler('z',yaw).as_matrix()@down(-90)
      point=phase['point'].copy();height=point[2];point[2]=0.
      goal=pos+OR@point+phase['delta']+np.array([0.,0.,height]);self.grasps.pop(obj,None)
     elif kind in ['move','lift']:
      H=hands[side]
      if obj not in self.grasps:self.grasps[obj]=(H['rotation'].T@(pos-H['tcp']),H['rotation'].T@OR)
      tr,rr=self.grasps[obj];goalObj=pos+phase['delta'] if kind=='lift' else phase['position'];objR=phase['rotation'] if phase['rotation'] is not None else OR
      if phase.get('relative')=='plug':goalObj=m.p('plug')+m.orientation('plug')@goalObj;objR=m.orientation('plug')@objR
      goalR=objR@rr.T;goal=goalObj-goalR@tr
     elif kind=='withdraw':goal=self.phase_start[0]+phase['delta'];goalR=self.phase_start[1]
     else:goal,goalR=self.last_goal
     self.phase_goal=(goal,goalR);self.last_goal=self.phase_goal
    if phase['kind']=='lift' and k==end:
     if phase['obj']=='old_fuse':lift=float((m.p('old_fuse')-m.p('plug',FC))@m.orientation('plug')[:,2])
     else:lift=float((m.p(phase['obj'])-self.phase_object_start)[2])
     if lift<.025:raise RuntimeError('The scripted pickup did not lift the part; stop this diagnostic.')
    if phase['kind']=='pick':
     # The hand-held plug settles during insertion. Follow the measured
     # part throughout pickup rather than an obsolete phase-start pose.
     obj=phase['obj'];pos=m.p(obj);OR=m.orientation(obj)
     from common import down
     yaw=np.arctan2(OR[1,0],OR[0,0]);goalR=Rot.from_euler('z',yaw).as_matrix()@down(-90)
     point=phase['point'].copy();height=point[2];point[2]=0.
     goal=pos+OR@point+phase['delta']+np.array([0.,0.,height])
     if obj=='old_fuse':
      P=m.orientation('plug');goalR=P@down(-90)
      goal=pos+OR@point+P@(phase['delta']+np.array([0.,0.,height]))
     self.phase_goal=(goal,goalR);self.last_goal=self.phase_goal
    if phase['kind']=='lift' and phase['obj']=='old_fuse':
     tr,rr=self.grasps['old_fuse'];P=m.orientation('plug')
     goalR=P@rr.T;goal=m.p('plug',FC)+P@phase['delta']-goalR@tr
     self.phase_goal=(goal,goalR);self.last_goal=self.phase_goal
    if phase.get('relative')=='plug' and phase['kind']=='move':
     tr,rr=self.grasps[phase['obj']];plugR=m.orientation('plug')
     goalR=plugR@phase['rotation']@rr.T
     goal=m.p('plug')+plugR@phase['position']-goalR@tr
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
