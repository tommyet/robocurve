"""Native flexible cloth joined only by contact with closed thread chains.

There are no cloth attachments, welds, proximity latches or vertex targets.
Breaking a thread joint leaves all fragments and their cloth contacts present.
Whether 0.4 mm thread/hole contact is stable is the purpose of the native probe.
"""
import math
import numpy as np
from geometry import patch,stitch_loop,STITCH_Y
from native_cloth import Fabric,author_cloth


def x_quat(direction):
    d=np.asarray(direction,float);d/=np.linalg.norm(d)
    if d[0]<-1+1e-10:return np.array((0.,0.,1.,0.))
    q=np.array((0.,-d[2],d[1],1+d[0]));return q/np.linalg.norm(q)


def author_thread(stage,path,nodes,*,radius=.0002,density=1400.,open_diagnostic=False):
    from pxr import Gf,Sdf,UsdGeom,UsdPhysics,PhysxSchema,UsdShade
    nodes=np.asarray(nodes,float);d=np.roll(nodes,-1,axis=0)-nodes
    lengths=np.linalg.norm(d,axis=1);centres=(nodes+np.roll(nodes,-1,axis=0))/2
    if np.any(lengths<2*radius):raise ValueError('Thread links too short for their radius')
    n=len(nodes);bodies=[];joints=[]
    for i,(p,direction,length) in enumerate(zip(centres,d,lengths)):
        root=UsdGeom.Xform.Define(stage,f'{path}/link_{i:03d}')
        root.AddTranslateOp().Set(Gf.Vec3d(*p))
        q=x_quat(direction);root.AddOrientOp(UsdGeom.XformOp.PrecisionDouble).Set(Gf.Quatd(q[3],*q[:3]))
        prim=root.GetPrim();UsdPhysics.RigidBodyAPI.Apply(prim)
        UsdPhysics.MassAPI.Apply(prim).CreateMassAttr(float(math.pi*radius**2*length*density))
        rb=PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
        rb.CreateSolverPositionIterationCountAttr(128)
        rb.CreateSolverVelocityIterationCountAttr(32)
        rb.CreateEnableCCDAttr(True)
        rb.CreateMaxDepenetrationVelocityAttr(.15)
        rb.CreateLinearDampingAttr(.04);rb.CreateAngularDampingAttr(.02)
        capsule=UsdGeom.Capsule.Define(stage,f'{path}/link_{i:03d}/Shape')
        capsule.CreateAxisAttr('X');capsule.CreateRadiusAttr(radius);capsule.CreateHeightAttr(float(length))
        capsule.CreateDisplayColorAttr([Gf.Vec3f(.8,.08,.03)])
        UsdPhysics.CollisionAPI.Apply(capsule.GetPrim())
        contact=PhysxSchema.PhysxCollisionAPI.Apply(capsule.GetPrim())
        contact.CreateContactOffsetAttr(.00005);contact.CreateRestOffsetAttr(0.)
        mat=UsdShade.Material.Define(stage,f'{path}/ThreadMaterial')
        pm=UsdPhysics.MaterialAPI.Apply(mat.GetPrim())
        pm.CreateStaticFrictionAttr(.35);pm.CreateDynamicFrictionAttr(.3)
        UsdShade.MaterialBindingAPI.Apply(capsule.GetPrim()).Bind(mat,UsdShade.Tokens.weakerThanDescendants,'physics')
        # Only adjoining end-cap overlap is filtered. Every cloth, tool and
        # non-neighbouring thread contact remains active.
        UsdPhysics.FilteredPairsAPI.Apply(prim).CreateFilteredPairsRel().SetTargets(
            [Sdf.Path(f'{path}/link_{j:03d}') for j in ((i-1)%n,(i+1)%n)])
        bodies.append(str(root.GetPath()))
    for i in range(n):
        before=(i-1)%n
        joint=UsdPhysics.SphericalJoint.Define(stage,f'{path}/joint_{i:03d}')
        joint.CreateBody0Rel().SetTargets([Sdf.Path(bodies[before])])
        joint.CreateBody1Rel().SetTargets([Sdf.Path(bodies[i])])
        joint.CreateLocalPos0Attr(Gf.Vec3f(float(lengths[before]/2),0.,0.))
        joint.CreateLocalPos1Attr(Gf.Vec3f(float(-lengths[i]/2),0.,0.))
        joint.CreateCollisionEnabledAttr(False)
        joint.CreateJointEnabledAttr(not (open_diagnostic and i==0))
        joints.append(str(joint.GetPath()))
    return {'bodies':bodies,'joints':joints,'nodes':nodes,'lengths':lengths,
            'mass_kg':float(math.pi*radius**2*lengths.sum()*density)}


def author_pair(stage,*,transform=lambda p:p,open_diagnostic=False,root_path='/World',
                thread_radius=.0002,hole_half=.0006,contact_refinement=None,hole_mesh_spacing=None):
    cloth=[]
    material=Fabric(thickness=.0004,density=350.,youngs_modulus=2e6,bend_modulus=8e4,
                    contact_offset=.00025,rest_offset=.0002,solver_iterations=64)
    for i,left in enumerate((True,False)):
        mesh=patch(left,hole_half=hole_half,hole_mesh_spacing=hole_mesh_spacing)
        mesh.rest=transform(mesh.rest)
        author_cloth(stage,f'{root_path}/Cloth_{i}',mesh,material,
                     color=(.76,.68,.47) if left else (.25,.42,.66),
                     contact_refinement=contact_refinement)
        cloth.append(mesh)
    threads=[author_thread(stage,f'{root_path}/Stitch_{i}',transform(stitch_loop(y)),
                            open_diagnostic=open_diagnostic,radius=thread_radius) for i,y in enumerate(STITCH_Y)]
    return cloth,threads


def sever_contacted_joints(stage,threads,global_indices):
    """Apply force-qualified events from ThreadCutter; never release cloth."""
    from pxr import UsdPhysics
    all_joints=[j for t in threads for j in t['joints']]
    for k in global_indices:
        if not 0<=int(k)<len(all_joints):raise ValueError('Unknown thread joint')
        UsdPhysics.Joint(stage.GetPrimAtPath(all_joints[int(k)])).GetJointEnabledAttr().Set(False)
