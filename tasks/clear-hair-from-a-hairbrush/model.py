import numpy as np
from native_model import NativeModel
from geometry import HAIRS,SEGMENTS
class Model(NativeModel):
 def __init__(self):super().__init__();self.comb_touched_locks=set()
 def bind_native(self,base):
  super().bind_native(base)
  from isaaclab.app.settings_manager import get_settings_manager
  get_settings_manager().set_bool('/physics/disableContactProcessing',False)
 def subscribe_events(self):
  super().subscribe_events()
  from pxr import PhysicsSchemaTools
  from omni.physx import get_physx_simulation_interface
  def contacts(headers,data):
   for h in headers:
    names=[str(PhysicsSchemaTools.intToSdfPath(a)).rsplit('/',1)[-1] for a in (h.actor0,h.actor1)]
    if 'comb' not in names:continue
    other=names[1-names.index('comb')]
    if not other.startswith('hair_'):continue
    strand=int(other.split('_')[1])
    if strand in self.comb_touched_locks:continue
    for j in range(h.contact_data_offset,h.contact_data_offset+h.num_contact_data):
     impulse=float(np.linalg.norm(data[j].impulse))
     if impulse>1e-12:
      self.comb_touched_locks.add(strand);self.events.append(dict(event='comb_hair_contact',lock=strand,body=other,impulse_ns=impulse,position_m=list(data[j].position),time=self.time));break
  self.contact_subscription=get_physx_simulation_interface().subscribe_contact_report_events(contacts)
 def configure_station(self):
  from pad_covers import install
  install()
 def material(self,hands,dt):self.failed |= any(n.startswith('pin_') for n in self.broken)
 def measure(self):
  hair=np.array([self.p(f'hair_{s}_{i}') for s in range(HAIRS) for i in range(SEGMENTS)])
  local=(hair-self.p('brush'))@self.orientation('brush')
  trapped=(abs(local[:,0])<.029)&(abs(local[:,1])<.050)&(local[:,2]>-.010)&(local[:,2]<.033)
  # Count a strand as cleared only when its entire centreline leaves the
  # expanded bristle envelope. This corresponds to weighing removed locks.
  clear=~trapped.reshape(HAIRS,SEGMENTS).any(axis=1)
  qualified=clear & np.array([s in self.comb_touched_locks for s in range(HAIRS)])
  return dict(removed_fraction=float(clear.mean()),comb_cleared_fraction=float(qualified.mean()),comb_touched_locks=len(self.comb_touched_locks),remaining_contact_snags=20-sum(n.startswith('hair_snag_') for n in self.broken),intact=not self.failed,released_seconds=self.release,failed=self.failed)
 def reset_valid(self):
  q=self.measure();return q['removed_fraction']==0. and q['remaining_contact_snags']>=18 and not self.failed
 def score(self):
  self.failed |= self.integrity_failed()
  if self.failed:return 0.
  x=self.measure()['comb_cleared_fraction']
  if x>=.9 and self.release>=3:return 1.
  return .5 if x>=.5 else (.25 if x>=.25 else 0.)
 def integrity_failed(self):return super().integrity_failed() or any(n.startswith('pin_') for n in self.broken)

 def state(self):return dict(super().state(),comb_touched_locks=sorted(self.comb_touched_locks))
 def restore(self,state):
  s=dict(state);self.comb_touched_locks=set(s.pop('comb_touched_locks'));super().restore(s)
