"""Track the settled cap for pickup using robot commands only."""
import numpy as np
from scipy.optimize import least_squares
class DemoControl:
 def __init__(self):self.offset=None;self.grip_offset=None
 def action(self,k,wanted,m,observed,hands):
  if 190<=k<=480 and set(m.grasp_state)!={'left','right'}:raise RuntimeError('Scripted demonstration lost a required grip; stop this diagnostic before further motion.')
  from yam_arena import ik,station
  from geometry import POINTS,RIM,M
  if self.offset is None:self.offset={s:m.nodes[i]-POINTS[i] for s,i in [('left',RIM[M//4]),('right',RIM[3*M//4])]}
  if k==180:
   self.grip_offset={}
   for side,o in [('left',0),('right',7)]:
    target,_=ik.tcp_pose(wanted[o:o+6],station.BASES[side]);self.grip_offset[side]=hands[side]['tcp']-target
  out=wanted.copy()
  for side,o in [('left',0),('right',7)]:
   target,R=ik.tcp_pose(wanted[o:o+6],station.BASES[side])
   offset=self.offset[side]
   if self.grip_offset is not None:
    w=float(np.clip((k-180)/20,0,1));offset=(1-w)*offset+w*self.grip_offset[side]
   target+=min(1.,k/60)*max(0.,min(1.,(260-k)/80))*offset
   if 100<=k<=180 and side not in m.grasp_state:
    node=RIM[M//4 if side=='left' else 3*M//4]
    # Observe the current rim while inserting, then close around it. The
    # fingertip passes 10 mm beyond the edge; only robot joints are commanded.
    aim=m.nodes[node]+R@np.array([0.,0.,.010])+np.array([0.,0.,-.010*float(np.clip((140-k)/20,0,1))])
    blend=float(np.clip((k-100)/20,0,1));target=(1-blend)*target+blend*aim
   seed=np.clip(observed[o:o+6],ik.LOWER+1e-6,ik.UPPER-1e-6)
   p0,R0=ik.tcp_pose(seed,station.BASES[side]);bias=hands[side]['tcp']-p0;rbias=hands[side]['rotation']@R0.T
   def residual(q):
    pp,rr=ik.tcp_pose(q,station.BASES[side]);return np.r_[pp+bias-target,.10*ik._rot_error(R,rbias@rr),.001*(q-seed)]
   out[o:o+6]=least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=25).x
  return out
