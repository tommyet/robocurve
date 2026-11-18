"""Robot-only tracking correction; never changes task objects."""
import numpy as np
from scipy.optimize import least_squares
class DemoControl:
 def __init__(self):self.offset=None;self.closing_offset=None
 def action(self,k,wanted,m,observed,hands):
  from yam_arena import ik,station
  if self.offset is None:
    from geometry import POINTS,RIM,M
    self.offset={s:m.nodes[i]-POINTS[i] for s,i in [('left',RIM[M//4]),('right',RIM[3*M//4])]}
  if k>=240 and self.closing_offset is None:
   from geometry import POINTS,RIM,M
   self.closing_offset={s:m.nodes[i]-POINTS[i] for s,i in [('left',RIM[M//4]),('right',RIM[3*M//4])]}
  out=wanted.copy()
  for side,o in [('left',0),('right',7)]:
   target,R=ik.tcp_pose(wanted[o:o+6],station.BASES[side])
   offset=self.offset[side]
   if self.closing_offset is not None:
    offset=self.closing_offset[side]
   if 200<=k<240:
    from geometry import RIM,M
    target=m.nodes[RIM[M//4 if side=='left' else 3*M//4]].copy()
   else:target+=min(1.,k/60)*(1.-float(np.clip((k-360)/80,0,1)))*offset
   seed=np.clip(observed[o:o+6],ik.LOWER+1e-6,ik.UPPER-1e-6)
   p0,R0=ik.tcp_pose(seed,station.BASES[side]);bias=hands[side]['tcp']-p0;rbias=hands[side]['rotation']@R0.T
   def residual(q):
    pp,rr=ik.tcp_pose(q,station.BASES[side]);return np.r_[pp+bias-target,.08*ik._rot_error(R,rbias@rr),.001*(q-seed)]
   out[o:o+6]=least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=25).x
  return out
