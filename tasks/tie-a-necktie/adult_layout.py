"""Standalone adult collar candidate; passive geometry, no cloth constraints.

This isolated probe keeps the earlier child-collar trials reproducible. The
1.45m tie starts untied and uncrossed, then settles under native gravity.
"""
import numpy as np
from pathlib import Path
from cloth_mesh import necktie

TABLE=.7475
NECK=(.40,0.,1.25)
NECK_RADIUS=.055
NECK_HEIGHT=.10
LENGTH=1.45
ARC_START=.83
DRAPE_RADIUS=.065


def make_mesh():
    # The native054 coarse mesh retained the band, but one5mm triangle cut
    # through the leading flap corner. Resolve the whole curved neckband and
    # adjacent bends at1.25mm longitudinal / about2.2mm across its width.
    # Geometry, material and collision thresholds are unchanged.
    s=np.r_[np.linspace(0.,.75,151),np.linspace(.75,1.12,297)[1:],np.linspace(1.12,LENGTH,67)[1:]]
    return necktie(length=LENGTH,columns=16,longitudinal_samples=s)


def fixture_geometry():
    # Physical open-front folded collar: the tie sits between neck and flap.
    result={
        'Neck':dict(kind='cylinder',center=NECK,radius=NECK_RADIUS,height=NECK_HEIGHT),
        'CollarRim':dict(kind='cylinder',center=(NECK[0],0.,1.2225),radius=.081,height=.005),
        'RearArm':dict(kind='box',center=(.495,0.,1.190),size=(.210,.025,.025)),
        'RearPost':dict(kind='box',center=(.590,0.,(TABLE+1.2025)/2),size=(.025,.025,1.2025-TABLE)),
        'Base':dict(kind='box',center=(.590,0.,TABLE+.006),size=(.180,.160,.012)),
    }
    # Tangential pieces form a semicircular rigid collar flap, open at front.
    # A lower flange and outer folded collar physically retain the neckband;
    # no attachment, world joint or hidden point constraint is introduced.
    # Leave a40degree opening at each front side. In056 the long flap's sharp
    # leading corner snagged an edge and stretched it40%; a real folded collar
    # opens ahead of the neckband bend, rather than acting as a full side wall.
    for i,a in enumerate(np.deg2rad(np.linspace(-70.,70.,15))):
        R=np.array(((np.cos(a),-np.sin(a),0.),(np.sin(a),np.cos(a),0.),(0.,0.,1.)))
        result[f'FoldedCollar{i:02d}']=dict(kind='box',center=(NECK[0]+.079*np.cos(a),.079*np.sin(a),1.25),size=(.003,.015,.06),rotation=R.tolist(),yaw_rad=float(a))
    return result


def initial_layout(mesh=None,*,inside_out=True):
    """Isometric loose drape, authored only before gravity settling.

    The long wide end curves around an empty region above the table to avoid
    an initially off-table tip. Its curve stays in a horizontal plane with a
    constant vertical cross-width: it creates no crossing, twist or knot.
    This is not the photographed task reset until natural settling is checked.
    """
    mesh=make_mesh() if mesh is None else mesh
    r=DRAPE_RADIUS;arc_end=ARC_START+np.pi*r
    p=np.empty_like(mesh.rest)
    for row in mesh.markers['row_nodes']:
        s=float(mesh.rest[row[len(row)//2],1])
        if s<ARC_START:
            t=ARC_START-s
            straight=.25;bend=.10
            if t<=straight:
                center=np.array((NECK[0]-t,-r,NECK[2]))
            elif t<=straight+np.pi*bend/2:
                a=(t-straight)/bend
                center=np.array((NECK[0]-straight-bend*np.sin(a),-r-bend*(1-np.cos(a)),NECK[2]))
            else:
                extra=t-straight-np.pi*bend/2
                center=np.array((NECK[0]-straight-bend,-r-bend-extra,NECK[2]))
        elif s>arc_end:
            center=np.array((NECK[0]-(s-arc_end),r,NECK[2]))
        else:
            a=(s-ARC_START)/r-np.pi/2
            center=np.array((NECK[0]+r*np.cos(a),r*np.sin(a),NECK[2]))
        p[row]=center+mesh.rest[row,0,None]*np.array((0.,0.,-1. if inside_out else 1.))
    return p


def settled_initial_layout(mesh=None,*,inside_out=True):
    """Source-authored gravity shape, used only by the shared scene reset.

    Native058 naturally settled this untied strip on the physical collar.
    Starting here avoids dropping a horizontal strip over the ready robot.
    This function is never called by a policy during an episode.
    """
    if not inside_out:raise ValueError('The measured adult reset is inside-out')
    mesh=make_mesh() if mesh is None else mesh
    with np.load(Path(__file__).with_name('adult-settled-reset.npz'),allow_pickle=False) as data:
        if mesh.rest.shape!=data['rest'].shape or not np.allclose(mesh.rest,data['rest'],rtol=0.,atol=1e-12) or not np.array_equal(mesh.faces,data['faces']):
            raise ValueError('Measured adult reset does not match the authored material mesh')
        points=data['positions'].copy()
    if points.shape!=mesh.rest.shape or not np.isfinite(points).all():raise ValueError('Invalid measured adult reset')
    return points


def author_collar(stage,path='/World/Collar'):
    from pxr import Gf,UsdGeom,UsdPhysics,PhysxSchema
    from native_cloth import author_box
    for name,spec in fixture_geometry().items():
        if spec['kind']=='box':
            box=author_box(stage,path+'/'+name,spec['size'],spec['center'],(.92,.92,.90) if name.startswith('Folded') else (.35,.35,.37))
            if 'yaw_rad' in spec:
                a=spec['yaw_rad'];box.AddOrientOp(UsdGeom.XformOp.PrecisionDouble).Set(Gf.Quatd(float(np.cos(a/2)),0.,0.,float(np.sin(a/2))))
            continue
        cylinder=UsdGeom.Cylinder.Define(stage,path+'/'+name)
        cylinder.CreateRadiusAttr(spec['radius']);cylinder.CreateHeightAttr(spec['height']);cylinder.CreateAxisAttr('Z')
        cylinder.AddTranslateOp().Set(Gf.Vec3d(*spec['center']))
        cylinder.CreateDisplayColorAttr([Gf.Vec3f(.92,.92,.90)])
        UsdPhysics.CollisionAPI.Apply(cylinder.GetPrim())
        collision=PhysxSchema.PhysxCollisionAPI.Apply(cylinder.GetPrim())
        collision.CreateContactOffsetAttr(.0005);collision.CreateRestOffsetAttr(0.)
    mark=UsdGeom.Sphere.Define(stage,path+'/CentreMark');mark.CreateRadiusAttr(.0015)
    mark.AddTranslateOp().Set(Gf.Vec3d(NECK[0]-NECK_RADIUS-.0001,0.,NECK[2]))
    mark.CreateDisplayColorAttr([Gf.Vec3f(.08,.08,.08)])
