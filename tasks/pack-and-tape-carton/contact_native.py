"""Contact-pressure/dwell -> passive breakable native adhesive constraints.

Must be stepped from real native contact sensors at each physics substep.
The controller has no bond/unbond API. No film/cardboard pose is ever written.
"""
import numpy as np
from pxr import UsdPhysics,Gf
from yam_arena.ik import matrix_to_quat_xyzw
from bond_geometry import width_contacts,PATCHES,dot
from model import TAPE_WIDTH
class NativeAdhesion:
 def __init__(self,stage,parent):self.stage=stage;self.parent=parent;self.dwell={};self.bonds={};self.broken=set()
 def step(self,dt,films,targets,contact_forces):
  if not 0<dt<=1/120:raise ValueError('adhesion requires physics substep telemetry')
  # contact_forces[(film,target)] is a measured filtered native force vector,
  # never a controller-specified pressure or a tool proximity proxy.
  for fn,film in films.items():
   for tn,target in targets.items():
    key=(fn,tn)
    if key in self.broken:continue
    if key in self.bonds:
     b=self.bonds[key];a=np.array(target['pos'])+np.array(target['rotation'])@b['target_anchor'];p=np.array(film['pos'])+np.array(film['rotation'])@b['film_anchor'];separation=float(np.linalg.norm(a-p));b['separation']=separation
     if separation>.001:
      b['joint'].GetJointEnabledAttr().Set(False);self.broken.add(key)
     continue
    hits=width_contacts(film,target);force=contact_forces.get(key,(0.,0.,0.));valid=bool(hits) and dot(force,hits[0][2])>=.5
    self.dwell[key]=self.dwell.get(key,0.)+dt if valid else 0.
    if self.dwell[key]+1e-12<.1:continue
    point=np.mean([p for _,p,_ in hits],axis=0);rf=np.array(film['rotation']);rt=np.array(target['rotation']);fa=rf.T@(point-np.array(film['pos']));ta=rt.T@(point-np.array(target['pos']));q=matrix_to_quat_xyzw(rt.T@rf)
    j=UsdPhysics.FixedJoint.Define(self.stage,self.parent+'/'+fn+'/adhesion_'+tn);j.CreateBody0Rel().SetTargets([self.parent+'/'+tn]);j.CreateBody1Rel().SetTargets([self.parent+'/'+fn]);j.CreateLocalPos0Attr(Gf.Vec3f(*ta));j.CreateLocalPos1Attr(Gf.Vec3f(*fa));j.CreateLocalRot0Attr(Gf.Quatf(float(q[3]),Gf.Vec3f(*q[:3])));fraction=len(hits)/PATCHES;j.CreateBreakForceAttr(2.*fraction);j.CreateBreakTorqueAttr(.008*fraction);j.CreateExcludeFromArticulationAttr(True);j.CreateCollisionEnabledAttr(False)
    self.bonds[key]={'joint':j,'width_bins':{k for k,_,_ in hits},'target_anchor':ta,'film_anchor':fa,'separation':0.}
 def bonded_width(self,film):
  bins=set()
  for key,b in self.bonds.items():
   if key[0]==film and key not in self.broken and b['separation']<=.001:bins|=b['width_bins']
  return len(bins)/PATCHES*TAPE_WIDTH
