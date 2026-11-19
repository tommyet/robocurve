"""Robot-only feedback to the settled towel's two pickup points."""
import numpy as np
from scipy.optimize import least_squares
class DemoControl:
 def __init__(self):self.offset=None
 def action(self,k,wanted,m,observed,hands):
  from yam_arena import ik,station
  from geometry import POINTS,GRIP_IDS
  if self.offset is None:self.offset={s:m.nodes[i]-POINTS[i] for s,i in zip(['left','right'],GRIP_IDS)}
  if 280<k<1720 and set(m.grasp_state)!={'left','right'}:raise RuntimeError('Towel grip lost; stop diagnostic')
  if 140<=k<=280:
   for s,i in zip(['left','right'],GRIP_IDS):
    if s not in m.grasp_state:self.offset[s]+=np.clip(.35*(m.nodes[i]-POINTS[i]-self.offset[s]),-.002,.002)
  out=wanted.copy()
  for s,o in [('left',0),('right',7)]:
   target,R=ik.tcp_pose(wanted[o:o+6],station.BASES[s]);target+=self.offset[s]*max(0.,min(1.,(420-k)/80))
   seed=np.clip(observed[o:o+6],ik.LOWER+1e-6,ik.UPPER-1e-6);p0,R0=ik.tcp_pose(seed,station.BASES[s]);bias=hands[s]['tcp']-p0;rbias=hands[s]['rotation']@R0.T
   def residual(q):
    p,r=ik.tcp_pose(q,station.BASES[s]);return np.r_[p+bias-target,.1*ik._rot_error(R,rbias@r),.001*(q-seed)]
   out[o:o+6]=least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=25).x
  return out
