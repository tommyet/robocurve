"""Observe the hanging pull tab and guide ordinary robot joints into a grasp."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from geometry import TABLE
class DemoControl:
 def __init__(self):self.choice=None;self.start=None;self.startR=None;self.contact=None;self.graspR=None;self.nominal=None
 def action(self,k,wanted,stage,m,observed):
  if k<=240:return wanted
  from yam_arena import ik,station
  point=m.p('cup_tab_8',[0,.006,0]);tabR=m.orientation('cup_tab_8')
  seed=np.clip(observed[7:13],ik.LOWER+1e-6,ik.UPPER-1e-6)
  if self.choice is None:
   self.start,self.startR=ik.tcp_pose(seed,station.BASES['right']);candidates=[]
   for tangent in [0,1]:
    for zs in [-1,1]:
     for xs in [-1,1]:
      X=xs*tabR[:,2];Z=zs*tabR[:,tangent];R=np.column_stack([X,np.cross(Z,X),Z]);target=point-.006*Z
      if (target-.134*Z)[2]<TABLE+.06:continue
      def end_error(q):
       p,rr=ik.tcp_pose(q,station.BASES['right']);return np.r_[p-target,.15*ik._rot_error(R,rr)]
      sol=least_squares(end_error,seed,bounds=(ik.LOWER,ik.UPPER),max_nfev=120)
      error=np.linalg.norm(sol.fun)
      if error<.01:candidates.append((np.linalg.norm(sol.x-seed),(tangent,zs,xs)))
   if not candidates:raise RuntimeError('No reachable native tab grasp; stop this development trial.')
   self.choice=min(candidates,key=lambda v:v[0])[1]
   frame=json.loads(Path(__file__).with_name('demo-plan.json').read_text())['frames'][279]['action14'];self.nominal=ik.tcp_pose(np.asarray(frame)[7:13],station.BASES['right'])[0]
  if k<=300:
   tangent,zs,xs=self.choice;X=xs*tabR[:,2];Z=zs*tabR[:,tangent];self.graspR=np.column_stack([X,np.cross(Z,X),Z]);self.contact=point-.006*Z
  def smooth(u):u=np.clip(u,0,1);return u*u*(3-2*u)
  if k<=260:
   u=smooth((k-240)/20);target=(1-u)*self.start+u*(self.contact-.04*self.graspR[:,2]);R=ik.slerp_matrix(self.startR,self.graspR,u)
  elif k<=280:
   u=smooth((k-260)/20);target=self.contact-(1-u)*.04*self.graspR[:,2];R=self.graspR
  elif k<=300:target=self.contact;R=self.graspR
  else:
   p,_=ik.tcp_pose(wanted[7:13],station.BASES['right']);target=self.contact+p-self.nominal;R=self.graspR
  def residual(q):
   p,rr=ik.tcp_pose(q,station.BASES['right']);return np.r_[p-target,.12*ik._rot_error(R,rr),.001*(q-seed)]
  out=wanted.copy();out[7:13]=least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=40).x;return out
