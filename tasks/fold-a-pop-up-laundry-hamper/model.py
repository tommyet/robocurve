import numpy as np
from native_model import NativeModel
from geometry import SURFACES,N
class Model(NativeModel):
 def __init__(self):
  super().__init__();self.nodes={s['name']:s['points'].copy() for s in SURFACES};self.node_velocities={n:np.zeros_like(p) for n,p in self.nodes.items()};self.peak_stretch={n:1. for n in self.nodes}
 def configure_station(self):
  from pad_covers import install
  install()
 def bind_native(self,base):
  self.surfaces={};super().bind_native(base)
  from isaaclab_physx.physics import PhysxManager as SimulationManager
  view=SimulationManager.get_physics_sim_view()
  for s in SURFACES:
   v=view.create_surface_deformable_body_view('/World/envs/env_*/materials/'+s['name'])
   if v.count!=1:raise RuntimeError('Expected one native '+s['name']+' surface')
   self.surfaces[s['name']]=v
  self.read()
 def read(self):
  super().read()
  for s in SURFACES:
   v=getattr(self,'surfaces',{}).get(s['name'])
   if v is not None:
    self.nodes[s['name']]=v.get_simulation_nodal_positions().numpy()[0,:len(s['points'])].copy();self.node_velocities[s['name']]=v.get_simulation_nodal_velocities().numpy()[0,:len(s['points'])].copy()
 def release_points(self):return np.vstack(list(self.nodes.values()))
 def update(self,hands,dt=.05):
  self.read();self.time+=dt;points=self.release_points()
  clear=all(h['opening']>.4 and np.min(np.linalg.norm(points-h['tcp'],axis=1))>.05 for h in hands.values());self.release=self.release+dt if clear else 0.
  for s in SURFACES:
   p=self.nodes[s['name']];e=s['edges'];stretch=np.linalg.norm(p[e[:,1]]-p[e[:,0]],axis=1)/s['rest_lengths'];self.peak_stretch[s['name']]=max(self.peak_stretch[s['name']],float(stretch.max()))
  self.failed |= self.integrity_failed()
 def integrity_failed(self):
  return super().integrity_failed() or any(not np.isfinite(v).all() for v in self.nodes.values()) or self.peak_stretch['frame']>1.02 or self.peak_stretch['cloth']>1.35 or self.peak_stretch['band']>3.5
 def measure(self):
  wire=self.nodes['frame'];packet=np.vstack([wire,self.nodes['cloth']]);band=self.nodes['band'];centre=wire.mean(axis=0);_,_,axes=np.linalg.svd(wire-centre,full_matrices=False);local=(packet-centre)@axes.T;extent=np.ptp(local,axis=0)+.007
  _,_,ba=np.linalg.svd(band-band.mean(axis=0),full_matrices=False);across=ba[0]-axes[2]*float(ba[0]@axes[2]);across/=max(np.linalg.norm(across),1e-12)
  # Use the centreline of the elastic, preserving its topological order.
  mid=band[64:128];bl=np.c_[(mid-centre)@across,(mid-centre)@axes[2]];pl=np.c_[(packet-centre)@across,(packet-centre)@axes[2]]
  a=np.arctan2(bl[:,1],bl[:,0]);d=np.diff(np.r_[a,a[0]]);w=abs(np.sum((d+np.pi)%(2*np.pi)-np.pi))/(2*np.pi)
  enclosed=bool(w>.8 and bl[:,0].min()<pl[:,0].min()+.02 and bl[:,0].max()>pl[:,0].max()-.02 and bl[:,1].min()<pl[:,1].min()+.005 and bl[:,1].max()>pl[:,1].max()-.005)
  return dict(bundle_long_mm=float(max(extent[:2])*1000),bundle_short_mm=float(min(extent[:2])*1000),thickness_mm=float(extent[2]*1000),retainer_encloses_packet=enclosed,intact=not self.failed,released_seconds=self.release,failed=self.failed)
 def score(self):
  self.failed |= self.integrity_failed();m=self.measure()
  if self.failed:return 0.
  compact=m['bundle_long_mm']<=220 and m['bundle_short_mm']<=220 and m['thickness_mm']<=60
  if compact and m['retainer_encloses_packet'] and self.release>=3:return 1.
  if compact:return .5
  return .25 if m['bundle_long_mm']<=350 and m['bundle_short_mm']<=250 else 0.
 def state(self):return dict(super().state(),nodes=self.nodes,node_velocities=self.node_velocities,peak_stretch=self.peak_stretch)
 def restore(self,state):
  s=dict(state);self.nodes={k:np.asarray(v) for k,v in s.pop('nodes').items()};self.node_velocities={k:np.asarray(v) for k,v in s.pop('node_velocities').items()};self.peak_stretch=s.pop('peak_stretch');super().restore(s)
