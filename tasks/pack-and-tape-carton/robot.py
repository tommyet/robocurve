"""Ordinary robot pickup/place prefix, no product or carton pose writes."""
import numpy as np
from yam_arena.demo import ArmPlan,Waypoint as W
from yam_arena.constants import FINGER_OPEN
from config import *
class ProductsProbe:
 def __init__(self,env):
  self.env=env;self.previous=env._ready.detach().cpu().numpy().reshape(-1).copy();O=FINGER_OPEN;path=[];travel=TOP+.16
  for (name,p,size,mass,color),target in zip(PRODUCTS,[(.275,0.),(.365,0.)]):
   x,y,z=p;grip=-.0185 if name=='product_a' else -.0135
   path += [W(1.5,(x,y,travel),O),W(2.,(x,y,z+.008),O),W(1.,(x,y,z+.008),grip),W(2.,(x,y,travel),grip),W(3.,(*target,travel),grip),W(2.,(*target,TOP+.039),grip),W(1.,(*target,TOP+.039),O),W(2.,(*target,travel),O)]
  path += [W(3.,(.13,.24,TOP+.17),O)]
  self.plan=ArmPlan(path,env.rig.bases['left']);self.park=ArmPlan([W(3.,(.13,-.24,TOP+.17),O)],env.rig.bases['right']);self.duration=self.plan.duration
 def command(self,t):
  a,phase=self.plan.action7(t+.05);b,_=self.park.action7(t+.05);out=np.r_[a,b];delta=np.array([.04]*6+[.05]+[.04]*6+[.05]);out=np.clip(out,self.previous-delta,self.previous+delta);out=np.clip(out,self.env._low,self.env._high);self.previous=out
  return out,{'phase':'pack_products' if t<self.duration else 'hold_packed','ik_error_m':self.plan.worst_ik_mm/1000,'ik_error_deg':self.plan.worst_ik_deg}
