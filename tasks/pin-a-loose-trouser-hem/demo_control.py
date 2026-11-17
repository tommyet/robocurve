"""Pinch a fold and guide the straight needle through both sides using robot joints."""
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
   self.start=tip.copy();self.initial_axis=axis.copy();choices=[];direction=np.array([-1.,0,0])
   names=[n for n in m.names if n.startswith(('front_','hem_','back_'))]
   apex=max(m.p(n)[2] for n in names if n.startswith('hem_'))
   for y in np.linspace(.109,.119,11):
    for z in np.arange(.776,min(.805,apex-.003),.001):
     hits=[]
     for n in names:
      R=m.orientation(n);normal=R[:,2]
      if abs(normal@direction)<.25:continue
      origin=np.array([.4,y,z]);distance=float(normal@(m.p(n)-origin)/(normal@direction));point=origin+distance*direction;local=R.T@(point-m.p(n))
      half_y=.005 if n.startswith('hem_') else .012
      if abs(local[0])<.004 and abs(local[1])<half_y-.001:hits.append((n,point))
     front=[h for h in hits if h[0].startswith('front_')];hem=[h for h in hits if h[0].startswith('hem_')]
     if len(front)==2 and len(hem)==2 and len(hits)==4:
      xs=[v[1][0] for v in hits];span=max(xs)-min(xs)
      if .008<span<.034:choices.append((span,y,z,min(xs),max(xs),[n for n,_ in hits]))
   if not choices:raise RuntimeError('The held hem does not present a clear four-layer needle path; stop this development trial.')
   span,y,z,lo,hi,names=max(choices,key=lambda c:c[0]);self.entry=np.array([hi+.025,y,z]);self.end=np.array([lo-.003,y,z])
   m.events.append(dict(event='demo_selected_straight_pin_path',start=self.entry.tolist(),end=self.end.tolist(),patches=names,time=m.time))
  def blend(a,b,start,end):
   u=np.clip((k-start)/(end-start),0,1);u=u*u*(3-2*u);return a*(1-u)+b*u
  if k<=340:goal=blend(self.start,self.entry+[0,0,.04],220,340);goalaxis=blend(self.initial_axis,np.array([-1.,0,0]),220,340)
  elif k<=400:goal=blend(self.entry+[0,0,.04],self.entry,340,400);goalaxis=np.array([-1.,0,0])
  elif k<=640:goal=blend(self.entry,self.end,400,640);goalaxis=np.array([-1.,0,0])
  else:goal=self.end;goalaxis=np.array([-1.,0,0])
  goalaxis/=np.linalg.norm(goalaxis);relative_tip=h['rotation'].T@(tip-h['tcp']);relative_axis=h['rotation'].T@axis
  seed=np.clip(current[7:13],ik.LOWER+1e-6,ik.UPPER-1e-6)
  def residual(q):
   pp,R=ik.tcp_pose(q,station.BASES['right']);return np.r_[pp+R@relative_tip-goal,.04*(R@relative_axis-goalaxis),.001*(q-seed)]
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
