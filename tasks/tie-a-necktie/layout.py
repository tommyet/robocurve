"""Untied necktie reset layout and fixed collar geometry, in SI units.

The tie starts draped around the collar with two uncrossed ends. This geometry
is authored once before physics and must settle honestly; no prescribed knot
or per-step cloth motion is provided by this module.
"""
import numpy as np
from cloth_mesh import necktie,edge_strain

TABLE=.7475
NECK=(.50,0.,1.12)
NECK_RADIUS=.055
NECK_HEIGHT=.065


def fixture_geometry():
    """Exact solid dimensions shared by authoring and the CPU clearance audit."""
    return {
        'Neck':dict(kind='cylinder',center=NECK,radius=NECK_RADIUS,height=NECK_HEIGHT),
        'Post':dict(kind='box',size=(.025,.025,NECK[2]-TABLE),
                    center=(NECK[0],0.,(NECK[2]+TABLE)/2)),
        'Base':dict(kind='box',size=(.18,.16,.012),center=(NECK[0],0.,TABLE+.006)),
        'LeftPoint':dict(kind='box',size=(.008,.035,.055),center=(.441,.039,1.096)),
        'RightPoint':dict(kind='box',size=(.008,.035,.055),center=(.441,-.039,1.096)),
    }


def face_colors(mesh):
    """Asymmetric edge marks make the visible wide-end face check unambiguous.

    With the wide tip down, the front face has a pale left edge and gold right
    edge. The back reverses that pattern. These are colours on material nodes,
    not added rigid markers or geometry updates during the episode.
    """
    colours=np.tile((.50,.08,.17),(len(mesh.rest),1))
    for row in mesh.markers['row_nodes'][1:-1]:
        colours[row[0]]=(.92,.92,.88)
        colours[row[-1]]=(.85,.63,.12)
    return colours


def initial_layout(mesh=None):
    """Isometric diagnostic drape, not yet the task's settled reset state.

    A half-cylinder at the back of the form joins two uncrossed free ends.
    Gravity must create the hanging configuration in the probe. The initially
    horizontal ends are explicitly not presented as a photographed task setup.
    Freeze and audit a naturally settled configuration only after GPU evidence.
    """
    mesh=necktie() if mesh is None else mesh
    r=.065
    arc_start=.58
    arc_end=arc_start+np.pi*r
    current=np.empty_like(mesh.rest)
    for row in mesh.markers['row_nodes']:
        s=float(mesh.rest[row[len(row)//2],1])
        if s < arc_start:
            center=np.array((NECK[0]+s-arc_start,-r,NECK[2]))
        elif s > arc_end:
            center=np.array((NECK[0]-(s-arc_end),r,NECK[2]))
        else:
            theta=(s-arc_start)/r-np.pi/2
            center=np.array((NECK[0]+r*np.cos(theta),r*np.sin(theta),NECK[2]))
        current[row]=center+mesh.rest[row,0,None]*np.array((0.,0.,1.))
    return current


def author_collar(stage,path='/World/Collar'):
    """Rigid collar form, with a 110 mm neck and two shirt-collar points."""
    from pxr import Gf,UsdGeom,UsdPhysics,PhysxSchema
    from native_cloth import author_box
    fixtures=fixture_geometry()
    neck=fixtures['Neck']
    cylinder=UsdGeom.Cylinder.Define(stage,path+'/Neck')
    cylinder.CreateRadiusAttr(neck['radius'])
    cylinder.CreateHeightAttr(neck['height'])
    cylinder.CreateAxisAttr('Z')
    cylinder.AddTranslateOp().Set(Gf.Vec3d(*neck['center']))
    cylinder.CreateDisplayColorAttr([Gf.Vec3f(.82,.80,.75)])
    UsdPhysics.CollisionAPI.Apply(cylinder.GetPrim())
    collision=PhysxSchema.PhysxCollisionAPI.Apply(cylinder.GetPrim())
    collision.CreateContactOffsetAttr(.0005)
    collision.CreateRestOffsetAttr(0.)
    # A small painted centre mark is visual only; it does not alter contact.
    mark=UsdGeom.Sphere.Define(stage,path+'/CentreMark')
    mark.CreateRadiusAttr(.0015)
    mark.AddTranslateOp().Set(Gf.Vec3d(NECK[0]-NECK_RADIUS-.0001,0.,NECK[2]))
    mark.CreateDisplayColorAttr([Gf.Vec3f(.08,.08,.08)])
    # Central support stays inside the neck footprint, clear of the rear drape.
    for name,spec in fixtures.items():
        if name=='Neck':continue
        color=(.92,.92,.90) if name.endswith('Point') else (.35,.35,.37)
        author_box(stage,path+'/'+name,spec['size'],spec['center'],color)
    return cylinder
