import numpy as np
from native_model import NativeModel
from geometry import FC,CARRIER_OFFSET
from common import TABLE
class Model(NativeModel):
 def __init__(self):super().__init__();self.grasp_state={}
 def bind_native(self,base):
  super().bind_native(base)
  from finite_pinch import FinitePinch
  self.pinch=FinitePinch(self,['screwdriver'],.009,.003,.002,(-.037,.008))
 def configure_station(self):
  from pad_covers import install
  install()
 def material(self,hands,dt):self.pinch.update(hands);self.failed |= bool(self.broken)
 def state(self):return dict(super().state(),grasp_state=self.grasp_state)
 def measure(self):
  R=self.orientation('plug');new=(self.p('spare_fuse')-self.p('plug'))@R;old=(self.p('old_fuse')-self.p('plug'))@R;carrier=(self.p('carrier')-self.p('plug'))@R
  # Cylinder child geometry maps its Z axis onto the fuse body's local X.
  gap=float(np.linalg.norm(new-FC));axis=abs(float((R.T@self.orientation('spare_fuse'))[0,0]))
  seated=bool(gap<.003 and axis>.95)
  closed=bool(np.linalg.norm(carrier-CARRIER_OFFSET)<.0025 and float(np.trace(R.T@self.orientation('carrier'))) > 2.9)
  # Real scoring: visible metal caps correctly in both spring clips, face
  # carrier flush and retained, and old fuse outside the plug.
  on_table=all(self.p(n)[2]>=TABLE-.015 for n in ['plug','old_fuse','spare_fuse','carrier'])
  return dict(parts_on_table=on_table,old_fuse_seated=bool(np.linalg.norm(old-FC)<.003),old_fuse_removed=bool(np.linalg.norm(old-FC)>.04),replacement_seated=seated,cover_closed=closed,intact=not self.failed,released_seconds=self.release,failed=self.failed)
 def reset_valid(self):
  m=self.measure();return m['old_fuse_seated'] and m['cover_closed']
 def score(self):
  if self.failed or self.broken:return 0.
  m=self.measure()
  if not m['parts_on_table'] or not m['old_fuse_removed']:return 0.
  if m['replacement_seated'] and m['cover_closed'] and self.release>=3:return 1.
  return .5 if m['replacement_seated'] else .25
