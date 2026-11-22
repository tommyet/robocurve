"""Mechanical trigger release and local hook capture, without pose writes."""
import numpy as np
from native_model import NativeModel
from geometry import *
class Model(NativeModel):
 def __init__(self):super().__init__();self.attached=set();self.closed_once=False;self.opened_after=False;self.detent={'old':0.,'new':0.}
 def configure_station(self):
  from pad_covers import install
  install()
 def reset_valid(self):return not self.disabled and not self.failed and Rotation.from_matrix(OPEN.T@self.orientation('old_visor')).magnitude()<np.radians(5)
 def material(self,hands,dt):
  # Passive two-position hinge detents, represented by a bistable spring.
  # Both potential wells have equal energy at the35-degree switching point.
  from pxr import UsdPhysics
  for tag in ['old','new']:
   relative=Rotation.from_matrix(self.orientation(tag+'_visor')).as_rotvec()[1]+np.radians(70)
   target=70. if relative>np.radians(35) else 0.
   self.detent[tag]=target
   for side in ['left','right']:
    UsdPhysics.DriveAPI(self.joints[tag+'_hinge_'+side].GetPrim(),'rotY').GetTargetPositionAttr().Set(target)
  for side in ['left','right']:
   pressed=-float(self.joint_gap('trigger_slide_'+side)[2])
   if pressed>.0028:
    self.disable('old_hinge_'+side,'release_trigger_pressed')
    if side in self.attached:
     self.disable('new_hinge_'+side,'release_trigger_pressed');self.enabled.discard('new_hinge_'+side);self.attached.discard(side)
   name='new_hinge_'+side
   if side not in self.attached and pressed<.001:
    gap=float(np.linalg.norm(self.joint_gap(name)));Q=self.orientation('new_ear_'+side)
    angle=Rotation.from_matrix(OPEN.T@Q).magnitude()
    if gap<.0025 and angle<np.radians(6) and np.linalg.norm(self.velocities[self.index['new_ear_'+side],:3])<.08:
     self.enable(name,'hook_seated_at_hinge');self.disabled.discard(name);self.attached.add(side)
  Q=self.orientation('new_visor');angle=Rotation.from_matrix(Q).as_rotvec()[1]
  if len(self.attached)==2 and abs(angle)<np.radians(8):self.closed_once=True
  if self.closed_once and len(self.attached)==2 and angle<np.radians(-55):self.opened_after=True
  self.failed |= bool(self.broken)
 def measure(self):
  old_off=all('old_hinge_'+s in self.disabled for s in ['left','right'])
  old_down=bool(abs(self.p('old_visor')[0]-TRAY[0])<.14 and abs(self.p('old_visor')[1]-TRAY[1])<.13 and self.p('old_visor')[2]<TABLE+.12)
  return dict(old_visor_detached=old_off,old_visor_in_tray=old_down,new_catches_seated=len(self.attached),closed_once=self.closed_once,reopened=self.opened_after,released_seconds=self.release,failed=self.failed)
 def score(self):
  m=self.measure()
  if self.failed:return 0.
  if m['old_visor_detached'] and m['new_catches_seated']==2 and m['closed_once'] and m['reopened'] and m['old_visor_in_tray'] and self.release>=2.:return 1.
  return .75 if len(self.attached)==2 else .5 if len(self.attached)==1 else .25 if m['old_visor_detached'] else 0.
 def state(self):return dict(super().state(),attached=sorted(self.attached),closed_once=self.closed_once,opened_after=self.opened_after,detent=self.detent)
 def restore(self,state):
  super().restore(state);self.attached=set(self.attached)
