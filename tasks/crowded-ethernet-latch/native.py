"""Actual passive native retention and flexible rigid-link cable approximation.

No latch release flags, body pose writes, distance-triggered welds or software
retention forces. Joined latch/plug contact is disabled because the compliant
clip is represented by a spring slider rather than a bending plastic beam.
"""
import math
from pathlib import Path
from pxr import Usd,UsdGeom,UsdPhysics,PhysxSchema,Gf
from config import *

def collider(shape):
    UsdPhysics.CollisionAPI.Apply(shape.GetPrim())
    c=PhysxSchema.PhysxCollisionAPI.Apply(shape.GetPrim());c.CreateContactOffsetAttr(.0001);c.CreateRestOffsetAttr(0.)

def cube(stage,path,size,pos,color):
    c=UsdGeom.Cube.Define(stage,path);c.CreateSizeAttr(1.)
    c.AddTranslateOp().Set(Gf.Vec3d(*pos));c.AddScaleOp().Set(Gf.Vec3f(*size));c.CreateDisplayColorAttr([Gf.Vec3f(*color)]);collider(c)
    return c

def wedge(stage,path,color):
    # Leading +x face slopes down; trailing -x face retains against the ledge.
    m=UsdGeom.Mesh.Define(stage,path)
    v=[(.006,y,.0005) for y in [-.0025,.0025]]+[(.006,y,.0025) for y in [-.0025,.0025]]+[(.010,y,.0005) for y in [-.0025,.0025]]
    m.CreatePointsAttr([Gf.Vec3f(*p) for p in v]);faces=[[0,1,3,2],[0,4,5,1],[2,3,5,4],[0,2,4],[1,5,3]]
    m.CreateFaceVertexCountsAttr([len(f) for f in faces]);m.CreateFaceVertexIndicesAttr([i for f in faces for i in f]);m.CreateSubdivisionSchemeAttr('none');m.CreateDisplayColorAttr([Gf.Vec3f(*color)])
    collider(m);UsdPhysics.MeshCollisionAPI.Apply(m.GetPrim()).CreateApproximationAttr('convexHull')

def export(path,name):
    stage=Usd.Stage.CreateNew(str(path));UsdGeom.SetStageMetersPerUnit(stage,1.);UsdGeom.SetStageUpAxis(stage,'Z')
    root=UsdGeom.Xform.Define(stage,'/Object');stage.SetDefaultPrim(root.GetPrim())
    color=(.82,.86,.88)
    if name=='switch':
        # Real open cavities with separate surfaces, not painted sockets.
        case_back=.3985+PANEL_DEPTH;case_z=(.95-.0055+.95+PITCH_Z+.0078)/2
        cube(stage,'/Object/back',(.012,PANEL_WIDTH,PANEL_HEIGHT),(case_back-.006,0,case_z),(.55,.59,.63))
        post_height=case_z-TOP-.012
        cube(stage,'/Object/post',(.020,.045,post_height),(case_back-.003,0,TOP+.012+post_height/2),(.25,.28,.31))
        cube(stage,'/Object/foot',(.095,.135,.012),(case_back-.005,0,TOP+.006),(.25,.28,.31))
        for i in range(8):
            _,y,z=port(i)
            cube(stage,f'/Object/floor_{i}',(.027,.015,.001),(.412,y,z-.005),color)
            cube(stage,f'/Object/roof_{i}',(.027,.015,.001),(.412,y,z+.0073),color)
            for sign in [-1,1]:
                cube(stage,f'/Object/side_{i}_{"p" if sign>0 else "m"}',(.027,.002,.0133),(.412,y+sign*.0075,z+.00115),color)
            cube(stage,f'/Object/ledge_{i}',(.002,.0055,.002),(.408,y,z+.006),color)
            cube(stage,f'/Object/contact_{i}',(.003,.010,.006),(case_back-.004,y,z-.001),(.76,.59,.18))
    else:
        UsdPhysics.RigidBodyAPI.Apply(root.GetPrim())
        mass=.0003 if name.startswith('clip') else .008 if name.startswith('plug') else .001
        UsdPhysics.MassAPI.Apply(root.GetPrim()).CreateMassAttr(mass)
        PhysxSchema.PhysxContactReportAPI.Apply(root.GetPrim()).CreateThresholdAttr(0.)
        if name.startswith('plug'):
            i=int(name.split('_')[1]);col=(1.,.38,.025) if i==SERVICE else (.05,.36,.75)
            cube(stage,'/Object/shell',(.024,.012,.005),(0,0,-.0015),color)
            for sign in [-1,1]:cube(stage,f'/Object/shoulder_{"p" if sign>0 else "m"}',(.014,.0025,.003),(.003,sign*.00475,.0025),color)
            boot=UsdGeom.Cylinder.Define(stage,'/Object/boot');boot.CreateRadiusAttr(.0035);boot.CreateHeightAttr(.014);boot.CreateAxisAttr('X');boot.AddTranslateOp().Set(Gf.Vec3d(-.0205,0,-.0005));boot.CreateDisplayColorAttr([Gf.Vec3f(*col)]);collider(boot)
        elif name.startswith('clip'):
            cube(stage,'/Object/tab',(.020,.005,.001),(-.003,0,0),color);wedge(stage,'/Object/hook',color)
        else:
            _,i,k=name.split('_');i=int(i);k=int(k);points=cable_points(i);a,b=points[k:k+2]
            delta=Gf.Vec3d(*[v-u for u,v in zip(a,b)])
            c=UsdGeom.Capsule.Define(stage,'/Object/cable');c.CreateRadiusAttr(CABLE_RADIUS);c.CreateHeightAttr(delta.GetLength());c.CreateAxisAttr('Z')
            q=Gf.Rotation(Gf.Vec3d(0,0,1),delta).GetQuat();c.AddOrientOp().Set(Gf.Quatf(q.GetReal(),Gf.Vec3f(*q.GetImaginary())))
            c.CreateDisplayColorAttr([Gf.Vec3f(*((1.,.38,.025) if i==SERVICE else ((.02,.4,.8) if i%2 else (.03,.58,.28))))]);collider(c)
    stage.GetRootLayer().Save();return str(Path(path).resolve())

