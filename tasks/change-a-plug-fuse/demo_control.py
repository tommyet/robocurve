"""Robot-only tracking correction; never changes task objects."""
import numpy as np
from scipy.optimize import least_squares
class DemoControl:
 def __init__(self):self.grasp=None
 def action(self,k,wanted,m,observed,hands):
  from yam_arena import ik,station
  from geometry import FC
  from scipy.spatial.transform import Rotation as Rot
  if k>=200 and self.grasp is None:
   H=hands['right'];self.grasp=(H['rotation'].T@(m.p('screwdriver')-H['tcp']),H['rotation'].T@m.orientation('screwdriver'),m.p('screwdriver',[0,.069,0]),m.orientation('screwdriver').copy())
  out=wanted.copy()
  for side,o in [('left',0),('right',7)]:
   target,R=ik.tcp_pose(wanted[o:o+6],station.BASES[side])
   if side=='right' and self.grasp is not None:
    t_rel,r_rel,start_tip,start_R=self.grasp;H=hands['right'];t_rel=H['rotation'].T@(m.p('screwdriver')-H['tcp']);r_rel=H['rotation'].T@m.orientation('screwdriver');P=m.orientation('plug');base=m.p('plug');Rtool=P@Rot.from_euler('z',90,degrees=True).as_matrix()
    insert=base+P@(FC+np.array([.0135,0,.005-.002]));outside=insert+P@np.array([.009,0,0]);fulcrum=base+P@(FC+np.array([.020,0,.0014]))
    if k<=260:
     u=ik.smoothstep((k-200)/60);tip=start_tip+u*(outside-start_tip);Rtool=ik.slerp_matrix(start_R,Rtool,u)
    elif k<=300:
     u=ik.smoothstep((k-260)/40);tip=outside+u*(insert-outside)
    else:
     u=ik.smoothstep(min(1.,(k-300)/80));turn=Rot.from_euler('y',15*u,degrees=True).as_matrix();tip=fulcrum+P@turn@P.T@(insert-fulcrum);Rtool=P@turn@P.T@Rtool
    if k>380:tip+=P@np.array([0,0,.008*ik.smoothstep(min(1.,(k-380)/60))])
    R=Rtool@r_rel.T;target=tip-R@(t_rel+r_rel@np.array([0,.069,0]))
   seed=np.clip(observed[o:o+6],ik.LOWER+1e-6,ik.UPPER-1e-6)
   p0,R0=ik.tcp_pose(seed,station.BASES[side]);bias=hands[side]['tcp']-p0;rbias=hands[side]['rotation']@R0.T
   def residual(q):
    pp,rr=ik.tcp_pose(q,station.BASES[side]);return np.r_[pp+bias-target,.10*ik._rot_error(R,rbias@rr),.001*(q-seed)]
   out[o:o+6]=least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=25).x
  return out
