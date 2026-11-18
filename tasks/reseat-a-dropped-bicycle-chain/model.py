"""Outcome checks for seating and a continuous backpedal function check."""
import numpy as np
from native_model import NativeModel
from geometry import FRONT,REAR,R,RR,LINKS,BIKE_ROT
class Model(NativeModel):
 def __init__(self):
  super().__init__();self.previous_angle=0.;self.turn=0.;self.lo=0.;self.hi=0.;self.clean_turns=0.;self.chain_turn=0.;self.chain_lo=0.;self.chain_hi=0.;self.previous_link_angles=None;self.previous_engaged=None
 def configure_station(self):
  from pad_covers import install
  install()
 def chain_coordinates(self):
  links=np.array([self.p(f'link_{i:03d}') for i in range(LINKS)])
  return (links-self.p('bicycle_frame'))@self.orientation('bicycle_frame')
 def masks(self,links):
  rear=(REAR-FRONT)@BIKE_ROT
  front=(abs(links[:,0])<.0045)&(abs(np.linalg.norm(links[:,1:],axis=1)-R)<.007)
  back=(abs(links[:,0]-rear[0])<.0045)&(abs(np.linalg.norm(links[:,1:]-rear[1:],axis=1)-RR)<.007)
  return front,back
 def engagement(self):
  f,r=self.masks(self.chain_coordinates());return int(f.sum()),int(r.sum())
 def material(self,hands,dt):
  self.failed |= bool(self.broken)
  R0=self.orientation('bicycle_frame').T@self.orientation('chainring');angle=float(np.arctan2(R0[2,1],R0[1,1]));delta=(angle-self.previous_angle+np.pi)%(2*np.pi)-np.pi;self.previous_angle=angle
  links=self.chain_coordinates();front,rear=self.masks(links);angles=np.arctan2(links[:,2],links[:,1])
  valid=front & self.previous_engaged if self.previous_engaged is not None else np.zeros(LINKS,dtype=bool)
  if front.sum()>=14 and rear.sum()>=5 and valid.sum()>=6:
   motion=(angles-self.previous_link_angles+np.pi)%(2*np.pi)-np.pi
   self.turn+=delta;self.chain_turn+=float(np.median(motion[valid]))
   self.lo=min(self.lo,self.turn);self.hi=max(self.hi,self.turn);self.chain_lo=min(self.chain_lo,self.chain_turn);self.chain_hi=max(self.chain_hi,self.chain_turn)
   # The crank alone cannot earn credit: the engaged chain must also advance.
   self.clean_turns=min(max(0.,-self.turn),max(0.,-self.chain_turn))/(2*np.pi)
  else:self.turn=self.lo=self.hi=self.chain_turn=self.chain_lo=self.chain_hi=self.clean_turns=0.
  self.previous_link_angles=angles;self.previous_engaged=front
 def measure(self):
  f,r=self.engagement();return dict(engaged_front_links=f,engaged_rear_links=r,continuous_crank_and_chain_revolutions=self.clean_turns,intact=not self.failed,released_seconds=self.release,failed=self.failed)
 def reset_valid(self):
  front,rear=self.masks(self.chain_coordinates())
  # Two short crossings at the plate edge are not a wrapped/engaged chain.
  # Reject any initial arc of three consecutive rollers on the teeth.
  wrapped=any(front[i] and front[(i+1)%LINKS] and front[(i+2)%LINKS] for i in range(LINKS))
  return front.sum()<=6 and not wrapped and rear.sum()>=5 and not self.failed
 def score(self):
  if self.failed or self.broken:return 0.
  if self.clean_turns>=1 and self.release>=3:return 1.
  return .5 if self.clean_turns>=.5 else (.25 if self.clean_turns>=.25 else 0.)
 def state(self):
  return dict(super().state(),previous_angle=self.previous_angle,turn=self.turn,lo=self.lo,hi=self.hi,clean_turns=self.clean_turns,chain_turn=self.chain_turn,chain_lo=self.chain_lo,chain_hi=self.chain_hi,previous_link_angles=self.previous_link_angles,previous_engaged=self.previous_engaged)
 def restore(self,state):
  s=dict(state)
  for key in ['previous_link_angles','previous_engaged']:
   value=s.pop(key);setattr(self,key,None if value is None else np.asarray(value))
  super().restore(s)
