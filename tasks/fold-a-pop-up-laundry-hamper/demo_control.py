"""Correct the planned seam approach for passive settling, using robot joints."""
import numpy as np
from scipy.optimize import least_squares
from geometry import BODIES,GRIP_ENDS

class DemoControl:
 def __init__(self):self.offset=None
 def action(self,k,wanted,m,observed):
  from yam_arena import ik,station
  if self.offset is None:
   self.offset={}
   for side,i in [('left',GRIP_ENDS[0]),('right',GRIP_ENDS[1])]:
    names=[f'wire_{f}_{i:02d}' for f in range(4)]
    expected=np.mean([b['pos'] for b in BODIES if b['name'] in names],axis=0)
    self.offset[side]=np.mean([m.p(n) for n in names],axis=0)-expected
  out=wanted.copy()
  for side,o in [('left',0),('right',7)]:
   p,R=ik.tcp_pose(wanted[o:o+6],station.BASES[side]);planned=p.copy()
   offset_weight=min(1.,k/60)*np.clip((200-k)/60,0,1) if k>140 else min(1.,k/60)
   p+=offset_weight*self.offset[side]
   if 60<k<=100:
    index=GRIP_ENDS[0] if side=='left' else GRIP_ENDS[1]
    point=np.mean([m.p(f'wire_{f}_{index:02d}') for f in range(4)],axis=0)
    target=point-.006*R[:,2];u=np.clip((k-60)/40,0,1);p=(1-u)*p+u*target
    if k==100:self.offset[side]=target-planned
   if 100<k<=140:
    index=GRIP_ENDS[0] if side=='left' else GRIP_ENDS[1]
    point=np.mean([m.p(f'wire_{f}_{index:02d}') for f in range(4)],axis=0)
    # Balance the thin stack between the ordinary closing pads without
    # chasing it along the fingertip's approach direction.
    p+=R[:,0]*float((point-p)@R[:,0])
    if k==140:self.offset[side]=p-planned
   seed=np.clip(observed[o:o+6],ik.LOWER+1e-6,ik.UPPER-1e-6)
   def residual(q):
    pp,rr=ik.tcp_pose(q,station.BASES[side]);return np.r_[pp-p,(.05 if k<=140 else .15)*ik._rot_error(R,rr),.001*(q-seed)]
   out[o:o+6]=least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=30).x
   if k>100:out[o+6]=max(0.,observed[o+6]-.010)
  return out
