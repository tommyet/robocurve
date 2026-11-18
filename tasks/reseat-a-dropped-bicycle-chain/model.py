import numpy as np
from native_model import NativeModel
from geometry import FRONT,REAR,R,RR,LINKS,BIKE_ROT
class Model(NativeModel):
 def __init__(self):super().__init__();self.previous_angle=0.;self.turn=0.;self.lo=0.;self.hi=0.;self.clean_turns=0.
 def configure_station(self):
  from pad_covers import install
  install()
 def engagement(self):
  links=np.array([self.p(f'link_{i:03d}') for i in range(LINKS)])
  links=(links-self.p('bicycle_frame'))@self.orientation('bicycle_frame');rear=(REAR-FRONT)@BIKE_ROT
  front=(abs(links[:,0])<.0045)&(abs(np.linalg.norm(links[:,1:],axis=1)-R)<.007)
  rear=(abs(links[:,0]-rear[0])<.0045)&(abs(np.linalg.norm(links[:,1:]-rear[1:],axis=1)-RR)<.007)
  return int(front.sum()),int(rear.sum())
 def material(self,hands,dt):
  self.failed |= bool(self.broken)
  R0=self.orientation('bicycle_frame').T@self.orientation('chainring');angle=float(np.arctan2(R0[2,1],R0[1,1]));delta=(angle-self.previous_angle+np.pi)%(2*np.pi)-np.pi;self.previous_angle=angle
  front,rear=self.engagement()
  if front>=14 and rear>=5:
   self.turn+=delta;self.lo=min(self.lo,self.turn);self.hi=max(self.hi,self.turn);self.clean_turns=(self.hi-self.lo)/(2*np.pi)
  else:self.turn=self.lo=self.hi=self.clean_turns=0.
 def measure(self):
  f,r=self.engagement();return dict(engaged_front_links=f,engaged_rear_links=r,continuous_crank_revolutions=self.clean_turns,intact=not self.failed,released_seconds=self.release,failed=self.failed)
 def score(self):
  if self.failed or self.broken:return 0.
  if self.clean_turns>=2 and self.release>=3:return 1.
  return .5 if self.clean_turns>=1 else (.25 if self.clean_turns>=.25 else 0.)
 def state(self):return dict(super().state(),previous_angle=self.previous_angle,turn=self.turn,lo=self.lo,hi=self.hi,clean_turns=self.clean_turns)
