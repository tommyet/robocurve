"""Native dispenser geometry and material coupling, imported after SimulationApp.

The plunger is a free rigid body constrained by an ordinary prismatic joint.
There are no motor targets. Equal and opposite material-pressure forces resist
compression. Only emitted material geometry is authored from material state.
This adapter is implemented but has not yet been executed on the team GPU.
"""
from __future__ import annotations
import numpy as np
from material import Icing


def rotation(q):
    q=np.asarray(q,float);q=q/np.linalg.norm(q)
    x,y,z,w=q
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])


def author_dispenser(stage,barrel_path,plunger_path,*,diagnostic_fixture=False):
    """Add the joint/nozzle to existing Box rigid bodies, before physics starts.

    Barrel frame: long axis +Y towards tip, plunger initial centre Y=-60 mm.
    The bare barrel/plunger boxes remain the normal grip/contact surfaces.
    """
    from pxr import Gf,Sdf,UsdGeom,UsdPhysics,PhysxSchema
    b,p=stage.GetPrimAtPath(barrel_path),stage.GetPrimAtPath(plunger_path)
    for prim in (b,p):
        if not prim or not prim.HasAPI(UsdPhysics.RigidBodyAPI):
            raise RuntimeError("Dispenser needs two existing dynamic rigid bodies")
        rb=PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
        rb.CreateSolverPositionIterationCountAttr(64)
        rb.CreateSolverVelocityIterationCountAttr(16)
        rb.CreateEnableCCDAttr(True)
    # Barrel/plunger overlap only at the sliding seal. Other object contact is
    # retained. No task/policy condition changes this permanent mechanism.
    UsdPhysics.FilteredPairsAPI.Apply(b).CreateFilteredPairsRel().SetTargets([Sdf.Path(plunger_path)])
    joint=UsdPhysics.PrismaticJoint.Define(stage,barrel_path+'/PistonGuide')
    joint.CreateBody0Rel().SetTargets([Sdf.Path(barrel_path)])
    joint.CreateBody1Rel().SetTargets([Sdf.Path(plunger_path)])
    joint.CreateAxisAttr('Y')
    joint.CreateLocalPos0Attr(Gf.Vec3f(0.,-.060,0.))
    joint.CreateLocalPos1Attr(Gf.Vec3f(0.,0.,0.))
    joint.CreateLowerLimitAttr(0.)
    joint.CreateUpperLimitAttr(Icing().p.stroke_m)
    # A hollow metal frustum, with an actual six-point aperture. Each sector is
    # one convex contact piece. Icing is emitted through this same aperture.
    for i in range(24):
        angles=np.array((i,i+1))*2*np.pi/24
        pts=[]
        for y,outer in ((.040,.010),(.080,.004)):
            for inner in (False,True):
                for angle in angles:
                    radius=(.008 if y==.040 else .0025*(1+.28*np.cos(6*angle))) if inner else outer
                    pts.append((radius*np.cos(angle),y,radius*np.sin(angle)))
        faces=((0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3))
        mesh=UsdGeom.Mesh.Define(stage,f'{barrel_path}/NozzleSector{i:02d}')
        mesh.CreatePointsAttr(pts);mesh.CreateFaceVertexCountsAttr([4]*6)
        mesh.CreateFaceVertexIndicesAttr([j for f in faces for j in f])
        mesh.CreateSubdivisionSchemeAttr('none')
        mesh.CreateDisplayColorAttr([Gf.Vec3f(.70,.72,.75)])
        UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
        UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim()).CreateApproximationAttr('convexHull')
        contact=PhysxSchema.PhysxCollisionAPI.Apply(mesh.GetPrim())
        contact.CreateContactOffsetAttr(.0002);contact.CreateRestOffsetAttr(0.)
    if diagnostic_fixture:
        # Test fixture only, expressly absent from the robot scene.
        world=UsdGeom.XformCache().GetLocalToWorldTransform(b)
        anchor=UsdPhysics.FixedJoint.Define(stage,barrel_path+'/DiagnosticClamp')
        anchor.CreateBody1Rel().SetTargets([Sdf.Path(barrel_path)])
        anchor.CreateLocalPos0Attr(Gf.Vec3f(*world.ExtractTranslation()))
        q=world.ExtractRotationQuat()
        anchor.CreateLocalRot0Attr(Gf.Quatf(q.GetReal(),Gf.Vec3f(*q.GetImaginary())))
    return joint


