"""Contact-driven needle-path candidate; privileged poses guide ordinary joints."""
import numpy as np
from scipy.optimize import least_squares
class DemoControl:
 def __init__(self):self.start=None;self.closure=None;self.last_q=None;self.released_at=None
 def action(self,k,wanted,m,hands,current):
  if k<=220:return wanted
  from yam_arena import ik,station
  if k>700:return self.close(k,wanted,m,hands,current)
  h=hands['right'];tip=m.p('needle_point',[.001,0,0]);axis=m.orientation('pin_arm')[:,0]
  if self.start is None:
   self.start=tip.copy();self.initial_axis=axis.copy()
   self.entry=(m.p('hem_9_0',[0,0,0])+m.p('front_9_0',[0,.007,0]))/2
   self.end=(m.p('hem_8_0',[0,0,0])+m.p('front_8_0',[0,.007,0]))/2
   self.normal=m.orientation('hem_9_0')[:,2]+m.orientation('front_9_0')[:,2];self.normal/=np.linalg.norm(self.normal)
   self.tangent=self.end-self.entry;self.tangent-=self.normal*np.dot(self.tangent,self.normal);self.tangent/=np.linalg.norm(self.tangent)
  def blend(a,b,start,end):
   u=np.clip((k-start)/(end-start),0,1);u=u*u*(3-2*u);return a*(1-u)+b*u
  n,t=self.normal,self.tangent
  down=np.cos(np.radians(45))*t-np.sin(np.radians(45))*n;up=np.cos(np.radians(45))*t+np.sin(np.radians(45))*n
  if k<=340:goal=blend(self.start,self.entry+.030*n,220,340);goalaxis=blend(self.initial_axis,down,220,340)
  elif k<=400:goal=blend(self.entry+.030*n,self.entry+.002*n,340,400);goalaxis=down
  elif k<=480:goal=blend(self.entry+.002*n,self.entry+.002*t-.010*n,400,480);goalaxis=down
  elif k<=540:goal=blend(self.entry+.002*t-.010*n,(self.entry+self.end)/2-.003*n,480,540);goalaxis=blend(down,t,480,540)
  elif k<=620:goal=blend((self.entry+self.end)/2-.003*n,self.end+.003*n,540,620);goalaxis=blend(t,up,540,620)
  else:goal=self.end+.003*n;goalaxis=up
  goalaxis/=np.linalg.norm(goalaxis)
  relative_tip=h['rotation'].T@(tip-h['tcp']);relative_axis=h['rotation'].T@axis
  # Free rotation around the needle avoids imposing an unnecessary wrist angle.
  target=goal
  desired=goalaxis
  seed=np.clip(current[7:13],ik.LOWER+1e-6,ik.UPPER-1e-6)
  def residual(q):
   p,R=ik.tcp_pose(q,station.BASES['right']);return np.r_[p+R@relative_tip-target,.04*(R@relative_axis-desired),.001*(q-seed)]
  sol=least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=25)
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
  out=wanted.copy();out[7:13]=self.last_q;out[13]=.04
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