def install_joints(stage,parent):
    for i in USED:
        plug=f'{parent}/plug_{i}';clip=f'{parent}/clip_{i}'
        j=UsdPhysics.PrismaticJoint.Define(stage,plug+'/clip_spring');j.CreateBody0Rel().SetTargets([plug]);j.CreateBody1Rel().SetTargets([clip]);j.CreateAxisAttr('Z');j.CreateLocalPos0Attr(Gf.Vec3f(0,0,CLIP_Z));j.CreateLocalPos1Attr(Gf.Vec3f(0,0,0));j.CreateLowerLimitAttr(-CLIP_TRAVEL);j.CreateUpperLimitAttr(0.);j.CreateCollisionEnabledAttr(False);j.CreateExcludeFromArticulationAttr(True)
        d=UsdPhysics.DriveAPI.Apply(j.GetPrim(),'linear');d.CreateTypeAttr('force');d.CreateTargetPositionAttr(0.);d.CreateStiffnessAttr(CLIP_STIFFNESS);d.CreateDampingAttr(.04)
        points=cable_points(i)
        for k in range(LINKS):
            b=f'{parent}/wire_{i}_{k}';a=plug if k==0 else f'{parent}/wire_{i}_{k-1}'
            j=UsdPhysics.SphericalJoint.Define(stage,b+'/bend');j.CreateBody0Rel().SetTargets([a]);j.CreateBody1Rel().SetTargets([b]);j.CreateExcludeFromArticulationAttr(True);j.CreateCollisionEnabledAttr(False)
            anchor=points[k]
            center_a=port(i) if k==0 else tuple((u+v)/2 for u,v in zip(points[k-1],points[k]))
            center_b=tuple((u+v)/2 for u,v in zip(points[k],points[k+1]))
            j.CreateLocalPos0Attr(Gf.Vec3f(*[u-v for u,v in zip(anchor,center_a)]));j.CreateLocalPos1Attr(Gf.Vec3f(*[u-v for u,v in zip(anchor,center_b)]));j.CreateConeAngle0LimitAttr(35.);j.CreateConeAngle1LimitAttr(35.)
            PhysxSchema.PhysxJointAPI.Apply(j.GetPrim()).CreateJointFrictionAttr(.0002)
