"""Full-size flexible-paper scene, awaiting coupled native validation.

A low document support leaves the far sheet edges accessible. The staple is
free: no crown fixture, pins or automatic material release. A rigid forked
lever remover must act through collisions and its tabletop fulcrum.
"""
import math
import numpy as np
from paper import perforated_sheet
from native_paper import author_paper,author_staple


TABLE_TOP=.7475
SUPPORT_TOP=TABLE_TOP+.020
SHEET_CENTRES=((.32,0.),(.32,.012))
STAPLE_XY=(.227,-.050)
PAPER_TOP=SUPPORT_TOP+.0009
SHEET_GAP=.00012
CROWN_GAP=.00002
PAPER_CENTRE_HEIGHTS=(PAPER_TOP-.00005-CROWN_GAP-SHEET_GAP,
                      PAPER_TOP-.00005-CROWN_GAP)


def paper_mesh(index):
    cx,cy=SHEET_CENTRES[index]
    holes=[(STAPLE_XY[0]-cx,STAPLE_XY[1]+side*.0064-cy) for side in (-1,1)]
    return perforated_sheet(size=(.21,.148),centers=holes,hole_size=(.00062,.00042),spacing=.008)


def build_scene(stage,root='/StapleTask', *, include_table=True, include_papers=True):
    from pxr import Gf,PhysxSchema,UsdGeom,UsdPhysics,Vt
    UsdGeom.Xform.Define(stage,root)
    def collision(prim):
        UsdPhysics.CollisionAPI.Apply(prim)
        p=PhysxSchema.PhysxCollisionAPI.Apply(prim)
        p.CreateContactOffsetAttr(.000002);p.CreateRestOffsetAttr(0.)
    def box(path,center,size,color):
        g=UsdGeom.Cube.Define(stage,path);g.CreateSizeAttr(1.)
        g.AddTranslateOp().Set(Gf.Vec3d(*map(float,center)))
        g.AddScaleOp().Set(Gf.Vec3f(*map(float,size)))
        g.CreateDisplayColorAttr([Gf.Vec3f(*color)]);collision(g.GetPrim());return g
    if include_table:box(root+'/table',(.3,0.,TABLE_TOP-.02),(1.,1.,.04),(.25,.24,.22))
    # Top surface supports the staple and tool fulcrum. Far edges overhang by
    # 20 mm (lower sheet) and 32 mm (upper), without any paper attachment.
    box(root+'/document_support',(.32,-.010,TABLE_TOP+.010),(.21,.128,.020),(.28,.31,.34))
    meshes=[paper_mesh(i) for i in range(2)]
    paths=[]
    for i,(mesh,(x,y)) in enumerate(zip(meshes,SHEET_CENTRES)):
        path=f'{root}/paper_{i}';paths.append(path)
        if include_papers:author_paper(stage,path,mesh,(x,y,PAPER_CENTRE_HEIGHTS[i]))
    staple=author_staple(stage,root+'/staple',origin=(*STAPLE_XY,PAPER_TOP),yaw=math.pi/2,fixed_crown=False)
    tool=root+'/remover'
    xf=UsdGeom.Xform.Define(stage,tool)
    xf.AddTranslateOp().Set(Gf.Vec3d(.28,-.20,TABLE_TOP+.003))
    p=xf.GetPrim();UsdPhysics.RigidBodyAPI.Apply(p);UsdPhysics.MassAPI.Apply(p).CreateMassAttr(.045)
    rb=PhysxSchema.PhysxRigidBodyAPI.Apply(p);rb.CreateEnableCCDAttr(True)
    rb.CreateSleepThresholdAttr(0.);rb.CreateSolverPositionIterationCountAttr(128);rb.CreateSolverVelocityIterationCountAttr(4)
    box(tool+'/grip',(0.,-.043,.005),(.018,.080,.016),(.14,.30,.42))
    box(tool+'/heel',(0.,-.004,0.),(.015,.006,.006),(.6,.62,.65))
    # Two sharpened steel wedges approach from below the crown. Full collision
    # geometry remains active; paper deformation and crown bending are causal.
    for side in (-1,1):
        x=side*.0046;half=.0012
        profile=np.array(((-.004,-.003),(.025,0.),(.025,.00005),(-.004,.003)))
        vertices=np.asarray([(x+offset,y,z) for offset in (-half,half) for y,z in profile])
        faces=np.array(((0,3,2),(0,2,1),(4,5,6),(4,6,7),(0,1,5),(0,5,4),
                        (1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)))
        g=UsdGeom.Mesh.Define(stage,tool+('/fork_left' if side<0 else '/fork_right'))
        g.CreatePointsAttr(Vt.Vec3fArray(vertices.tolist()));g.CreateFaceVertexCountsAttr([3]*len(faces))
        g.CreateFaceVertexIndicesAttr(faces.ravel().tolist());g.CreateSubdivisionSchemeAttr('none')
        g.CreateDisplayColorAttr([Gf.Vec3f(.65,.67,.70)]);collision(g.GetPrim())
        UsdPhysics.MeshCollisionAPI.Apply(g.GetPrim()).CreateApproximationAttr('convexHull')
    return dict(root=root,paper_paths=paths,paper_meshes=meshes,staple=staple,remover_path=tool,
                support_top_m=SUPPORT_TOP,initial_paper_top_m=PAPER_TOP-CROWN_GAP,staple_xy_m=list(STAPLE_XY),
                initial_sheet_midplane_gap_m=SHEET_GAP,initial_crown_clearance_m=CROWN_GAP,
                limitations=['Proposed setup; no full robot trial yet','Planar staple bending approximation',
                             'Conservative elastic paper validity termination; no rendered post-fracture topology'])