class Coupling:
    def __init__(self,material=None):
        self.material=material or Icing()
        self.last_piston_m=0.
        self.last_reaction_n=0.
        self.last_contact_force=np.zeros(3)
        self.last_contact_torque=np.zeros(3)
        self.mesh=None

    def advance(self,barrel_pose,barrel_velocity,plunger_pose,dt):
        """Return world pressure wrenches from measured native body state."""
        b,p,v=(np.asarray(a,float) for a in (barrel_pose,plunger_pose,barrel_velocity))
        r=rotation(b[3:]);axis=r[:,1]
        q=float(np.dot(p[:3]-b[:3],axis)+.060)
        # A tolerance handles PhysX joint round-off, not arbitrary out-of-range
        # state. Larger constraint violations fail rather than earn material.
        if not -.0002<=q<=self.material.p.stroke_m+.0002:
            raise RuntimeError(f"Piston escaped its guide: {q:.6f} m")
        q=float(np.clip(q,0.,self.material.p.stroke_m))
        tip=b[:3]+r@np.array((0.,.080,0.))
        tipvel=v[:3]+np.cross(v[3:],tip-b[:3])
        nr=r@np.array([[1.,0.,0.],[0.,0.,1.],[0.,-1.,0.]])
        reaction=self.material.step(dt,piston_m=q,nozzle_pos=tip,
                                    nozzle_rotation=nr,nozzle_velocity=tipvel)
        angles=np.arange(24)*2*np.pi/24
        samples=np.array([(radius*np.cos(a),.080,radius*np.sin(a))
                          for radius in (.0035,.004) for a in angles])
        world=samples@r.T+b[:3]
        velocities=v[:3]+np.cross(np.broadcast_to(v[3:],world.shape),world-b[:3])
        contact=self.material.tool_contact(world,velocities,dt,
                                          stiffness_n_m=1500./len(world),damping_ns_m=1./len(world))
        self.last_contact_force=contact.sum(axis=0)
        self.last_contact_torque=np.cross(world-b[:3],contact).sum(axis=0)
        self.last_piston_m,self.last_reaction_n=q,reaction
        # The fluid pushes the piston backwards and barrel forwards. Torque is
        # zero for these centred axial forces.
        return axis*reaction+self.last_contact_force,-axis*reaction

    def author_surface(self,stage,path='/World/DepositedIcing'):
        from pxr import Gf,UsdGeom
        m=self.material
        points=np.column_stack((m.X.ravel(),m.Y.ravel(),(m.base+m.height).ravel()))
        faces=[];ny=len(m.y)
        for i in range(len(m.x)-1):
            for j in range(ny-1):
                a=i*ny+j;faces.extend(((a,a+ny,a+ny+1),(a,a+ny+1,a+1)))
        self.all_faces=np.asarray(faces,int)
        self.mesh=UsdGeom.Mesh.Define(stage,path)
        self.mesh.CreatePointsAttr(points.tolist())
        self.mesh.CreateSubdivisionSchemeAttr('none')
        self.mesh.CreateDoubleSidedAttr(True)
        self.mesh.CreateDisplayColorAttr([Gf.Vec3f(.91,.78,.49)])
        self.update_surface()

    def update_surface(self):
        if self.mesh is None:return
        m=self.material
        points=np.column_stack((m.X.ravel(),m.Y.ravel(),(m.base+m.height).ravel()))
        # No icing is drawn until the material solver deposits it. The same
        # measured surface is used by the scorer; blank cells remain invisible.
        active=m.height.ravel()>1e-5
        faces=self.all_faces[active[self.all_faces].any(axis=1)]
        self.mesh.GetPointsAttr().Set(points.tolist())
        self.mesh.CreateFaceVertexCountsAttr([3]*len(faces))
        self.mesh.CreateFaceVertexIndicesAttr(faces.ravel().tolist())
