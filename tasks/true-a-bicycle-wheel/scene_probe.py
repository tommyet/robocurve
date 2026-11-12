"""Bounded native scene+thread-coupling diagnostic. No robot/policy/Dream.

This settles the proposed complete wheel/stand/wrench geometry with gravity
and records live native body/material state. It does not turn a nipple with a
robot, score the task or certify simulation fidelity. Authored, not yet run.
"""
import argparse
import json
from pathlib import Path
import time
import numpy as np
from wheel_scene import build_scene
from thread_coupling import NativeThreadCoupler, rotation


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--dt",type=float,default=.001)
    p.add_argument("--seconds",type=float,default=2.)
    args=p.parse_args()
    if not .0001<=args.dt<=.002 or not .5<=args.seconds<=5.:
        p.error("Use 0.0001 <= dt <= 0.002 and 0.5 <= seconds <= 5")
    args.out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    from isaaclab.app import AppLauncher
    app=AppLauncher(headless=True,enable_cameras=False).app
    from pxr import Gf,PhysxSchema,Usd,UsdGeom,UsdPhysics,UsdUtils
    from omni.physx import get_physx_interface,get_physx_simulation_interface
    sim,physics=get_physx_simulation_interface(),get_physx_interface()
    cache=UsdUtils.StageCache.Get()
    stage=Usd.Stage.CreateInMemory()
    cache.Insert(stage)
    stage_id=cache.GetId(stage).ToLongInt()
    attached=False
    record={"schema":"native-wheel-scene-diagnostic-v1","complete":False,"calibrated":False,
            "evidence_type":"Native proposed-scene settling with thread coupling; no robot or task score",
            "dt":args.dt,"seconds":args.seconds,"samples":[]}
    try:
        scene=UsdPhysics.Scene.Define(stage,"/physicsScene")
        scene.CreateGravityDirectionAttr(Gf.Vec3f(0.,0.,-1.))
        scene.CreateGravityMagnitudeAttr(9.80665)
        phys=PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
        phys.CreateSolverTypeAttr("TGS")
        phys.CreateEnableGPUDynamicsAttr(False)
        phys.CreateBroadphaseTypeAttr("MBP")
        phys.CreateEnableCCDAttr(True)
        table=UsdGeom.Cube.Define(stage,"/Bench")
        table.CreateSizeAttr(1.)
        table.AddTranslateOp().Set(Gf.Vec3d(.3,0.,.7275))
        table.AddScaleOp().Set(Gf.Vec3f(1.,1.,.04))
        UsdPhysics.CollisionAPI.Apply(table.GetPrim())
        PhysxSchema.PhysxCollisionAPI.Apply(table.GetPrim()).CreateContactOffsetAttr(.000002)
        metadata=build_scene(stage)
        stage.GetRootLayer().Export(str(args.out/"initial.usda"))
        sim.attach_stage(stage_id)
        attached=True
        coupling=NativeThreadCoupler(stage_id,metadata)
        steps=round(args.seconds/args.dt)
        for step in range(steps):
            coupling.before_step()
            sim.simulate(args.dt,step*args.dt)
            sim.fetch_results()
            if step % max(1,round(.02/args.dt))==0 or step==steps-1:
                hub=physics.get_rigidbody_transformation(metadata["hub_path"])
                wrench=physics.get_rigidbody_transformation(metadata["wrench_path"])
                rim=[physics.get_rigidbody_transformation(s["rim_path"]) for s in metadata["spokes"]]
                if not all(t.get("ret_val") for t in [hub,wrench,*rim]):
                    raise RuntimeError("Live body transform missing")
                hp=np.asarray(hub["position"],dtype=float)
                hR=rotation(hub["rotation"])
                points=np.asarray([list(t["position"]) for t in rim],dtype=float)
                local=(points-hp)@hR
                if not np.isfinite(local).all() or np.max(np.linalg.norm(local,axis=1))>.35:
                    raise RuntimeError("Native rim escaped wheel bounds")
                record["samples"].append({"step":step+1,"hub_position_m":hp.tolist(),
                    "hub_rotation_xyzw":list(map(float,hub["rotation"])),
                    "rim_positions_m":points.tolist(),"lateral_runout_m":float(np.ptp(local[:,2])),
                    "wrench_position_m":list(map(float,wrench["position"])),
                    "thread_state":coupling.observation_for_assessor()})
        record["complete"]=True
        stage.GetRootLayer().Export(str(args.out/"final.usda"))
    except Exception as e:
        record["error"]=f"{type(e).__name__}: {e}"
        raise
    finally:
        record["wall_seconds"]=time.monotonic()-started
        (args.out/"scene-diagnostic.json").write_text(json.dumps(record,indent=2)+"\n")
        if attached: sim.detach_stage()
        cache.Erase(stage)
        app.close()


if __name__=="__main__":
    main()
