"""Correct the planned seam approach for passive settling, using robot joints."""
import numpy as np
from scipy.optimize import least_squares
from geometry import BODIES

class DemoControl:
 def __init__(self):self.offset=None
 def action(self,k,wanted,m,observed):
  from yam_arena import ik,station
  if self.offset is None:
   self.offset={}
   for side,i in [('left',0),('right',24)]:
    names=[f'wire_{f}_{i:02d}' for f in range(4)]
    expected=np.mean([b['pos'] for b in BODIES if b['name'] in names],axis=0)
    self.offset[side]=np.mean([m.p(n) for n in names],axis=0)-expected
  out=wanted.copy()
  for side,o in [('left',0),('right',7)]:
   p,R=ik.tcp_pose(wanted[o:o+6],station.BASES[side]);p+=min(1.,k/60)*self.offset[side]
   seed=np.clip(observed[o:o+6],ik.LOWER+1e-6,ik.UPPER-1e-6)
   def residual(q):
    pp,rr=ik.tcp_pose(q,station.BASES[side]);return np.r_[pp-p,.15*ik._rot_error(R,rr),.001*(q-seed)]
   out[o:o+6]=least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=30).x
  return out
