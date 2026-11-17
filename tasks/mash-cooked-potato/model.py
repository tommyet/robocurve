import numpy as np
from native_model import NativeModel
from geometry import JOINTS
class Model(NativeModel):
 def material(self,hands,dt):pass
 def measure(self):
  names=[n for n in self.names if n.startswith('food_')];parent={n:n for n in names}
  def root(n):
   while parent[n]!=n:n=parent[n]
   return n
  for j in JOINTS:
   if j['name'] not in self.broken:parent[root(j['a'])]=root(j['b'])
  groups={}
  for n in names:groups.setdefault(root(n),[]).append(n)
  sizes={}
  for key,ns in groups.items():
   p=np.array([self.p(n) for n in ns]);sizes[key]=float(np.max(np.linalg.norm(p[:,None]-p[None,:],axis=-1))+.007)
  local=np.array([self.orientation('bowl').T@(self.p(n)-self.p('bowl')) for n in names]);inside=(np.linalg.norm(local[:,:2],axis=1)<.075)&(local[:,2]>.003)&(local[:,2]<.060)
  small=np.array([sizes[root(n)]<=.009 for n in names])
  return dict(small_lump_mass_fraction=float((small&inside).sum()/max(1,inside.sum())),retained_mass_fraction=float(inside.mean()),largest_lump_mm=max(sizes.values())*1000,released_seconds=self.release,failed=self.failed)
 def integrity_failed(self):return super().integrity_failed() or (False)
 def score(self):
  self.failed |= self.integrity_failed()
  m=self.measure()
  if self.failed or m['retained_mass_fraction']<.95:return 0.
  f=m['small_lump_mass_fraction']
  if f>=.95 and self.release>=3:return 1.
  return .5 if f>=.75 else .25 if f>=.5 else 0.
