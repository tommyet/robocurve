"""Candidate complete prop layout. YAM integration and reach remain unvalidated."""
import numpy as np
from cloth_mesh import tshirt
from native_cloth import Fabric

TABLE=.7475
LINE_X=.52
LINE_Z=1.09
LINE_HALF_SPAN=.25


def initial_layout(mesh=None):
    mesh=tshirt() if mesh is None else mesh
    p=mesh.rest
    return np.column_stack((.18+p[:,1],-p[:,0],TABLE+.003+p[:,2]))


def author_rack(stage,path='/World/Rack'):
    from pxr import Gf,UsdGeom,UsdPhysics,PhysxSchema
    from native_cloth import author_box
    UsdGeom.Xform.Define(stage,path)
    line=UsdGeom.Cylinder.Define(stage,path+'/Clothesline')
    line.CreateRadiusAttr(.0015)
    line.CreateHeightAttr(2*LINE_HALF_SPAN)
    line.CreateAxisAttr('Y')
    line.AddTranslateOp().Set(Gf.Vec3d(LINE_X,0.,LINE_Z))
    line.CreateDisplayColorAttr([Gf.Vec3f(.78,.78,.78)])
    UsdPhysics.CollisionAPI.Apply(line.GetPrim())
    cp=PhysxSchema.PhysxCollisionAPI.Apply(line.GetPrim())
    cp.CreateContactOffsetAttr(.0005)
    cp.CreateRestOffsetAttr(0.)
    for sign in (-1,1):
        label='Left' if sign>0 else 'Right'
        author_box(stage,path+'/'+label+'Post',(.025,.025,LINE_Z-TABLE),
                   (LINE_X,sign*(LINE_HALF_SPAN+.0125),(LINE_Z+TABLE)/2),(.35,.35,.37))
        author_box(stage,path+'/'+label+'Foot',(.15,.07,.015),
                   (LINE_X,sign*(LINE_HALF_SPAN+.0125),TABLE+.0075),(.35,.35,.37))
    return line


def author_props(stage):
    from native_cloth import author_cloth,author_peg
    mesh=tshirt()
    author_cloth(stage,'/World/Tshirt',mesh,Fabric(),points=initial_layout(mesh))
    author_rack(stage)
    for sign in (-1,1):
        label='Left' if sign>0 else 'Right'
        author_peg(stage,'/World/'+label+'Peg',pos=(.12,sign*.20,TABLE+.014),
                   fixed_lower=False,spring=True,open_angle=0.)
    return mesh
