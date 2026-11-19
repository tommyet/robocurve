"""Track the observed rigid tip through ordinary robot joint targets."""
import numpy as np
from scipy.optimize import least_squares
class DemoControl:
 def __init__(self):self.grasp=None;self.grasp_rotation=None;self.correction=np.zeros(3)
 def action(self,k,wanted,m,hands,observed):
  if k==220:
   from geometry import REST
   if m.p('extension')[2]<REST[2]+.02:raise RuntimeError('The extension was not lifted; stop this diagnostic.')
  if 220<=k<=1720:
   h=hands['right'];rel=h['rotation'].T@(m.p('extension')-h['tcp'])
   if self.grasp is None:self.grasp=rel.copy();self.grasp_rotation=h['rotation'].T@m.orientation('extension')
   elif np.linalg.norm(rel-self.grasp)>.008:raise RuntimeError('Extension slipped from the physical grip; stop diagnostic.')
  if k<160:return wanted
  from yam_arena import ik,station
  h=hands['right'];R0=np.array([[0,0,-1],[1,0,0],[0,-1,0.]])
  p,R=ik.tcp_pose(wanted[7:13],station.BASES['right'])
  if wanted[13]>.2:return wanted
  # The plan's TCP is 3 mm above the tip origin. Preserve that tool relation,
  # correcting only for observed slip, not moving the object itself.
  desired_R=R@R0.T;goal=p-desired_R@np.array([0,0,.003])
  # Visual servoing uses the current measured tool transform. The compliant
  # pinch may move under seating load; its initial transform is not a weld.
  relative=h['rotation'].T@(m.p('extension')-h['tcp'])
  relative_R=h['rotation'].T@m.orientation('extension')
  seed=np.clip(observed[7:13],ik.LOWER+1e-6,ik.UPPER-1e-6)
  p0,r0=ik.tcp_pose(seed,station.BASES['right']);bias=h['tcp']-p0;rbias=h['rotation']@r0.T
  def f(q):
   pp,rr=ik.tcp_pose(q,station.BASES['right']);rr=rbias@rr
   return np.r_[pp+bias+rr@relative-goal,.10*ik._rot_error(desired_R,rr@relative_R),.001*(q-seed)]
  out=wanted.copy();out[7:13]=least_squares(f,seed,bounds=(np.maximum(ik.LOWER,seed-.10),np.minimum(ik.UPPER,seed+.10)),max_nfev=25).x;return out
