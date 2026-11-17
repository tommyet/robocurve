"""Contact-driven needle-path candidate; privileged poses guide ordinary joints."""
import numpy as np
from scipy.optimize import least_squares
class DemoControl:
 def __init__(self):self.start=None
 def action(self,k,wanted,m,hands,current):
  if k<=220:return wanted
  from yam_arena import ik,station
  h=hands['right'];tip=m.p('needle_point',[.001,0,0]);axis=m.orientation('pin_arm')[:,0]
  if self.start is None:
   self.start=tip.copy();self.initial_axis=axis.copy()
   self.entry=(m.p('hem_8_0')+m.p('front_8_0',[0,.006,0]))/2
   self.end=(m.p('hem_9_0')+m.p('front_9_0',[0,.006,0]))/2
   self.normal=m.orientation('hem_8_0')[:,2]+m.orientation('front_8_0')[:,2];self.normal/=np.linalg.norm(self.normal)
   self.tangent=self.end-self.entry;self.tangent-=self.normal*np.dot(self.tangent,self.normal);self.tangent/=np.linalg.norm(self.tangent)
  def blend(a,b,start,end):
   u=np.clip((k-start)/(end-start),0,1);u=u*u*(3-2*u);return a*(1-u)+b*u
  n,t=self.normal,self.tangent
  down=np.cos(np.radians(25))*t-np.sin(np.radians(25))*n;up=np.cos(np.radians(25))*t+np.sin(np.radians(25))*n
  if k<=340:goal=blend(self.start,self.entry+.030*n,220,340);goalaxis=blend(self.initial_axis,down,220,340)
  elif k<=400:goal=blend(self.entry+.030*n,self.entry+.002*n,340,400);goalaxis=down
  elif k<=480:goal=blend(self.entry+.002*n,self.entry+.003*t-.003*n,400,480);goalaxis=down
  elif k<=540:goal=blend(self.entry+.003*t-.003*n,(self.entry+self.end)/2-.003*n,480,540);goalaxis=blend(down,t,480,540)
  elif k<=620:goal=blend((self.entry+self.end)/2-.003*n,self.end+.003*n,540,620);goalaxis=blend(t,up,540,620)
  else:goal=self.end+.003*n;goalaxis=up
  goalaxis/=np.linalg.norm(goalaxis)
  relative_tip=h['rotation'].T@(tip-h['tcp']);relative_axis=h['rotation'].T@axis
  # Free rotation around the needle avoids imposing an unnecessary wrist angle.
  delta=goal-tip;delta*=min(1.,.002/max(np.linalg.norm(delta),1e-12));target=tip+delta
  desired=axis+.10*(goalaxis-axis);desired/=np.linalg.norm(desired)
  seed=current[7:13]
  def residual(q):
   p,R=ik.tcp_pose(q,station.BASES['right']);return np.r_[p+R@relative_tip-target,.06*(R@relative_axis-desired),.0002*(q-seed)]
  sol=least_squares(residual,seed,bounds=(ik.LOWER,ik.UPPER),max_nfev=25)
  out=wanted.copy();out[7:13]=sol.x;return out
