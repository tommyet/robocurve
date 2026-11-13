"""Author the proposed wheel/stand/nipple/wrench scene in an existing USD stage.

This is substantive native geometry and mechanics, but remains UNRUN. It is not
a YAM demo, policy, score or submission certificate. The caller must install
NativeThreadCoupler.before_step before every physics substep, preserve its
failure conditions, and reset all bodies/joints to their authored states.
"""
from __future__ import annotations
import math
import numpy as np
from mechanics import WheelSpec, starting_turn_errors
from native_probe import build as build_ring
from thread_coupling import ThreadSpec


def quat(R):
    R=np.asarray(R,dtype=float)
    tr=np.trace(R)
    if tr>0:
        s=2*math.sqrt(tr+1.)
        return np.array([(R[2,1]-R[1,2])/s,(R[0,2]-R[2,0])/s,(R[1,0]-R[0,1])/s,.25*s])
    i=int(np.argmax(np.diag(R)))
    j,k=(i+1)%3,(i+2)%3
    s=2*math.sqrt(1+R[i,i]-R[j,j]-R[k,k])
    out=np.zeros(4)
    out[i]=.25*s
    out[j]=(R[j,i]+R[i,j])/s
    out[k]=(R[k,i]+R[i,k])/s
    out[3]=(R[k,j]-R[j,k])/s
    return out


def x_frame(direction):
    # Callers reuse the metric direction to place the two half-spokes.
    x=np.array(direction,dtype=float,copy=True)
    x/=np.linalg.norm(x)
    seed=np.array([0.,0.,1.]) if abs(x[2])<.9 else np.array([0.,1.,0.])
    y=np.cross(seed,x)
    y/=np.linalg.norm(y)
    return np.column_stack((x,y,np.cross(x,y)))


