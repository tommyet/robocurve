"""Native pose feedback used only to command the two robot arms."""
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot
class DemoControl:
 def __init__(self):self.pick_index=None;self.pick=None;self.angle=0.
 def action(self,k,wanted,m,observed,hands):
  from yam_arena import ik,station
  from geometry import FRONT,POINTS,LINKS,R as RING_RADIUS
  if k<=100:
   links=np.array([m.p(f'link_{i:03d}') for i in range(LINKS)])
   if self.pick_index is None:self.pick_index=int(np.argmin(links[:,2]))
   self.pick=links[self.pick_index].copy()+[-.005,0,0]
   v=m.orientation('chainring')[:,1];self.angle=float(np.arctan2(v[2],v[1]))
  out=wanted.copy()
  for side,o in [('left',0),('right',7)]:
   target,R=ik.tcp_pose(wanted[o:o+6],station.BASES[side])
   if side=='right':
    turn=Rot.from_euler('x',self.angle*min(1.,k/60)).as_matrix();target=FRONT+turn@(target-FRONT);R=turn@R
   else:
    i=int(np.argmin(POINTS[:,2]));nominal=(POINTS[i]+POINTS[(i+1)%LINKS])/2+[-.005,0,0]
    if k<=140:target+=min(1.,k/60)*(self.pick-nominal)
    else:
     lift=self.pick+[-.04,0,.03];above=FRONT+[-.06,-RING_RADIUS,0];seat=FRONT+[-.010,-RING_RADIUS,0]
     if k<=200:target=self.pick+ik.smoothstep((k-140)/60)*(lift-self.pick)
     elif k<=280:target=lift+ik.smoothstep((k-200)/80)*(above-lift)
     elif k<=340:target=above+ik.smoothstep((k-280)/60)*(seat-above)
     elif k<=360:target=seat
     elif k<=400:target=seat+ik.smoothstep((k-360)/40)*np.array([-.09,-.03,0])
     else:target=seat+[-.09,-.03,0]
   seed=np.clip(observed[o:o+6],ik.LOWER+1e-6,ik.UPPER-1e-6)
   p0,R0=ik.tcp_pose(seed,station.BASES[side]);bias=hands[side]['tcp']-p0;rbias=hands[side]['rotation']@R0.T
   def residual(q):
    pp,rr=ik.tcp_pose(q,station.BASES[side]);return np.r_[pp+bias-target,.08*ik._rot_error(R,rbias@rr),.001*(q-seed)]
   out[o:o+6]=least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=25).x
  return out
