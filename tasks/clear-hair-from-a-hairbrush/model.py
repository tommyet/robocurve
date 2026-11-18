import numpy as np
from native_model import NativeModel
from geometry import HAIRS,SEGMENTS
class Model(NativeModel):
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
  return dict(removed_fraction=float(clear.mean()),intact=not self.failed,released_seconds=self.release,failed=self.failed)
 def score(self):
  self.failed |= self.integrity_failed()
  if self.failed:return 0.
  x=self.measure()['removed_fraction']
  if x>=.9 and self.release>=3:return 1.
  return .5 if x>=.5 else (.25 if x>=.25 else 0.)
 def integrity_failed(self):return super().integrity_failed() or any(n.startswith('pin_') for n in self.broken)
