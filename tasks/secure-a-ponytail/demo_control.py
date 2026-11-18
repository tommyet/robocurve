"""Robot-only tracking correction; never changes task objects."""
import numpy as np
from scipy.optimize import least_squares
class DemoControl:
 def __init__(self):self.offset=None;self.hair_x=None
 def action(self,k,wanted,m,observed,hands):
  from yam_arena import ik,station
  if self.offset is None:
    from geometry import POINTS,M
    self.offset={s:m.nodes[i]-POINTS[i] for s,i in [('left',M+M//4),('right',M+3*M//4)]}
  out=wanted.copy()
  for side,o in [('left',0),('right',7)]:
   target,R=ik.tcp_pose(wanted[o:o+6],station.BASES[side])
   # The pickup follows the settled band. Fade that correction before
   # reaching the hair so its world height is not lowered by band sag.
   weight=min(1.,k/60)*max(0.,min(1.,(300-k)/80))
   target+=weight*self.offset[side]
   if k>=220:
    from geometry import STRANDS,SEGMENTS
    if k<=440 or self.hair_x is None:
     centres=[]
     for strand in range(STRANDS):
      p=np.array([m.p(f'hair_{strand}_{i}') for i in range(SEGMENTS)])
      centres.append(p[np.argmin(abs(p[:,2]-target[2])),0])
     self.hair_x=float(np.clip(np.median(centres),.27,.33))
    target[0]+=min(1.,(k-220)/80)*(self.hair_x-.300)
   seed=np.clip(observed[o:o+6],ik.LOWER+1e-6,ik.UPPER-1e-6)
   p0,R0=ik.tcp_pose(seed,station.BASES[side]);bias=hands[side]['tcp']-p0;rbias=hands[side]['rotation']@R0.T
   def residual(q):
    pp,rr=ik.tcp_pose(q,station.BASES[side]);return np.r_[pp+bias-target,.10*ik._rot_error(R,rbias@rr),.001*(q-seed)]
   out[o:o+6]=least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=25).x
  return out
