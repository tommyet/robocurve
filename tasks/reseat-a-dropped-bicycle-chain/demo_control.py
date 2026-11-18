"""Read-only object feedback for robot joint commands; no object actuation."""
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
class DemoControl:
 def __init__(self):self.offset=None;self.pick_offset=None;self.crank_angle=0.;self.pick_world=None
 def action(self,k,wanted,m,observed,hands):
  from yam_arena import ik,station
  from geometry import FRONT,POINTS,LINKS,R as RING_RADIUS
  if self.offset is None:self.offset=m.p('bicycle_frame')-FRONT
  if k<=140:
   v=m.orientation('chainring')[:,1];self.crank_angle=float(np.arctan2(-v[0],v[1]))
   i=int(np.argmin(POINTS[:,1]));nominal=(POINTS[i]+POINTS[(i+1)%len(POINTS)])/2
   links=np.array([m.p(f'link_{i:03d}') for i in range(LINKS)]);self.pick_world=links[int(np.argmin(links[:,1]))].copy();self.pick_offset=self.pick_world-nominal
  out=wanted.copy();u=min(1.,k/60)
  for side,o in [('left',0),('right',7)]:
   target,R=ik.tcp_pose(wanted[o:o+6],station.BASES[side])
   if side=='left':
    turn=Rotation.from_euler('z',self.crank_angle*u).as_matrix();target=FRONT+turn@(target-FRONT)+u*self.offset;R=turn@R
   else:
    if k<=140:target+=u*self.pick_offset
    else:
     frame=FRONT+self.offset;start=self.pick_world+np.array([0,0,.010]);clear=start+np.array([0,0,.040]);above=frame+np.array([0,-RING_RADIUS,.060]);seat=frame+np.array([0,-RING_RADIUS,.013])
     if k<=200:target=start+ik.smoothstep((k-140)/60)*(clear-start)
     elif k<=260:target=clear+ik.smoothstep((k-200)/60)*(above-clear)
     elif k<=320:target=above+ik.smoothstep((k-260)/60)*(seat-above)
     elif k<=340:target=seat
     elif k<=380:target=seat+ik.smoothstep((k-340)/40)*np.array([0,-.08,.08])
     else:target=seat+np.array([0,-.08,.08])
   seed=np.clip(observed[o:o+6],ik.LOWER+1e-6,ik.UPPER-1e-6)
   p0,R0=ik.tcp_pose(seed,station.BASES[side]);bias=hands[side]['tcp']-p0;rbias=hands[side]['rotation']@R0.T
   def residual(q):
    pp,rr=ik.tcp_pose(q,station.BASES[side]);return np.r_[pp+bias-target,.08*ik._rot_error(R,rbias@rr),.001*(q-seed)]
   out[o:o+6]=least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=25).x
  return out
