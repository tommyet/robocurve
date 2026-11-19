import numpy as np
from native_model import NativeModel
from geometry import HEAD,HEADROT,RADII,POINTS,TRIS,RIM,EDGES,REST_LENGTHS
class Model(NativeModel):
 def __init__(self):super().__init__();self.grasp_state={};self.nodes=POINTS.copy();self.node_velocities=np.zeros_like(self.nodes);self.peak_stretch=1.
 def configure_station(self):
  from pad_covers import install
  install()
 def bind_native(self,base):
  self.surface=None;super().bind_native(base)
  from isaaclab_physx.physics import PhysxManager as SimulationManager
  view=SimulationManager.get_physics_sim_view();self.surface=view.create_surface_deformable_body_view('/World/envs/env_*/materials/cap')
  if self.surface.count!=1:raise RuntimeError('Expected one native cap surface')
  from finite_pinch import FinitePinch
  self.pinch=FinitePinch(self,[n for n in self.names if n.startswith('rim_contact_')],0.0015,0.003,0.002,(-0.025, 0.008))
  self.read()
 def read(self):
  super().read()
  if getattr(self,'surface',None) is not None:
   self.nodes=self.surface.get_simulation_nodal_positions().numpy()[0,:len(POINTS)].copy()
   self.node_velocities=self.surface.get_simulation_nodal_velocities().numpy()[0,:len(POINTS)].copy()
 def release_points(self):return self.nodes
 def update(self,hands,dt=.05):
  self.read();self.time+=dt;self.pinch.update(hands)
  clear=all(h['opening']>.4 and np.min(np.linalg.norm(self.nodes-h['tcp'],axis=1))>.05 for h in hands.values())
  self.release=self.release+dt if clear else 0.
  self.peak_stretch=max(self.peak_stretch,float(np.max(np.linalg.norm(self.nodes[EDGES[:,1]]-self.nodes[EDGES[:,0]],axis=1)/REST_LENGTHS)))
  self.failed |= self.integrity_failed()
 def rim_gap(self):return max(float(np.linalg.norm(self.nodes[node]-self.p(f'rim_contact_{i:03d}'))) for i,node in enumerate(RIM))
 def integrity_failed(self):return self.rim_gap()>.005 or super().integrity_failed() or not np.isfinite(self.nodes).all() or self.peak_stretch>3.
 def measure(self):
  rim=self.nodes[RIM];local=(rim-HEAD)@HEADROT
  # The rim must encircle the head below the crown, while its front arc
  # stays above the eyes. The normalised radial check excludes a cap beside it.
  angle=np.arctan2(local[:,1],local[:,0]);d=np.diff(np.r_[angle,angle[0]]);winding=abs(np.sum((d+np.pi)%(2*np.pi)-np.pi))/(2*np.pi)
  front=local[:,0]<-.045
  radial=np.sqrt((local[:,0]/RADII[0])**2+(local[:,1]/RADII[1])**2)
  crown=float(np.linalg.norm(self.nodes[0]-(HEAD+HEADROT@np.array([0,0,RADII[2]]))))
  fitted=bool(winding>.9 and radial.min()>.55 and radial.max()<1.35 and local[:,2].max()<.075 and local[:,2].min()>-.055)
  clear=bool(front.any() and local[front,2].min()>=.030)
  return dict(rim_attachment_gap_mm=self.rim_gap()*1000,crown_gap_mm=crown*1000,rim_encircles_head=fitted,face_clear=clear,intact=not self.failed,released_seconds=self.release,failed=self.failed)
 def score(self):
  self.failed |= self.integrity_failed();m=self.measure()
  if self.failed:return 0.
  if m['rim_encircles_head'] and m['face_clear'] and m['crown_gap_mm']<=20 and self.release>=3:return 1.
  if m['rim_encircles_head'] and m['face_clear']:return .5
  return .25 if m['crown_gap_mm']<=25 and m['face_clear'] else 0.
 def state(self):return dict(super().state(),grasp_state=self.grasp_state,nodes=self.nodes,node_velocities=self.node_velocities,peak_stretch=self.peak_stretch)
 def restore(self,state):
  s=dict(state);self.nodes=np.asarray(s.pop('nodes'));self.node_velocities=np.asarray(s.pop('node_velocities'));self.peak_stretch=s.pop('peak_stretch');super().restore(s)
