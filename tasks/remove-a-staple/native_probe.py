"""Native jaw-contact/plastic-hinge coupon, not a complete staple task.

A 3 mm real-scale wire leg is rooted at a revolute material hinge. A prescribed
kinematic diagnostic jaw presses downward, then withdraws. Only native contact
can move the leg. There are no paper sheets; paper survival/extraction cannot
be inferred. This entry point is authored but not runtime validated.
"""
import argparse
import json
import math
from pathlib import Path
import time
import numpy as np
from materials import SteelSpec
from physx_material import PhysxPlasticHinge


def build(stage):
    from pxr import Gf, PhysxSchema, Sdf, UsdGeom, UsdPhysics
    UsdGeom.SetStageMetersPerUnit(stage, 1.)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    scene = UsdPhysics.Scene.Define(stage, "/physicsScene")
    scene.CreateGravityMagnitudeAttr(0.)
    ps = PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
    ps.CreateSolverTypeAttr("TGS")
    ps.CreateEnableGPUDynamicsAttr(False)
    ps.CreateBroadphaseTypeAttr("MBP")
    ps.CreateEnableCCDAttr(True)

    def body(path, center, size, mass, kinematic=False):
        root = UsdGeom.Xform.Define(stage, path)
        translate = root.AddTranslateOp()
        translate.Set(Gf.Vec3d(*center))
        root.AddOrientOp().Set(Gf.Quatf(1.,0.,0.,0.))
        p = root.GetPrim()
        rb = UsdPhysics.RigidBodyAPI.Apply(p)
        rb.CreateKinematicEnabledAttr(kinematic)
        UsdPhysics.MassAPI.Apply(p).CreateMassAttr(mass)
        extra = PhysxSchema.PhysxRigidBodyAPI.Apply(p)
        extra.CreateSolverPositionIterationCountAttr(128)
        extra.CreateSolverVelocityIterationCountAttr(32)
        extra.CreateSleepThresholdAttr(0.)
        extra.CreateEnableCCDAttr(True)
        extra.CreateMaxDepenetrationVelocityAttr(.01)
        shape = UsdGeom.Cube.Define(stage, path+"/shape")
        shape.CreateSizeAttr(1.)
        shape.AddScaleOp().Set(Gf.Vec3f(*size))
        UsdPhysics.CollisionAPI.Apply(shape.GetPrim())
        collision = PhysxSchema.PhysxCollisionAPI.Apply(shape.GetPrim())
        collision.CreateContactOffsetAttr(.000002)
        collision.CreateRestOffsetAttr(0.)
        return p, translate

    steel = SteelSpec()
    length = .003
    mass = 7850*length*steel.wire_width_m*steel.wire_thickness_m
    leg, _ = body("/Probe/leg", (length/2,0.,0.),
                  (length,steel.wire_width_m,steel.wire_thickness_m), mass)
    _, jaw_translate = body("/Probe/jaw", (.0025,0.,.001), (.001,.002,.001), .01, True)
    joint = UsdPhysics.RevoluteJoint.Define(stage, "/Probe/material_hinge")
    joint.CreateAxisAttr("Y")
    joint.CreateBody1Rel().SetTargets([Sdf.Path("/Probe/leg")])
    joint.CreateLocalPos0Attr(Gf.Vec3f(0.,0.,0.))
    joint.CreateLocalPos1Attr(Gf.Vec3f(-length/2,0.,0.))
    joint.CreateLowerLimitAttr(-5.)
    joint.CreateUpperLimitAttr(100.)
    material = PhysxPlasticHinge(joint.GetPrim(), steel)
    return jaw_translate, material


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--dt", type=float, default=.0001)
    p.add_argument("--seconds", type=float, default=2.)
    args = p.parse_args()
    if not .00002 <= args.dt <= .001 or not 1 <= args.seconds <= 5:
        p.error("Use 0.00002 <= dt <= 0.001 and 1 <= seconds <= 5")
    args.out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    from isaaclab.app import AppLauncher
    app = AppLauncher(headless=True, enable_cameras=False).app
    from pxr import Gf, Usd, UsdUtils
    from omni.physx import get_physx_interface, get_physx_simulation_interface
    sim, physics = get_physx_simulation_interface(), get_physx_interface()
    cache = UsdUtils.StageCache.Get()
    stage = Usd.Stage.CreateInMemory()
    cache.Insert(stage)
    attached = False
    record = {"schema":"native-staple-contact-probe-v1","complete":False,"calibrated":False,
              "evidence_type":"Native wire/kinematic-jaw contact coupon; no paper, extraction or robot evidence",
              "dt":args.dt,"seconds":args.seconds,"samples":[]}
    try:
        jaw, material = build(stage)
        stage.GetRootLayer().Export(str(args.out/"initial.usda"))
        sim.attach_stage(cache.GetId(stage).ToLongInt())
        attached = True
        steps = round(args.seconds/args.dt)
        for step in range(steps):
            # Smooth down/up diagnostic sweep; no dynamic-body pose writes.
            fraction = (step+1)/steps
            descent = math.sin(math.pi*fraction)**2
            bottom = .0005-.003*descent
            jaw.Set(Gf.Vec3d(.0025,0.,bottom+.0005))
            sim.simulate(args.dt, step*args.dt)
            sim.fetch_results()
            tr = physics.get_rigidbody_transformation("/Probe/leg")
            if not tr.get("ret_val"):
                raise RuntimeError("Native body transformation unavailable")
            x,y,z,w = map(float,tr["rotation"])
            angle = math.atan2(2*(w*y+x*z),1-2*(y*y+z*z))
            response = material.update_from_measured_angle(angle)
            if not math.isfinite(angle) or abs(angle) > math.pi:
                raise RuntimeError("Native wire coupon became invalid")
            if step % max(1,round(.005/args.dt)) == 0 or step == steps-1:
                record["samples"].append({"step":step+1,"jaw_bottom_z_m":bottom,
                    "leg_center_m":list(map(float,tr["position"])),"angle_rad":angle,**response})
        record["residual_angle_rad"] = record["samples"][-1]["angle_rad"]
        record["plastic_angle_rad"] = material.hinge.plastic_angle_rad
        if abs(record["plastic_angle_rad"]) < .05:
            raise RuntimeError("Diagnostic jaw did not produce measurable plastic bending; inspect contact scale and drive update")
        record["complete"] = True
        stage.GetRootLayer().Export(str(args.out/"final.usda"))
    except Exception as e:
        record["error"] = f"{type(e).__name__}: {e}"
        raise
    finally:
        record["wall_seconds"] = time.monotonic()-started
        (args.out/"native-probe.json").write_text(json.dumps(record,indent=2)+"\n")
        if attached: sim.detach_stage()
        cache.Erase(stage)
        app.close()


if __name__ == "__main__":
    main()
