"""Pinch a fold and guide the straight needle through both sides using robot joints."""
import numpy as np
from scipy.optimize import least_squares
class DemoControl:
 def __init__(self):self.start=None;self.closure=None;self.last_q=None;self.released_at=None;self.left_offset=None
 def action(self,k,wanted,m,hands,current):
  from yam_arena import ik,station
  from geometry import BODIES
  if self.left_offset is None:
   names=['hem_8_0','hem_9_0'];nominal=np.mean([b['pos'] for b in BODIES if b['name'] in names],axis=0)
   self.left_offset=np.mean([m.p(n) for n in names],axis=0)-nominal
  if k<=700:
   pp,RR=ik.tcp_pose(wanted[:6],station.BASES['left']);target=pp+self.left_offset*min(1.,k/60)
   if 60<k<=120:
    names=['front_8_0','front_9_0','hem_8_0','hem_9_0']
    centre=np.mean([m.p(n) for n in names],axis=0)
    grasp=centre-.006*RR[:,2];u=np.clip((k-60)/40,0,1)
    target=(1-u)*target+u*grasp
    if k==120:self.left_offset=grasp-pp
   seed=np.clip(current[:6],ik.LOWER+1e-6,ik.UPPER-1e-6)
   def correct(q):
    p,R=ik.tcp_pose(q,station.BASES['left']);return np.r_[p-target,.12*ik._rot_error(RR,R),.001*(q-seed)]
   wanted=wanted.copy();wanted[:6]=least_squares(correct,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=30).x
  if k<=220:return wanted
  if k>700:return self.close(k,wanted,m,hands,current)
  h=hands['right'];tip=m.p('needle_point',[.001,0,0]);axis=m.orientation('pin_arm')[:,0]
  if np.linalg.norm(m.p('pin_frame')-h['tcp'])>.055:raise RuntimeError('The pin slipped from the native grip; stop this failed development trial.')
  if self.start is None:
   from path_search import select_path
   self.start=tip.copy();self.initial_axis=axis.copy()
   self.entry,self.end,self.direction,names=select_path(m)
   m.events.append(dict(event='demo_selected_straight_pin_path',start=self.entry.tolist(),end=self.end.tolist(),patches=names,time=m.time))
   # Select a reachable wrist branch before descending to the cloth. A local
   # incremental solve can otherwise stop at the wrist's negative limit.
   from yam_arena.constants import READY
   self.approach_start=np.asarray(current[7:13]).copy()
   relative_tip=h['rotation'].T@(tip-h['tcp']);relative_axis=h['rotation'].T@axis
   target=self.entry+[0,0,.04]
   def approach_error(q):
    pp,RR=ik.tcp_pose(q,station.BASES['right']);return np.r_[pp+RR@relative_tip-target,.1*(RR@relative_axis-self.direction)]
   solutions=[least_squares(approach_error,seed,bounds=(ik.LOWER,ik.UPPER),max_nfev=180) for seed in [np.asarray(READY),(ik.LOWER+ik.UPPER)/2]]
   solution=min(solutions,key=lambda x:np.linalg.norm(x.fun))
   if np.linalg.norm(solution.fun)>.005:raise RuntimeError('No reachable needle approach for the observed grasp.')
   self.approach_q=solution.x
   m.events.append(dict(event='demo_reachable_needle_approach',residual=float(np.linalg.norm(solution.fun)),time=m.time))
  if k<=340:
   u=np.clip((k-220)/120,0,1);u=u*u*(3-2*u);out=wanted.copy();out[7:13]=(1-u)*self.approach_start+u*self.approach_q;self.last_q=out[7:13].copy();return out
  def blend(a,b,start,end):
   u=np.clip((k-start)/(end-start),0,1);u=u*u*(3-2*u);return a*(1-u)+b*u
  if k<=340:goal=blend(self.start,self.entry+[0,0,.04],220,340);goalaxis=blend(self.initial_axis,self.direction,220,340)
  elif k<=400:goal=blend(self.entry+[0,0,.04],self.entry,340,400);goalaxis=self.direction.copy()
  elif k<=640:goal=blend(self.entry,self.end,400,640);goalaxis=self.direction.copy()
  else:goal=self.end;goalaxis=self.direction.copy()
  goalaxis/=np.linalg.norm(goalaxis);relative_tip=h['rotation'].T@(tip-h['tcp']);relative_axis=h['rotation'].T@axis
  seed=np.clip(current[7:13],ik.LOWER+1e-6,ik.UPPER-1e-6)
  def residual(q):
   pp,R=ik.tcp_pose(q,station.BASES['right']);return np.r_[pp+R@relative_tip-goal,.1*(R@relative_axis-goalaxis),.001*(q-seed)]
  sol=least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=30)
  out=wanted.copy();out[7:13]=sol.x;self.last_q=sol.x.copy();return out

 def close(self,k,wanted,m,hands,current):
  from yam_arena import ik,station
  from scipy.spatial.transform import Rotation
  if self.closure is None:
   if not m.measure()['both_layers_held']:raise RuntimeError('Threading incomplete; stop the development demo before attempting closure.')
   tip=m.p('needle_point',[.001,0,0]);shield=m.p('pin_frame',[.045,0,.002]);z=shield-tip;z/=np.linalg.norm(z)
   x=np.cross(m.orientation('pin_arm')[:,0],z);x/=np.linalg.norm(x);R=np.column_stack([x,np.cross(z,x),z])
   self.closure=dict(tip=tip,shield=shield,R=R,left=hands['left']['tcp'].copy(),leftR=hands['left']['rotation'].copy(),right=hands['right']['tcp'].copy(),rightR=hands['right']['rotation'].copy())
  c=self.closure;R=c['R'];z=R[:,2];near=c['tip']-.030*z+.006*R[:,0];pressed=c['shield']-.006*z+.006*R[:,0]
  def mix(a,b,start,end):
   u=np.clip((k-start)/(end-start),0,1);u=u*u*(3-2*u);return a*(1-u)+b*u
  def solve(side,p,targetR):
   o=0 if side=='left' else 7;seed=np.clip(current[o:o+6],ik.LOWER+1e-6,ik.UPPER-1e-6)
   def residual(q):
    pp,rr=ik.tcp_pose(q,station.BASES[side]);return np.r_[pp-p,.12*ik._rot_error(targetR,rr),.001*(q-seed)]
   return least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=40).x
  out=wanted.copy();out[7:13]=self.last_q;out[13]=0.
  if k<=740:p=c['left'];targetR=c['leftR'];grip=.7
  elif k<=800:p=mix(c['left'],c['left']+[0,0,.08],740,800);targetR=c['leftR'];grip=.7
  elif k<=880:
   p=mix(c['left']+[0,0,.08],near,800,880);targetR=ik.slerp_matrix(c['leftR'],R,np.clip((k-800)/80,0,1));grip=0.
  else:p=mix(near,pressed,880,1000);targetR=R;grip=0.
  if m.latched and self.released_at is None:self.released_at=k
  if self.released_at is not None or k>1080:
   start=self.released_at or 1080;u=np.clip((k-start)/60,0,1);p=pressed-u*.09*z;targetR=R;grip=.7
   out[7:13]=solve('right',c['right']+[0,-.06*u,.09*u],c['rightR']);out[13]=.7
  out[:6]=solve('left',p,targetR);out[6]=grip;return out
