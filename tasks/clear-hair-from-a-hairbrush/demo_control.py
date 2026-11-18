"""Robot-only tracking correction; never changes task objects."""
import numpy as np
from scipy.optimize import least_squares
class DemoControl:
 def __init__(self):self.offset=None
 def action(self,k,wanted,m,observed,hands):
  from yam_arena import ik,station
  if self.offset is None:
    from geometry import BRUSH,TOOL
    self.offset={'left':m.p('brush')-BRUSH,'right':m.p('comb')-TOOL}
  if k<=140:
   from geometry import BRUSH
   self.offset['left']=m.p('brush')-BRUSH
  out=wanted.copy()
  for side,o in [('left',0),('right',7)]:
   target,R=ik.tcp_pose(wanted[o:o+6],station.BASES[side])
   offset=self.offset[side]
   if side=='right' and 180<k<=420:
    from geometry import BRUSH
    offset=m.p('brush')-(BRUSH+[0,0,.050])
   target+=min(1.,k/60)*offset
   seed=np.clip(observed[o:o+6],ik.LOWER+1e-6,ik.UPPER-1e-6)
   p0,R0=ik.tcp_pose(seed,station.BASES[side]);bias=hands[side]['tcp']-p0;rbias=hands[side]['rotation']@R0.T
   def residual(q):
    pp,rr=ik.tcp_pose(q,station.BASES[side]);return np.r_[pp+bias-target,.10*ik._rot_error(R,rbias@rr),.001*(q-seed)]
   out[o:o+6]=least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=25).x
  return out
