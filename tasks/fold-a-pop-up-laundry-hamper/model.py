import numpy as np
from native_model import NativeModel
from geometry import BODIES
class Model(NativeModel):
 def configure_station(self):
  from pad_covers import install
  install()
 def material(self,hands,dt):self.failed |= bool(self.broken)
 def packet_points(self):
  # Measure the outside of the rods and cloth, not only rod centres.
  if not hasattr(self,'packet_ids'):
   self.packet_ids=[i for i,b in enumerate(BODIES) if b['name'].startswith(('wire_','mesh_'))]
   signs=np.array([[x,y,z] for x in [-1,1] for y in [-1,1] for z in [-1,1]])
   self.packet_corners=np.array([signs*np.asarray(BODIES[i]['shapes'][0]['size'])/2 for i in self.packet_ids])
  return (np.einsum('nij,nkj->nki',self.R[self.packet_ids],self.packet_corners)+self.poses[self.packet_ids,None,:3]).reshape(-1,3)
 def measure(self):
  wire=np.array([self.p(n) for n in self.names if n.startswith('wire_')]);band=np.array([self.p(n) for n in self.names if n.startswith('elastic_')]);centre=wire.mean(axis=0)
  _,_,axes=np.linalg.svd(wire-centre,full_matrices=False);packet=self.packet_points();local=(packet-centre)@axes.T;extent=np.ptp(local,axis=0)
  # Retention is observed after release, not asserted by a success-triggered latch.
  # The retaining loop can wrap at any angle across the packet. Use its
  # observed plane, so a harmless in-plane rotation cannot lose credit.
  _,_,band_axes=np.linalg.svd(band-band.mean(axis=0),full_matrices=False)
  across=band_axes[0]-axes[2]*float(band_axes[0]@axes[2]);across/=max(np.linalg.norm(across),1e-12)
  band_local=np.c_[(band-centre)@across,(band-centre)@np.cross(axes[2],across),(band-centre)@axes[2]]
  retained_local=np.c_[(packet-centre)@across,(packet-centre)@np.cross(axes[2],across),(packet-centre)@axes[2]]
  a=np.arctan2(band_local[:,2],band_local[:,0]);delta=np.diff(np.r_[a,a[0]]);winding=abs(np.sum((delta+np.pi)%(2*np.pi)-np.pi))/(2*np.pi)
  enclosed=bool(winding>.8 and band_local[:,0].min()<retained_local[:,0].min()+.02 and band_local[:,0].max()>retained_local[:,0].max()-.02 and band_local[:,2].min()<retained_local[:,2].min()+.005 and band_local[:,2].max()>retained_local[:,2].max()-.005)
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
 def draw(self,d):
  if not hasattr(self,'fabric_view'):
   from fabric_view import FabricView
   self.fabric_view=FabricView(d)
  self.fabric_view.update(self)
