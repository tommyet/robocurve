"""Native pose feedback used only to command the two robot arms."""
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot
class DemoControl:
 def __init__(self):self.pick_index=None;self.pick=None;self.angle=0.;self.pick_R=None
 def action(self,k,wanted,m,observed,hands):
  from yam_arena import ik,station
  from geometry import FRONT,POINTS,LINKS,pickup_index,R as RING_RADIUS
  if k<=100:
   links=np.array([m.p(f'link_{i:03d}') for i in range(LINKS)])
   if self.pick_index is None:self.pick_index=pickup_index(links)
   self.pick=links[self.pick_index].copy()+[-.005,0,0]
   tangent=m.orientation(f'link_{self.pick_index:03d}')[:,0].copy();tangent[0]=0.;tangent/=np.linalg.norm(tangent)
   axis=np.array([1.,0,0]);self.pick_R=np.column_stack([np.cross(tangent,axis),tangent,axis])
   v=m.orientation('chainring')[:,1];self.angle=float(np.arctan2(v[2],v[1]))
  if k==341:
   v=m.orientation('chainring')[:,1];self.angle=float(np.arctan2(v[2],v[1]))
  out=wanted.copy()
  for side,o in [('left',0),('right',7)]:
   target,R=ik.tcp_pose(wanted[o:o+6],station.BASES[side])
   if side=='left':
    turn=Rot.from_euler('x',self.angle*max(0.,min(1.,(k-340)/60))).as_matrix();target=FRONT+turn@(target-FRONT)
   else:
    from demo_targets import PICK,ROTATION
    R=ik.slerp_matrix(R,self.pick_R,min(1.,k/60)) if k<=480 else R@ROTATION.T@self.pick_R
    if k==220:
     distance=min(np.linalg.norm(m.p(f'link_{i:03d}')-hands['right']['tcp']) for i in range(LINKS))
     if distance>.025:raise RuntimeError('Scripted chain pickup missed; stop before tooth placement.')
    nominal=PICK
    if k<=140:target+=min(1.,k/60)*(self.pick-nominal)
    else:
     lift=self.pick+[-.04,0,.01];above=FRONT+[-.04,-RING_RADIUS,0];seat=FRONT+[-.005,-RING_RADIUS,0]
     if k<=200:target=self.pick+ik.smoothstep((k-140)/60)*(lift-self.pick)
     elif k<=280:target=lift+ik.smoothstep((k-200)/80)*(above-lift)
     elif k<=340:target=above+ik.smoothstep((k-280)/60)*(seat-above)
     elif k<=480:target=seat
     # Later targets follow the authored quarter-turn guide and withdrawal.
     # The full function check starts only after this hand has let go.
   seed=np.clip(observed[o:o+6],ik.LOWER+1e-6,ik.UPPER-1e-6)
   p0,R0=ik.tcp_pose(seed,station.BASES[side]);bias=hands[side]['tcp']-p0;rbias=hands[side]['rotation']@R0.T
   def residual(q):
    pp,rr=ik.tcp_pose(q,station.BASES[side]);return np.r_[pp+bias-target,.08*ik._rot_error(R,rbias@rr),.001*(q-seed)]
   out[o:o+6]=least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=25).x
  return out