def build_scene(stage, root="/WheelTask"):
    from pxr import Gf, PhysxSchema, Sdf, UsdGeom, UsdPhysics
    spec,thread=WheelSpec(),ThreadSpec()
    wheel=root+"/wheel"
    n=spec.spokes
    UsdGeom.Xform.Define(stage,root)
    initial=starting_turn_errors(spec)
    rim_paths,old_spokes,_=build_ring(stage,initial,root=wheel,configure_physics=False)
    wheel_xf=UsdGeom.Xform.Define(stage,wheel)
    wheel_xf.AddTranslateOp().Set(Gf.Vec3d(.35,0.,1.005))
    wheel_xf.AddRotateYOp().Set(90.)

    def qgf(R):
        x,y,z,w=map(float,quat(R))
        return Gf.Quatf(w,x,y,z)

    def shape(parent,name,center,size,kind="box",color=(.45,.47,.5)):
        path=parent+"/"+name
        scale=None
        if kind=="cylinder":
            g=UsdGeom.Cylinder.Define(stage,path)
            g.CreateAxisAttr("Z")
            g.CreateRadiusAttr(size[0])
            g.CreateHeightAttr(size[1])
        elif kind=="capsule":
            g=UsdGeom.Capsule.Define(stage,path)
            g.CreateAxisAttr("X")
            g.CreateRadiusAttr(size[1])
            g.CreateHeightAttr(size[0])
        else:
            g=UsdGeom.Cube.Define(stage,path)
            g.CreateSizeAttr(1.)
            scale=g.AddScaleOp()
            scale.Set(Gf.Vec3f(*map(float,size)))
        translation=g.AddTranslateOp()
        translation.Set(Gf.Vec3d(*map(float,center)))
        if scale is not None:
            g.SetXformOpOrder([translation,scale])
        g.CreateDisplayColorAttr([Gf.Vec3f(*color)])
        UsdPhysics.CollisionAPI.Apply(g.GetPrim())
        c=PhysxSchema.PhysxCollisionAPI.Apply(g.GetPrim())
        c.CreateContactOffsetAttr(.000002)
        c.CreateRestOffsetAttr(0.)

    def body(path,pos,R,mass=None):
        g=UsdGeom.Xform.Define(stage,path)
        g.AddTranslateOp().Set(Gf.Vec3d(*map(float,pos)))
        g.AddOrientOp().Set(qgf(R))
        if mass is not None:
            p=g.GetPrim()
            UsdPhysics.RigidBodyAPI.Apply(p)
            UsdPhysics.MassAPI.Apply(p).CreateMassAttr(mass)
            rb=PhysxSchema.PhysxRigidBodyAPI.Apply(p)
            rb.CreateSolverPositionIterationCountAttr(128)
            rb.CreateSolverVelocityIterationCountAttr(4)
            rb.CreateSleepThresholdAttr(0.)
            rb.CreateEnableCCDAttr(True)
        return g

    I=np.eye(3)
    stand=root+"/stand"
    body(stand,(0.,0.,0.),I)
    shape(stand,"base",(.35,0.,.7575),(.18,.28,.02),color=(.18,.2,.22))
    for i,x in enumerate((.285,.415)):
        shape(stand,f"upright_{i}",(x,0.,.88625),(.015,.025,.2375),color=(.18,.2,.22))
    shape(stand,"pointer",(.373,0.,.785),(.020,.002,.002),color=(.85,.25,.12))

    hub=wheel+"/hub"
    body(hub,(0.,0.,0.),I,.18)
    shape(hub,"axle",(0.,0.,0.),(.010,.010,.130))
    shape(hub,"barrel",(0.,0.,0.),(.035,.035,.050))
    for side in (-1,1):
        shape(hub,f"flange_{'left' if side<0 else 'right'}",(0.,0.,side*.025),(.025,.003,0.),kind="cylinder")
    bearing=UsdPhysics.RevoluteJoint.Define(stage,wheel+"/hub_bearing")
    bearing.CreateAxisAttr("Z")
    bearing.CreateBody1Rel().SetTargets([Sdf.Path(hub)])
    bearing.CreateLocalPos0Attr(Gf.Vec3f(.35,0.,1.005))
    bearing.CreateLocalRot0Attr(Gf.Quatf(math.sqrt(.5),0.,math.sqrt(.5),0.))
    bearing.CreateLocalPos1Attr(Gf.Vec3f(0.,0.,0.))
    visc=UsdPhysics.DriveAPI.Apply(bearing.GetPrim(),"angular")
    visc.CreateTypeAttr("force")
    visc.CreateStiffnessAttr(0.)
    visc.CreateDampingAttr(.001*math.pi/180.)
    visc.CreateTargetVelocityAttr(0.)
    # Axle/stand overlap is an authored bearing, not a collision support.
    UsdPhysics.FilteredPairsAPI.Apply(stage.GetPrimAtPath(hub)).CreateFilteredPairsRel().SetTargets([Sdf.Path(stand)])

    theta=np.arange(n)*2*math.pi/n
    vertices=np.column_stack((spec.rim_radius_m*np.cos(theta),spec.rim_radius_m*np.sin(theta),np.zeros(n)))
    chord=2*spec.rim_radius_m*math.sin(math.pi/n)
    metadata={"hub_path":hub,"spokes":[],"wrench_path":root+"/wrench"}
    for i in range(n):
        old_spokes[i].CreateJointEnabledAttr(False)
        side=1 if i%2==0 else -1
        a=theta[i]+side*spec.cross_angle_rad
        anchor=np.array([spec.hub_flange_radius_m*math.cos(a),spec.hub_flange_radius_m*math.sin(a),side*spec.hub_half_width_m])
        endpoint=vertices[i]
        vec=endpoint-anchor
        L=float(np.linalg.norm(vec))
        R=x_frame(vec)
        k=spec.spoke_modulus_pa*math.pi*(spec.spoke_diameter_m/2)**2/L
        nominal=L-spec.baseline_tension_n/k
        rim_center=(vertices[i]+vertices[(i+1)%n])/2
        rim_R=x_frame(vertices[(i+1)%n]-vertices[i])
        # x_frame on a planar tangent produces the same z-up frame as the ring.
        inner=f"{wheel}/spoke_{i:02d}_inner"
        outer=f"{wheel}/spoke_{i:02d}_outer"
        mass=7850*math.pi*(spec.spoke_diameter_m/2)**2*L/2
        for path,fraction in ((inner,.25),(outer,.75)):
            body(path,anchor+vec*fraction,R,mass)
            shape(path,"steel",(0.,0.,0.),(L/2,.001,0.),kind="capsule")
            # The eyelet lies on the shared boundary of two rim sectors.
            # Both sectors overlap this jointed internal interface; filtering
            # only i would make i-1 eject the rod against its own rim joint.
            UsdPhysics.FilteredPairsAPI.Apply(stage.GetPrimAtPath(path)).CreateFilteredPairsRel().SetTargets([
                Sdf.Path(inner if path==outer else outer),Sdf.Path(hub),
                Sdf.Path(rim_paths[i]),Sdf.Path(rim_paths[(i-1)%n])])
        for label,path,other,p0,p1 in (
                ("hub",inner,hub,anchor,(-L/4,0.,0.)),
                ("rim",outer,rim_paths[i],(-chord/2,0.,0.),(L/4,0.,0.))):
            # A retained spoke head can tilt but cannot freely spin about the
            # shaft. This transmits the thread reaction through actual bodies.
            joint=(UsdPhysics.Joint if label=='hub' else UsdPhysics.SphericalJoint).Define(stage,f"{wheel}/spoke_{i:02d}_{label}_joint")
            joint.CreateBody0Rel().SetTargets([Sdf.Path(other)])
            joint.CreateBody1Rel().SetTargets([Sdf.Path(path)])
            joint.CreateLocalPos0Attr(Gf.Vec3f(*map(float,p0)))
            joint.CreateLocalPos1Attr(Gf.Vec3f(*map(float,p1)))
            if label=='hub':
                joint.CreateLocalRot0Attr(qgf(R));joint.CreateLocalRot1Attr(qgf(I))
                for axis in ('transX','transY','transZ','rotX'):
                    locked=UsdPhysics.LimitAPI.Apply(joint.GetPrim(),axis)
                    locked.CreateLowAttr(1.);locked.CreateHighAttr(-1.)
        axial=UsdPhysics.Joint.Define(stage,f"{wheel}/spoke_{i:02d}_axial")
        axial.CreateBody0Rel().SetTargets([Sdf.Path(inner)])
        axial.CreateBody1Rel().SetTargets([Sdf.Path(outer)])
        axial.CreateLocalPos0Attr(Gf.Vec3f(L/4,0.,0.))
        axial.CreateLocalPos1Attr(Gf.Vec3f(-L/4,0.,0.))
        for axis in ("transY","transZ","rotX"):
            limit=UsdPhysics.LimitAPI.Apply(axial.GetPrim(),axis)
            limit.CreateLowAttr(1.)
            limit.CreateHighAttr(-1.)
        # Midspan bending is compliant: a perfectly rigid two-half rod would
        # make a physical spoke-tension gauge impossible to reproduce. For
        # pin-supported half rods K=3EI/L gives the standard 48EI/L^3 centre
        # load stiffness; axial pretension adds geometric stiffness naturally.
        bend_stiffness=3*spec.spoke_modulus_pa*(math.pi*spec.spoke_diameter_m**4/64)/L
        for axis in ("rotY","rotZ"):
            bend=UsdPhysics.DriveAPI.Apply(axial.GetPrim(),axis)
            bend.CreateTypeAttr("force");bend.CreateStiffnessAttr(bend_stiffness*math.pi/180.)
            bend.CreateDampingAttr(.002*math.pi/180.);bend.CreateTargetPositionAttr(0.)
        limit=UsdPhysics.LimitAPI.Apply(axial.GetPrim(),"transX")
        limit.CreateLowAttr(-1.)
        limit.CreateHighAttr(nominal-initial[i]*thread.pitch_m_per_turn-L)
        soft=PhysxSchema.PhysxLimitAPI.Apply(axial.GetPrim(),"transX")
        soft.CreateStiffnessAttr(k)
        soft.CreateDampingAttr(1.)

        nipple=f"{wheel}/nipple_{i:02d}"
        nipple_center=endpoint-R[:,0]*.006
        body(nipple,nipple_center,R,.0009)
        shape(nipple,"flats",(0.,0.,0.),(.012,.00323,.00323),color=(.7,.52,.17))
        UsdPhysics.FilteredPairsAPI.Apply(stage.GetPrimAtPath(nipple)).CreateFilteredPairsRel().SetTargets([
            Sdf.Path(rim_paths[i]),Sdf.Path(rim_paths[(i-1)%n]),Sdf.Path(outer)])
        hinge=UsdPhysics.RevoluteJoint.Define(stage,f"{wheel}/nipple_{i:02d}_bearing")
        hinge.CreateAxisAttr("X")
        hinge.CreateBody0Rel().SetTargets([Sdf.Path(rim_paths[i])])
        hinge.CreateBody1Rel().SetTargets([Sdf.Path(nipple)])
        hinge.CreateLocalPos0Attr(Gf.Vec3f(*map(float,rim_R.T@(nipple_center-rim_center))))
        hinge.CreateLocalPos1Attr(Gf.Vec3f(0.,0.,0.))
        hinge.CreateLocalRot0Attr(qgf(rim_R.T@R))
        # Thread friction acts between nipple and outer spoke, not between
        # nipple and rim. The separate rim bearing locates the nipple but does
        # not prescribe its threaded angle or transfer a fictitious torque.
        thread_joint=UsdPhysics.Joint.Define(stage,f'{wheel}/nipple_{i:02d}_thread_friction')
        thread_joint.CreateBody0Rel().SetTargets([Sdf.Path(outer)])
        thread_joint.CreateBody1Rel().SetTargets([Sdf.Path(nipple)])
        friction=UsdPhysics.DriveAPI.Apply(thread_joint.GetPrim(),"rotX")
        friction.CreateTypeAttr("force")
        friction.CreateStiffnessAttr(0.)
        friction.CreateDampingAttr(thread.viscous_friction_nm_s_per_rad*math.pi/180.)
        friction.CreateTargetVelocityAttr(0.)
        friction.CreateMaxForceAttr(thread.friction_coefficient*spec.baseline_tension_n*thread.thread_mean_radius_m)
        metadata["spokes"].append({"nipple_path":nipple,"rim_path":rim_paths[i],
            "reference_nipple_in_spoke_rotation":I.tolist(),
            "initial_turn_offset":float(initial[i]),"hub_anchor_local_m":anchor.tolist(),
            "rim_anchor_local_m":[-chord/2,0.,0.],"nominal_rest_m":nominal,
            "stiffness_n_per_m":k,"rest_target_attribute":limit.GetHighAttr(),
            "inner_path":inner,"outer_path":outer,"half_rod_length_m":L/2,
            "rest_target_origin_m":L,"friction_drive":friction})

    wrench=metadata["wrench_path"]
    body(wrench,(.20,-.155,.7555),I,.045)
    shape(wrench,"handle",(0.,-.045,0.),(.016,.080,.016),color=(.13,.28,.4))
    half_slot=.00325/2
    for side in (-1,1):
        shape(wrench,f"jaw_{'left' if side<0 else 'right'}",(side*(half_slot+.001),0.,0.),(.002,.008,.004))
    shape(wrench,"jaw_back",(0.,-.005,0.),(.00725,.002,.004))
    return metadata
