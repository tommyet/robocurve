"""Thin triangular sheet with elastic bending and pressure-set plastic creases.

No pre-folds, animated hinges or shape targets. Stretch constraints preserve
the paper; signed dihedral bending stencils resist curvature. A compressed,
folded stencil acquires a plastic rest angle under a measured finger pad.
Dihedral plasticity and finite-thickness self-contact approximate paper behavior.
"""
import numpy as np
from paper_solver import solve,restore_stretch,hinges
from common import Grips,TABLE

class Paper:
 def __init__(self):
  self.nx=31;self.ny=23;self.dx=.007
  self.p=np.array([[.195+i*.007,-.077+j*.007,TABLE+.0003] for i in range(self.nx) for j in range(self.ny)])
  self.flat=self.p.copy();self.v=np.zeros_like(self.p);self.faces=[]
  for i in range(self.nx-1):
   for j in range(self.ny-1):
    a=i*self.ny+j
    if j>=self.ny//2:self.faces.extend([(a,a+self.ny,a+1),(a+1,a+self.ny,a+self.ny+1)])
    else:self.faces.extend([(a,a+self.ny,a+self.ny+1),(a,a+self.ny+1,a+1)])
  edge_faces={}
  for f in self.faces:
   for a,b,c in [(f[0],f[1],f[2]),(f[1],f[2],f[0]),(f[2],f[0],f[1])]:edge_faces.setdefault(tuple(sorted((a,b))),[]).append(c)
  self.edges=np.array(list(edge_faces));self.rest=np.linalg.norm(self.p[self.edges[:,1]]-self.p[self.edges[:,0]],axis=1)
  bends=[(a,b,*v) for (a,b),v in edge_faces.items() if len(v)==2];self.bends=np.array(bends)
  self.bend_rest=np.linalg.norm(self.p[self.bends[:,2]]-self.p[self.bends[:,3]],axis=1);self.original_bend=self.bend_rest.copy()
  self.bend_stiffness=np.full(len(bends),.9)  # Uniform, initially uncreased paper.
  self.grips=Grips();self.patches={};self.previous={};self.failed=False;self.max_strain=1.;self.crease_events=0
  self.radius=.00025;self.time=0.;self.pressure_time=np.zeros(len(bends));self.rest_angle=np.zeros(len(bends));self.yield_time=np.zeros(len(bends))
  self.degree=np.bincount(self.edges.flatten(),minlength=len(self.p))
  self.neighbours=np.eye(len(self.p),dtype=bool)
  self.neighbours[self.edges[:,0],self.edges[:,1]]=True;self.neighbours[self.edges[:,1],self.edges[:,0]]=True
  self.face_array=np.asarray(self.faces);self.self_contacts=0
  # Disjoint constraint colours permit exact in-place stretch projections.
  groups=[];used=[]
  for index,(a,b) in enumerate(self.edges):
   for c,nodes in enumerate(used):
    if a not in nodes and b not in nodes:break
   else:c=len(groups);groups.append([]);used.append(set())
   groups[c].append(index);used[c].update([a,b])
  self.edge_groups=[np.asarray(g) for g in groups]
  self.edge_order=np.concatenate(self.edge_groups)
 def hinges(self):return hinges(self.p,self.bends)
 def self_contact(self,old,w):
  """Swept vertex/triangle contact for non-adjacent material patches."""
  from scipy.spatial import cKDTree
  tri=self.p[self.face_array];centers=tri.mean(axis=1)
  pairs=cKDTree(centers).query_ball_point(self.p,.016)
  vi=np.repeat(np.arange(len(self.p)),[len(row) for row in pairs]);fi=np.array([j for row in pairs for j in row],int)
  if not len(vi):return
  mask=~np.any(self.neighbours[vi[:,None],self.face_array[fi]],axis=1)
  vi,fi=vi[mask],fi[mask];t=tri[fi];e0=t[:,1]-t[:,0];e1=t[:,2]-t[:,0]
  n=np.cross(e0,e1);length=np.linalg.norm(n,axis=1);n/=np.maximum(length,1e-12)[:,None]
  v=self.p[vi]-t[:,0];signed=np.einsum('ij,ij->i',v,n)
  old_tri=old[self.face_array[fi]]
  old_normal=np.cross(old_tri[:,1]-old_tri[:,0],old_tri[:,2]-old_tri[:,0])
  old_normal/=np.maximum(np.linalg.norm(old_normal,axis=1),1e-12)[:,None]
  before=np.einsum('ij,ij->i',old[vi]-old_tri[:,0],old_normal)
  projected=v-signed[:,None]*n
  aa=np.einsum('ij,ij->i',e0,e0);bb=np.einsum('ij,ij->i',e0,e1);cc=np.einsum('ij,ij->i',e1,e1)
  dd=np.einsum('ij,ij->i',projected,e0);ee=np.einsum('ij,ij->i',projected,e1);den=np.maximum(aa*cc-bb*bb,1e-20)
  u=(dd*cc-ee*bb)/den;v=(ee*aa-dd*bb)/den
  inside=(u>=-.0001)&(v>=-.0001)&(u+v<=1.0001)&(length>1e-10)
  hit=inside&((signed*before<0)|(abs(signed)<2*self.radius))
  # At exact edge/vertex coincidence the previous sign can be zero. Use a
  # deterministic material-index tie break, not a preferred fold location.
  ambiguous=abs(before)<1e-6
  order=np.where(vi>self.face_array[fi].mean(axis=1),1.,-1.)
  before=np.where(ambiguous,order*np.where(n[:,2]>=0,1.,-1.),before)
  ids=vi[hit];face=self.face_array[fi[hit]];normal=n[hit]
  weights=np.c_[1-u[hit]-v[hit],u[hit],v[hit]]
  den=w[ids]+(w[face]*weights**2).sum(axis=1)
  correction=normal*((np.sign(before[hit])*2*self.radius-signed[hit])/np.maximum(den,1e-12))[:,None]
  delta=np.zeros_like(self.p);counts=np.zeros(len(self.p))
  np.add.at(delta,ids,correction*w[ids,None]);np.add.at(counts,ids,1)
  for k in range(3):
   np.add.at(delta,face[:,k],-correction*(w[face[:,k]]*weights[:,k])[:,None]);np.add.at(counts,face[:,k],1)
  self.p+=delta/np.maximum(1,counts[:,None]);self.self_contacts+=int(hit.sum())

 def step(self,hands,dt=.05):
  self.time+=dt
  closing={s:self.previous.get(s,1)-h['opening']>.0001 for s,h in hands.items()};self.previous={s:h['opening'] for s,h in hands.items()}
  valid={s:(h if closing[s] or s in self.grips.held else dict(h,opening=max(.31,h['opening']))) for s,h in hands.items()}
  before=set(self.grips.held);self.grips.update(self.p,valid)
  for s in set(self.grips.held)-before:
   i=self.grips.held[s]['index'];h=hands[s]
   # A finite strip of the paper is pinched along the finger pad. Collinear
   # captured points may turn about that strip, but an interior pinch resists
   # free yaw/sliding of the entire sheet. At a corner there may be one point.
   local=(self.p-self.p[i])@h['rotation']
   ids=np.flatnonzero((abs(local[:,0])<.002)&(abs(local[:,1])<=.012)&(abs(local[:,2])<.001))
   self.grips.events.append(dict(event='pinch_patch',side=s,indices=ids.tolist()))
   self.patches[s]={int(j):(self.p[j]-h['tcp'])@h['rotation'] for j in ids}
  for s in list(self.patches):
   if s not in self.grips.held:del self.patches[s]
  targets={j:hands[s]['tcp']+hands[s]['rotation']@v for s,d in self.patches.items() for j,v in d.items()}
  w=np.ones(len(self.p));w[list(targets)]=0;starts={j:self.p[j].copy() for j in targets};substeps=6;h=dt/substeps
  ei,ej=self.edges.T;bi,bj=self.bends[:,2:].T
  for sub in range(substeps):
   old=self.p.copy();self.v[:,2]-=9.81*h;self.v*=np.exp(-8*h);self.p+=h*self.v
   ids=np.asarray(list(targets),dtype=np.int64)
   positions=np.array([starts[j]+(sub+1)/substeps*(targets[j]-starts[j]) for j in ids]).reshape(-1,3)
   solve(self.p,self.edges,self.rest,self.edge_order,self.bends,self.bend_stiffness,self.rest_angle,w,ids,positions,TABLE+self.radius,24)
   self.self_contact(old,w)
   # Restore in-plane distances after bending/contact corrections; finite
   # thickness must not turn contact into artificial paper extension.
   restore_stretch(self.p,self.edges,self.rest,self.edge_order,w,TABLE+self.radius,60)
   # Plastic deformation only under a fingertip on an already bent region.
   mid=(self.p[self.bends[:,0]]+self.p[self.bends[:,1]])/2
   pressed=np.zeros(len(mid),bool)
   for side,hand in hands.items():
    for sign in [-1,1]:
     pad=hand['tcp']+hand['rotation']@np.array([sign*hand['opening']*.094/2,0,.01284])
     rel=mid-pad
     pressed|=(np.linalg.norm(rel[:,:2],axis=1)<.012)&(abs(rel[:,2])<.003)
   angle,_=self.hinges()
   active=pressed&(abs(angle)>.35)
   self.pressure_time=np.where(active,self.pressure_time+h,0.)
   self.yield_time=np.where(abs(angle)>1.05,self.yield_time+h,0.)
   setting=(self.pressure_time>=.10)|(self.yield_time>=.20)
   diff=np.arctan2(np.sin(angle-self.rest_angle),np.cos(angle-self.rest_angle))
   self.rest_angle[setting]+=.12*diff[setting]
   self.crease_events+=int(np.sum(setting&(abs(diff)>.005)))
   self.v=(self.p-old)/h
   contact=self.p[:,2]<=TABLE+self.radius+1e-6;self.v[contact,:2]*=.65;self.v[contact,2]=np.maximum(0,self.v[contact,2])
  strain=float(np.max(np.linalg.norm(self.p[ej]-self.p[ei],axis=1)/self.rest));self.max_strain=max(self.max_strain,strain)
  if strain>1.20 or not np.isfinite(self.p).all():self.failed=True
 def state(self):return dict(points=self.p,bend_rest=self.bend_rest,rest_angle=self.rest_angle)
