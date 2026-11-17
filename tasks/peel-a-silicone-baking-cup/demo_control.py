"""Locate the settled pull tab, then peel it with ordinary robot joints."""
import numpy as np
from scipy.optimize import least_squares
from geometry import C
class DemoControl:
 def __init__(self):self.offset=None;self.started=None
 def action(self,k,wanted,stage,m,observed):
  if k<=240:return wanted
  from yam_arena import ik,station
  if self.offset is None:
   # Fixed correction from the observed tab after pickup. The subsequent pull
   # is a hand trajectory, not a command to the tab or its material bonds.
   self.offset=m.p('cup_tab_8',[0,.006,0])-(C+np.array([0,-.048,.122]));self.started=k
  p,R=ik.tcp_pose(wanted[7:13],station.BASES['right'])
  u=np.clip((k-self.started+1)/40,0,1);u=u*u*(3-2*u);target=p+u*self.offset
  seed=np.clip(observed[7:13],ik.LOWER+1e-6,ik.UPPER-1e-6)
  def residual(q):
   pp,rr=ik.tcp_pose(q,station.BASES['right']);return np.r_[pp-target,.12*ik._rot_error(R,rr),.001*(q-seed)]
  out=wanted.copy();out[7:13]=least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=30).x;return out
