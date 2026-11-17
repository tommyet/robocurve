import numpy as np
from native_model import NativeModel
class Model(NativeModel):
 def material(self,hands,dt):self.failed |= bool(self.broken)
 def measure(self):
  wire=np.array([self.p(n) for n in self.names if n.startswith('wire_')]);band=np.array([self.p(n) for n in self.names if n.startswith('elastic_')]);centre=wire.mean(axis=0)
  _,_,axes=np.linalg.svd(wire-centre,full_matrices=False);local=(wire-centre)@axes.T;extent=np.ptp(local,axis=0)
  # Retention is observed after release, not asserted by a success-triggered latch.
  band_local=(band-centre)@axes.T
  a=np.arctan2(band_local[:,2],band_local[:,0]);delta=np.diff(np.r_[a,a[0]]);winding=abs(np.sum((delta+np.pi)%(2*np.pi)-np.pi))/(2*np.pi)
  enclosed=bool(winding>.8 and band_local[:,0].min()<local[:,0].min()+.02 and band_local[:,0].max()>local[:,0].max()-.02 and band_local[:,2].min()<local[:,2].min()+.005 and band_local[:,2].max()>local[:,2].max()-.005)
  return dict(bundle_long_mm=float(max(extent[:2])*1000),bundle_short_mm=float(min(extent[:2])*1000),thickness_mm=float(extent[2]*1000),retainer_encloses_packet=enclosed,intact=not self.failed,released_seconds=self.release,failed=self.failed)
 def integrity_failed(self):return super().integrity_failed() or (bool(self.broken))
 def score(self):
  self.failed |= self.integrity_failed()
  m=self.measure()
  if self.failed:return 0.
  compact=m['bundle_long_mm']<=220 and m['bundle_short_mm']<=220 and m['thickness_mm']<=60
  if compact and m['retainer_encloses_packet'] and self.release>=3:return 1.
  if compact:return .5
  return .25 if m['bundle_long_mm']<=350 and m['bundle_short_mm']<=250 else 0.
