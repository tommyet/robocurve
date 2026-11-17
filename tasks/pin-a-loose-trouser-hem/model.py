"""Puncture and catch rules require native spring compression and real alignment."""
import numpy as np
from native_model import NativeModel
from geometry import DX,DY
class Model(NativeModel):
 def __init__(self):super().__init__();self.holes={};self.latched=False;self.max_puncture_load=0.
 def material(self,hands,dt):
  from pxr import Gf
  from scipy.spatial.transform import Rotation
  axis=self.orientation('pin_arm')[:,0];compression=max(0.,-float(self.joint_gap('point_compression')@axis));load=5000*compression;self.max_puncture_load=max(self.max_puncture_load,load)
  tip=self.p('needle_point',[.001,0,0])
  if load>=.8:
   for name in self.names:
    if not name.startswith(('front_','back_','hem_')) or name in self.holes:continue
    local=self.orientation(name).T@(tip-self.p(name));half_y=.005 if name.startswith('hem_') else DY/2
    if abs(local[0])<DX/2-.001 and abs(local[1])<half_y-.001 and abs(local[2])<.0012 and abs(axis@self.orientation(name)[:,2])>.2:
     j=self.joints['hole_'+name];anchor=self.orientation('pin_arm').T@(tip-self.p('pin_arm'))
     j.GetLocalPos0Attr().Set(Gf.Vec3f(*anchor));j.GetLocalPos1Attr().Set(Gf.Vec3f(*local))
     q=Rotation.from_matrix(self.orientation(name).T@self.orientation('pin_arm')).as_quat();j.GetLocalRot1Attr().Set(Gf.Quatf(float(q[3]),Gf.Vec3f(*q[:3])))
     self.exclude_collision('needle_point',name)
     self.enable('hole_'+name,'needle_punctured_under_load');self.holes[name]=local.copy()
  shield=self.p('pin_frame',[.045,0,.002]);gap=np.linalg.norm(tip-shield)
  relative=self.orientation('pin_frame').T@self.orientation('pin_arm');angle=np.arccos(np.clip((np.trace(relative)-1)/2,-1,1))
  if not self.latched and gap<.0015 and angle<np.radians(3):
   j=self.joints['pin_catch'];j.GetLocalPos1Attr().Set(Gf.Vec3f(*(self.orientation('pin_arm').T@(self.p('pin_frame',[.043,0,.001])-self.p('pin_arm')))))
   q=Rotation.from_matrix(self.orientation('pin_arm').T@self.orientation('pin_frame')).as_quat();j.GetLocalRot1Attr().Set(Gf.Quatf(float(q[3]),Gf.Vec3f(*q[:3])))
   self.enable('pin_catch','sprung_point_entered_shield');self.latched=True
  self.failed |= any(n.startswith(('cloth_','side_seam_','fold_','hem_','hole_','existing_stitch_')) for n in self.broken) or bool({'pin_catch','point_compression','pin_spring'} & self.broken)
 def measure(self):
  front=[n for n in self.holes if n.startswith('front_')];hem=[n for n in self.holes if n.startswith('hem_')];back=[n for n in self.holes if n.startswith('back_')]
  same_region=bool(len(front)>=2 and len(hem)>=2 and min(np.linalg.norm(self.p(a)-self.p(b)) for a in front for b in hem)<.025)
  return dict(front_layer_pierced=bool(front),hem_layer_pierced=bool(hem),back_of_leg_pierced=bool(back),both_layers_held=same_region,point_enclosed=self.latched,punctures=len(self.holes),fabric_intact=not self.failed,released_seconds=self.release,max_puncture_load_N=self.max_puncture_load,failed=self.failed)
 def integrity_failed(self):return super().integrity_failed() or (any(n.startswith(('cloth_','side_seam_','fold_','hem_','hole_','existing_stitch_')) for n in self.broken) or bool({'pin_catch','point_compression','pin_spring'} & self.broken))
 def score(self):
  self.failed |= self.integrity_failed()
  m=self.measure()
  if self.failed or m['back_of_leg_pierced'] or m['punctures']>4:return 0.
  if m['both_layers_held'] and self.latched and self.release>=3:return 1.
  if m['both_layers_held']:return .5
  return .25 if m['front_layer_pierced'] or m['hem_layer_pierced'] else 0.
 def state(self):return dict(**super().state(),holes=self.holes,latched=self.latched,max_puncture_load=self.max_puncture_load)
