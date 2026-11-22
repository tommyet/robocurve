"""Passive native ribbons; no scripted folding, interlacing or position writes."""
import numpy as np
from native_model import NativeModel
from geometry import *
class Model(NativeModel):
 def __init__(self):
  super().__init__();self.grasp_state={};self.peak_gap=0.
 def configure_station(self):
  from pad_covers import install
  install()
 def bind_native(self,base):
  super().bind_native(base)
  from finite_pinch import FinitePinch
  self.pinch=FinitePinch(self,CELLS,WIDTH/2,.001,.003,(-.004,.004),force_limit=.8,torque_limit=.012)
 def update(self,hands,dt=.05):
  self.read();self.time+=dt;self.pinch.update(hands)
  self.peak_gap=max(self.peak_gap,max(float(np.linalg.norm(self.joint_gap(j['name']))) for j in JOINTS))
  self.failed |= self.integrity_failed()
  clear=all(h['opening']>.4 and min(np.linalg.norm(h['tcp']-self.p(n)) for n in CELLS+['pie'])>.05 for h in hands.values())
  self.release=self.release+dt if clear else 0.
 def integrity_failed(self):
  p=np.array([self.p(n) for n in CELLS]);lost=bool(np.any(p[:,2]<TABLE-.01) or np.any(p[:,0]<0) or np.any(p[:,0]>.8) or np.any(abs(p[:,1])>.4))
  return super().integrity_failed() or bool(self.broken) or self.peak_gap>.003 or lost or self.orientation('pie')[2,2]<np.cos(np.pi/6)
 def reset_valid(self):return not self.failed and self.measure()['woven_rows']==0
 def strip(self,s):return np.array([(self.p(n)-self.p('pie'))@self.orientation('pie') for n in STRIPS[s]])
 @staticmethod
 def crossing(a,b):
  # Require a real projected centre-line crossing, not mere proximity.
  p=a[:-1,None,:2];q=b[None,:-1,:2];r=np.diff(a[:,:2],axis=0)[:,None,:];s=np.diff(b[:,:2],axis=0)[None,:,:]
  cross=lambda x,y:x[...,0]*y[...,1]-x[...,1]*y[...,0]
  den=cross(r,s);safe=np.where(abs(den)>1e-12,den,np.nan);t=cross(q-p,s)/safe;u=cross(q-p,r)/safe
  ii,jj=np.where((t>=0)&(t<=1)&(u>=0)&(u<=1))
  if len(ii)==0:return None
  points=[];dz=[]
  for i,j in zip(ii,jj):
   aa=a[i]+t[i,j]*(a[i+1]-a[i]);bb=b[j]+u[i,j]*(b[j+1]-b[j]);points.append(aa[:2]);dz.append(aa[2]-bb[2])
  if np.max(np.linalg.norm(np.asarray(points)-points[0],axis=1))>.001:return None
  return np.mean(points,axis=0),float(np.mean(dz))
 def result(self):
  strips=[self.strip(s) for s in range(5)]
  strips=sorted(strips[:2],key=lambda p:p[:,0].mean())+sorted(strips[2:],key=lambda p:p[:,1].mean())
  spans=[];signs=[];valid=[]
  for s,p in enumerate(strips):
   axis=1 if s<2 else 0;other=1-axis
   reach=np.sqrt(max(0.,.086**2-float(np.median(p[:,other]))**2));inside=np.linalg.norm(p[:,:2],axis=1)<.080
   spans.append(bool(p[:,axis].min() < -reach and p[:,axis].max()>reach and inside.any() and np.all((p[inside,2]>.012)&(p[inside,2]<.030))))
  for j in range(3):
   row=[];ok=[]
   for i in range(2):
    a=strips[i];b=strips[2+j];hit=self.crossing(a,b)
    if hit is None:row.append(0);ok.append(False);continue
    xy,dz=hit
    row.append(1 if dz>.0006 else -1 if dz<-.0006 else 0)
    ok.append(bool(np.linalg.norm(xy)<.080 and spans[i] and spans[2+j]))
   signs.append(row);valid.append(all(ok))
  # Both checkerboard phases are equivalent; identities and which strip is
  # handled first do not matter. A merely criss-crossed, unwoven row earns zero.
  phases=[[bool(valid[j] and signs[j]==[phase*(-1)**j,-phase*(-1)**j]) for j in range(3)] for phase in [1,-1]]
  rows=max(phases,key=sum)
  return rows,spans,signs
 def measure(self):
  rows,s,signs=self.result();return dict(woven_rows=sum(rows),rows=rows,crossing_orders=signs,spanning_flat_strips=s,total_rows=3,maximum_strip_joint_gap_mm=self.peak_gap*1000,released_seconds=self.release,failed=self.failed,pie_upright=bool(self.orientation('pie')[2,2]>=np.cos(np.pi/6)))
 def score(self):
  q=self.measure();return 0. if self.failed or self.release<3 or not q['pie_upright'] else q['woven_rows']/3
 def state(self):return dict(super().state(),grasp_state=self.grasp_state,peak_gap=self.peak_gap)
