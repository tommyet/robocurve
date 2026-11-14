"""Rigid compound aerosol geometry and native joints; import after Kit starts.

Cap retention is a spring-detent approximation: a 4 mm axial pull releases
the guide joint. No object pose is changed. The real snap-fit is not modelled.
"""
import math
from pathlib import Path
from pxr import Gf, Usd, UsdGeom, UsdPhysics, PhysxSchema
from config import CAN_COLOR,CAP_COLOR


def collider(shape):
    prim = shape.GetPrim()
    UsdPhysics.CollisionAPI.Apply(prim)
    api = PhysxSchema.PhysxCollisionAPI.Apply(prim)
    api.CreateContactOffsetAttr(.0003)
    api.CreateRestOffsetAttr(0.)


def box(stage,path,size,pos,color,collision=True,angle=0.):
    obj=UsdGeom.Cube.Define(stage,path)
    obj.CreateSizeAttr(1.)
    obj.AddTranslateOp().Set(Gf.Vec3d(*pos))
    obj.AddRotateZOp().Set(angle)
    obj.AddScaleOp().Set(Gf.Vec3f(*size))
    obj.CreateDisplayColorAttr([Gf.Vec3f(*color)])
    if collision: collider(obj)
    return obj


def cylinder(stage,path,radius,height,pos,color):
    obj=UsdGeom.Cylinder.Define(stage,path)
    obj.CreateRadiusAttr(radius);obj.CreateHeightAttr(height)
    obj.CreateAxisAttr('Z');obj.AddTranslateOp().Set(Gf.Vec3d(*pos))
    obj.CreateDisplayColorAttr([Gf.Vec3f(*color)])
    collider(obj)
    return obj


def asset(path,kind):
    stage=Usd.Stage.CreateNew(str(path))
    UsdGeom.SetStageMetersPerUnit(stage,1.)
    UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.z)
    root=UsdGeom.Xform.Define(stage,'/Object');stage.SetDefaultPrim(root.GetPrim())
    UsdPhysics.RigidBodyAPI.Apply(root.GetPrim())
    PhysxSchema.PhysxContactReportAPI.Apply(root.GetPrim()).CreateThresholdAttr(0.)
    UsdPhysics.MassAPI.Apply(root.GetPrim()).CreateMassAttr(
        {'spray_can':.25,'cap':.018,'button':.003}[kind])
    if kind=='spray_can':
        body=cylinder(stage,'/Object/body',.026,.13,(0.,0.,-.005),CAN_COLOR)
        # Finite finger-pad contact can resist twist about a pinch line.
        # Zero-radius point friction otherwise makes the cylindrical can an
        # unintended frictionless roller under the off-centre nozzle load.
        # 3 mm radius is smaller than the actual finger-pad face, uncalibrated.
        patch=PhysxSchema.PhysxCollisionAPI.Apply(body.GetPrim())
        patch.CreateTorsionalPatchRadiusAttr(.003)
        patch.CreateMinTorsionalPatchRadiusAttr(.0015)
        cylinder(stage,'/Object/shoulder',.023,.01,(0.,0.,.065),(.65,.65,.67))
        # No fake grip handles. The second gripper presses the real moving button.
    elif kind=='cap':
        cylinder(stage,'/Object/lid',.030,.002,(0.,0.,.016),CAP_COLOR)
        # Hollow cap: compound ring, not a solid cylinder intersecting the nozzle.
        for i in range(24):
            angle=2*math.pi*i/24
            box(stage,f'/Object/wall_{i}',(.003,.008,.032),
                (.0285*math.cos(angle),.0285*math.sin(angle),-.001),
                CAP_COLOR,angle=math.degrees(angle))
    else:
        cylinder(stage,'/Object/button',.009,.010,(0.,0.,0.),(.9,.9,.9))
        box(stage,'/Object/outlet',(.001,.004,.003),(.0092,0.,0.),(.05,.05,.05),False)
    stage.GetRootLayer().Save()
    return str(Path(path).resolve())


def stand_asset(path):
    """Ordinary steel display/painting stand with feet, posts and braces."""
    stage=Usd.Stage.CreateNew(str(path));UsdGeom.SetStageMetersPerUnit(stage,1.)
    UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.z)
    root=UsdGeom.Xform.Define(stage,'/Stand');stage.SetDefaultPrim(root.GetPrim())
    color=(.18,.24,.28)
    def beam(name,a,b,width=.014,depth=.014):
        direction=Gf.Vec3d(*[v-u for u,v in zip(a,b)])
        c=UsdGeom.Cube.Define(stage,'/Stand/'+name);c.CreateSizeAttr(1.)
        c.AddTranslateOp().Set(Gf.Vec3d(*[(u+v)/2 for u,v in zip(a,b)]))
        q=Gf.Rotation(Gf.Vec3d(0,0,1),direction).GetQuat()
        c.AddOrientOp().Set(Gf.Quatf(float(q.GetReal()),Gf.Vec3f(*q.GetImaginary())))
        c.AddScaleOp().Set(Gf.Vec3f(width,depth,direction.GetLength()))
        c.CreateDisplayColorAttr([Gf.Vec3f(*color)]);collider(c)
    for side,y in [('left',.13),('right',-.13)]:
        box(stage,'/Stand/'+side+'_foot',(.12,.026,.006),(0.,y,.003),color)
        beam(side+'_post',(0.,y,.006),(0.,y,.45),.018,.018)
        beam(side+'_brace',(.052,y,.006),(0.,y,.33),.010,.010)
        for z in (.13,.35):beam(side+'_mount_'+str(round(z*1000)),(-.047,y,z),(0.,y,z),.015,.015)
    beam('crossbar',(0.,-.13,.35),(0.,.13,.35),.018,.018)
    stage.GetRootLayer().Save();return str(Path(path).resolve())


def joints(stage,can,cap,button,cap_attached=True):
    definitions=(
        (can+'/cap_guide',cap,.087,0.,.012,1800.,1.),
        (can+'/button_slide',button,.077,-.003,0.,2200.,1.),
    )
    for path,body,z,lo,hi,stiffness,damping in (definitions if cap_attached else definitions[1:]):
        joint=UsdPhysics.PrismaticJoint.Define(stage,path)
        joint.CreateBody0Rel().SetTargets([can]);joint.CreateBody1Rel().SetTargets([body])
        joint.CreateAxisAttr('Z')
        joint.CreateLocalPos0Attr(Gf.Vec3f(0.,0.,z))
        joint.CreateLocalPos1Attr(Gf.Vec3f(0.,0.,0.))
        joint.CreateLowerLimitAttr(lo);joint.CreateUpperLimitAttr(hi)
        joint.CreateExcludeFromArticulationAttr(True)
        joint.CreateCollisionEnabledAttr(False)
        drive=UsdPhysics.DriveAPI.Apply(joint.GetPrim(),'linear')
        drive.CreateTypeAttr('force');drive.CreateTargetPositionAttr(0.)
        drive.CreateStiffnessAttr(stiffness);drive.CreateDampingAttr(damping)
    # The guide disables can/cap collision until released; cap/button remains
    # collidable so the closed lid physically prevents pressing the nozzle.
