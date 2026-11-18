import numpy as np
from native_model import NativeModel
from geometry import HAIRS,SEGMENTS
class Model(NativeModel):
 def __init__(self):super().__init__();self.comb_touched_locks=set()
 def bind_native(self,base):
  super().bind_native(base)
  from isaaclab.app.settings_manager import get_settings_manager
  get_settings_manager().set_bool('/physics/disableContactProcessing',False)
  from pxr import UsdUtils
  import omni.physics.tensors as tensors
  cache=UsdUtils.StageCache.Get();stage_id=cache.GetId(self.stage).ToLongInt()
  if stage_id<0:cache.Insert(self.stage);stage_id=cache.GetId(self.stage).ToLongInt()
  self.contact_sim=tensors.create_simulation_view('torch',stage_id);self.contact_sim.set_subspace_roots('/')
  roots={p.GetName():str(p.GetPath()) for p in self.stage.Traverse() if '/materials/' in str(p.GetPath()) and p.GetName() in self.index}
  hair_paths=[roots[f'hair_{s}_{i}'] for s in range(HAIRS) for i in range(SEGMENTS)]
  self.contact_view=self.contact_sim.create_rigid_contact_view([roots['comb']],filter_patterns=[hair_paths],max_contact_data_count=4096)
  if self.contact_view.sensor_count!=1 or self.contact_view.filter_count!=len(hair_paths):raise RuntimeError('Incomplete native comb contact matrix')
  paths=list(self.contact_view.filter_paths)
  if paths and isinstance(paths[0],(list,tuple)):paths=paths[0]
  self.contact_order=np.asarray([paths.index(p) for p in hair_paths]);self.contact_dt=float(base.physics_dt)
 def record_tool_contacts(self):
  value=self.contact_view.get_contact_force_matrix(dt=self.contact_dt)
  forces=getattr(value,'torch',value).detach().cpu().numpy()[0,self.contact_order]
  magnitudes=np.linalg.norm(forces,axis=1).reshape(HAIRS,SEGMENTS)
  for strand in range(HAIRS):
   if strand in self.comb_touched_locks:continue
   index=int(np.argmax(magnitudes[strand]));force=float(magnitudes[strand,index])
   if force>1e-6:
    self.comb_touched_locks.add(strand);self.events.append(dict(event='comb_hair_contact',lock=strand,body=f'hair_{strand}_{index}',impulse_ns=force*self.contact_dt,force_n=force,time=self.time,source='native filtered contact-force matrix'))
 def configure_station(self):
  from pad_covers import install
  install()
 def material(self,hands,dt):
  self.record_tool_contacts();self.failed |= any(n.startswith('pin_') for n in self.broken)
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

 def draw(self,d):
  from hair_visual import draw
  draw(self,d)
 def state(self):return dict(super().state(),comb_touched_locks=sorted(self.comb_touched_locks))
 def restore(self,state):
  s=dict(state);self.comb_touched_locks=set(s.pop('comb_touched_locks'));super().restore(s)
