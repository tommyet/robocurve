"""Native articulated flexible-lock approximation and a physical dryer slider.

Coarse rigid capsules connected with passive bending joints. No fixed painted
hair sheet, no scripted lock animation and no state-driven drying shortcuts.
"""
from pathlib import Path
from pxr import Usd,UsdGeom,UsdPhysics,PhysxSchema,Gf
from config import *

def collider(g):
 UsdPhysics.CollisionAPI.Apply(g.GetPrim());a=PhysxSchema.PhysxCollisionAPI.Apply(g.GetPrim());a.CreateContactOffsetAttr(.00015);a.CreateRestOffsetAttr(0.)
def box(s,p,size,pos,color):
 c=UsdGeom.Cube.Define(s,p);c.CreateSizeAttr(1.);c.AddTranslateOp().Set(Gf.Vec3d(*pos));c.AddScaleOp().Set(Gf.Vec3f(*size));c.CreateDisplayColorAttr([Gf.Vec3f(*color)]);collider(c);return c
def export(path,name):
 s=Usd.Stage.CreateNew(str(path));UsdGeom.SetStageMetersPerUnit(s,1.);UsdGeom.SetStageUpAxis(s,'Z');r=UsdGeom.Xform.Define(s,'/Object');s.SetDefaultPrim(r.GetPrim())
 if name=='head':
  c=UsdGeom.Sphere.Define(s,'/Object/scalp');c.CreateRadiusAttr(HEAD_RADIUS);c.CreateDisplayColorAttr([Gf.Vec3f(.75,.55,.42)]);collider(c)
  box(s,'/Object/neck',(.038,.045,.13),(0,0,-.11),(.75,.55,.42));box(s,'/Object/mount',(.11,.11,.11),(0,0,TOP+.055-HEAD[2]),(.3,.32,.35))
  nose=UsdGeom.Sphere.Define(s,'/Object/nose');nose.CreateRadiusAttr(.01);nose.AddTranslateOp().Set(Gf.Vec3d(-.065,0,0));nose.CreateDisplayColorAttr([Gf.Vec3f(.75,.55,.42)]);collider(nose)
 else:
  UsdPhysics.RigidBodyAPI.Apply(r.GetPrim());mass=.48 if name=='dryer' else .003 if name=='switch' else DRY_MASS_PER_SEGMENT+PATCHES_PER_SEGMENT*WATER_PER_PATCH
  UsdPhysics.MassAPI.Apply(r.GetPrim()).CreateMassAttr(mass)
  if name=='dryer':
   c=UsdGeom.Cylinder.Define(s,'/Object/motor');c.CreateRadiusAttr(.029);c.CreateHeightAttr(.09);c.CreateAxisAttr('X');c.CreateDisplayColorAttr([Gf.Vec3f(.85,.035,.19)]);collider(c)
   c=UsdGeom.Cylinder.Define(s,'/Object/nozzle');c.CreateRadiusAttr(.018);c.CreateHeightAttr(.045);c.CreateAxisAttr('X');c.AddTranslateOp().Set(Gf.Vec3d(.065,0,0));c.CreateDisplayColorAttr([Gf.Vec3f(.12,.14,.17)]);collider(c)
   box(s,'/Object/handle',(.030,.026,.085),(-.019,0,-.065),(.85,.035,.19))
  elif name=='switch':box(s,'/Object/slider',(.006,.013,.014),(0,0,0),(.06,.07,.08))
  else:
   c=UsdGeom.Capsule.Define(s,'/Object/lock');c.CreateRadiusAttr(RADIUS);c.CreateHeightAttr(LENGTH-2*RADIUS);c.CreateAxisAttr('Z');c.CreateDisplayColorAttr([Gf.Vec3f(.055,.025,.012)]);collider(c)
 s.GetRootLayer().Save();return str(Path(path).resolve())
def install_joints(s,parent):
 for k in range(LOCKS):
  for n in range(SEGMENTS):
   child=f'{parent}/hair_{k}_{n}'
   j=UsdPhysics.RevoluteJoint.Define(s,child+'/bend');j.CreateBody1Rel().SetTargets([child]);j.CreateAxisAttr('X' if (k+n)%2 else 'Y');j.CreateExcludeFromArticulationAttr(True);j.CreateCollisionEnabledAttr(False)
   if n:
    j.CreateBody0Rel().SetTargets([f'{parent}/hair_{k}_{n-1}']);j.CreateLocalPos0Attr(Gf.Vec3f(0,0,-LENGTH/2))
   else:j.CreateLocalPos0Attr(Gf.Vec3f(*root(k)))
   j.CreateLocalPos1Attr(Gf.Vec3f(0,0,LENGTH/2));j.CreateLowerLimitAttr(-70.);j.CreateUpperLimitAttr(70.)
   d=UsdPhysics.DriveAPI.Apply(j.GetPrim(),'angular');d.CreateTypeAttr('force');d.CreateTargetPositionAttr(0.);d.CreateStiffnessAttr(.00012);d.CreateDampingAttr(.000015)
 # A frictional slide switch, not a software timer or a controller power flag.
 j=UsdPhysics.PrismaticJoint.Define(s,parent+'/dryer/power_slider');j.CreateBody0Rel().SetTargets([parent+'/dryer']);j.CreateBody1Rel().SetTargets([parent+'/switch']);j.CreateAxisAttr('Z');j.CreateLocalPos0Attr(Gf.Vec3f(-.037,0,-.055));j.CreateLocalPos1Attr(Gf.Vec3f(0,0,0));j.CreateLowerLimitAttr(0.);j.CreateUpperLimitAttr(SWITCH_TRAVEL);j.CreateCollisionEnabledAttr(False);j.CreateExcludeFromArticulationAttr(True)
 PhysxSchema.PhysxJointAPI.Apply(j.GetPrim()).CreateJointFrictionAttr(.08)
