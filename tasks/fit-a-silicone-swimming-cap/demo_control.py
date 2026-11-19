"""Track the settled cap for pickup using robot commands only."""
import numpy as np
from scipy.optimize import least_squares
class DemoControl:
 def __init__(self):self.offset=None;self.grip_offset=None;self.radial={"left":0.,"right":0.}
 def action(self,k,wanted,m,observed,hands):
  if 90<=k<=380 and set(m.grasp_state)!={'left','right'}:raise RuntimeError('Scripted demonstration lost a required grip; stop this diagnostic before further motion.')
  if 380<k<=460 and 'right' not in m.grasp_state:raise RuntimeError('Front grip lost before the back hand cleared.')
  from yam_arena import ik,station
  from geometry import POINTS,RIM,M
  if self.offset is None:self.offset={s:m.nodes[i]-POINTS[i] for s,i in [('left',RIM[M//4]),('right',RIM[3*M//4])]}
  if k==20:
   self.grip_offset={}
   for side,o,node in [('left',0,RIM[M//4]),('right',7,RIM[3*M//4])]:
    _,R=ik.tcp_pose(wanted[o:o+6],station.BASES[side])
    self.grip_offset[side]=m.nodes[node]-POINTS[node]
  out=wanted.copy()
  for side,o in [('left',0),('right',7)]:
   target,R=ik.tcp_pose(wanted[o:o+6],station.BASES[side])
   offset=self.offset[side]
   if self.grip_offset is not None:
    w=float(np.clip((k-20)/20,0,1));offset=(1-w)*offset+w*self.grip_offset[side]
   target+=min(1.,k/20)*max(0.,min(1.,(160-k)/80))*offset
   # Bounded centring along the closing axis; never chase vertical rim
   # motion. Keep this offset after capture and fade it during the lift.
   if 20<=k<=80 and side not in m.grasp_state:
    node=RIM[M//4 if side=='left' else 3*M//4]
    error=float((m.nodes[node]-hands[side]['tcp'])@hands[side]['rotation'][:,0])
    self.radial[side]=float(np.clip(self.radial[side]+np.clip(.4*error,-.0008,.0008),-.025,.025))
   target+=R[:,0]*self.radial[side]*max(0.,min(1.,(160-k)/80))
   seed=np.clip(observed[o:o+6],ik.LOWER+1e-6,ik.UPPER-1e-6)
   p0,R0=ik.tcp_pose(seed,station.BASES[side]);bias=hands[side]['tcp']-p0;rbias=hands[side]['rotation']@R0.T
   def residual(q):
    pp,rr=ik.tcp_pose(q,station.BASES[side]);return np.r_[pp+bias-target,.10*ik._rot_error(R,rbias@rr),.001*(q-seed)]
   out[o:o+6]=least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=25).x
  return out
