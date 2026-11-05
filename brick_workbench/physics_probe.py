"""Development material probe, NOT a robot demonstration or task validation.

Run in the pinned Isaac environment, for example::

    python brick_workbench/physics_probe.py --out artifacts/brick-probe-001

Twelve separated fixtures exercise the four joining geometries with aligned,
2 mm lateral-offset, and non-contact hover approaches. Lower bricks are dynamic;
upper bricks are kinematic test actuators moved using PhysX kinematic targets,
not repeated root-pose teleports. No robot, scoring code or attachment joints
are involved. Retention here is material evidence, not proof of robot feasibility.
``--plan`` prints the proposed experiment without launching Isaac.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback

from geometry import (BODY_HEIGHT, STUD_HEIGHT, DEFAULT_DAMPING, DEFAULT_INTERFERENCE,
                      DEFAULT_SEGMENTS, DEFAULT_STIFFNESS, brick_dimensions, generate_brick_usd)
from variants import VARIANTS, config

DT = 1 / 240
SETTLE_S = 0.5
INSERT_S = 2.5
SEAT_HOLD_S = 0.5
LIFT_S = 4.0
AIR_HOLD_S = 1.25
START_GAP = STUD_HEIGHT + 0.006
SEATED_GAP = 0.0001
LIFT_DISTANCE = 0.04


def experiment_cases():
    cases = []
    for variant_index, name in enumerate(VARIANTS):
        task = config(name)
        for mode_index, mode in enumerate(("aligned", "misaligned_2mm", "hover_2mm")):
            index = len(cases)
            centre = [variant_index * 0.20, mode_index * 0.20]
            offset = list(task["target_offset"])
            if mode == "misaligned_2mm":
                offset[0] += 0.002
            cases.append({
                "index": index, "name": f"{name}__{mode}", "variant": name, "mode": mode,
                "lower_shape": list(task["lower_shape"]), "upper_shape": list(task["upper_shape"]),
                "lower_mass_kg": task["lower_mass"], "upper_mass_kg": task["upper_mass"],
                "lower_xy": centre, "upper_xy": [centre[j] + offset[j] for j in range(2)],
                "target_offset": list(task["target_offset"]),
                "final_gap_m": STUD_HEIGHT + 0.002 if mode == "hover_2mm" else SEATED_GAP,
                "lower_path": f"/World/Probe/case_{index:02d}/lower",
                "upper_path": f"/World/Probe/case_{index:02d}/upper",
            })
    return cases


def phase_at(t):
    if t <= SETTLE_S:
        return "settle"
    if t <= SETTLE_S + INSERT_S:
        return "insert"
    if t <= SETTLE_S + INSERT_S + SEAT_HOLD_S:
        return "seat_hold"
    if t <= SETTLE_S + INSERT_S + SEAT_HOLD_S + LIFT_S:
        return "lift"
    return "air_hold"


def desired_gap(case, t):
    u = min(1.0, max(0.0, (t - SETTLE_S) / INSERT_S))
    return START_GAP + u * (case["final_gap_m"] - START_GAP)


def _rotation(q):
    x, y, z, w = q
    n = math.sqrt(x*x + y*y + z*z + w*w)
    x, y, z, w = x/n, y/n, z/n, w/n
    return ((1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)),
            (2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)),
            (2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)))


def geometry_metrics(case, lower, upper):
    """Use measured root poses, including lower rotation, for conservative bounds."""
    # Tensor views return NumPy float32 values. Convert at this boundary so every
    # metric is ordinary JSON-serializable Python data, including nested vectors.
    lower = [float(value) for value in lower]
    upper = [float(value) for value in upper]
    rotation = _rotation(lower[3:])
    delta = [upper[i] - lower[i] for i in range(3)]
    relative = [sum(rotation[j][i] * delta[j] for j in range(3)) for i in range(3)]
    width, depth, height = brick_dimensions(case["lower_shape"])
    # A complete enclosing box, including studs, gives a conservative floor gap.
    low_z = (lower[2] + rotation[2][2] * STUD_HEIGHT/2
             - sum(abs(rotation[2][j]) * size/2
                   for j, size in enumerate((width, depth, height + STUD_HEIGHT))))
    return {
        "lower_floor_clearance_m": low_z,
        "relative_root_position_m": relative,
        "seat_gap_m": relative[2] - BODY_HEIGHT,
        "target_xy_error_m": math.hypot(relative[0]-case["target_offset"][0],
                                         relative[1]-case["target_offset"][1]),
        "lower_tilt_deg": math.degrees(math.acos(max(-1, min(1, rotation[2][2])))),
        "lower_xy_displacement_m": math.hypot(lower[0]-case["lower_xy"][0],
                                               lower[1]-case["lower_xy"][1]),
    }


def parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=Path)
    p.add_argument("--device", default="cpu",
                   help="physics device (default cpu: pinned GPU tensor backend lacks kinematic targets)")
    p.add_argument("--stiffness", type=float, default=DEFAULT_STIFFNESS)
    p.add_argument("--damping", type=float, default=DEFAULT_DAMPING)
    p.add_argument("--interference", type=float, default=DEFAULT_INTERFERENCE)
    p.add_argument("--segments", type=int, default=DEFAULT_SEGMENTS)
    p.add_argument("--normal-force-limit", type=float, default=20.0,
                   help="stop further downward travel above this measured axial normal-contact force (N)")
    p.add_argument("--plan", action="store_true")
    return p


def main():
    p = parser()
    args = p.parse_args()
    cases = experiment_cases()
    total_s = SETTLE_S + INSERT_S + SEAT_HOLD_S + LIFT_S + AIR_HOLD_S
    plan = {
        "purpose": "development material probe; not a task demo or a robot trial",
        "physics_hz": 240, "total_simulated_seconds": total_s,
        "physics_device": args.device,
        "actuation": "upper kinematic target; lower free dynamic under gravity",
        "lower_floor_z_m": 0.0, "lift_distance_m": LIFT_DISTANCE,
        "stiffness_N_per_m": args.stiffness, "damping_Ns_per_m": args.damping,
        "radial_interference_m": args.interference, "socket_segments": args.segments,
        "normal_force_limit_N": args.normal_force_limit,
        "limitations": [
            "Kinematic actuator motion is not a robot feasibility demonstration.",
            "Normal-contact force is not total insertion force; friction is not included.",
            "The free lower brick can self-align during a lateral-offset probe.",
            "Material values remain uncalibrated to physical printed parts.",
            "CPU material-probe results do not establish GPU robot-trial behaviour.",
            "The requested axial-normal-force limit is inactive without brick-pair contact reports.",
        ],
        "cases": cases,
    }
    if args.plan:
        print(json.dumps(plan, indent=2))
        return 0
    if args.out is None:
        p.error("--out is required except with --plan")
    if args.normal_force_limit <= 0 or not math.isfinite(args.normal_force_limit):
        p.error("--normal-force-limit must be finite and positive")
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        p.error("choose a new or empty --out directory; existing evidence will not be overwritten")
    out.mkdir(parents=True, exist_ok=True)
    (out / "plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    source_hashes = {}
    for name in ("geometry.py", "physics_probe.py", "variants.py"):
        source = Path(__file__).with_name(name).read_bytes()
        source_hashes[name] = hashlib.sha256(source).hexdigest()
        (out / name).write_bytes(source)
    os.environ.setdefault("OMNI_KIT_ACCEPT_EULA", "YES")
    started = time.monotonic()
    app = None
    completed = False
    failed = False

    def record_failure(exc, phase):
        """Persist the failure before Kit shutdown can replace a Python exit."""
        nonlocal failed
        failed = True
        details = {"phase": phase, "exception_type": type(exc).__name__,
                   "message": str(exc), "traceback": traceback.format_exc(),
                   "physics_device": args.device, "not_a_task_demonstration": True}
        path = out / ("failure.json" if phase == "probe" else "shutdown-failure.json")
        path.write_text(json.dumps(details, indent=2) + "\n")
        print(f"PROBE FAILED ({phase}): {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)

    try:
        from isaaclab.app import AppLauncher
        app = AppLauncher(headless=True, device=args.device, enable_cameras=False).app
        results = run_probe(args, out, cases, total_s)
        completed = True
        print(json.dumps(results, indent=2), flush=True)
    except BaseException as exc:
        record_failure(exc, "probe")
    finally:
        # Persist status before shutting down the standalone probe process.
        # This pinned SimulationApp.close() can exit the process with status0
        # natively, bypassing Python's SystemExit handling and hiding failures.
        (out / "runtime.json").write_text(json.dumps({
            "completed": completed and not failed, "elapsed_wall_seconds": time.monotonic()-started,
            "physics_device": args.device,
            "source_sha256": source_hashes, "not_a_task_demonstration": True,
            "shutdown": "explicit process exit after evidence is written and streams flushed",
        }, indent=2) + "\n")
    exit_code = 1 if failed else 0
    # This file owns its standalone process. Avoid SimulationApp.close() and
    # destructor hooks so their unconditional exit cannot replace our status.
    # All evidence files have already been closed. OS process teardown releases
    # the simulation resources; no other process or shared VM is affected.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(exit_code)


def run_probe(args, out, cases, total_s):
    import numpy as np
    import torch
    import isaaclab.sim as sim_utils
    import omni.physics.tensors as physics_tensors
    import omni.physx
    from pxr import Gf, PhysicsSchemaTools, PhysxSchema, UsdGeom, UsdPhysics
    from isaaclab.sim.utils.stage import get_current_stage_id

    sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(dt=DT, device=args.device))
    stage = sim.stage
    floor = UsdGeom.Cube.Define(stage, "/World/Probe/Floor")
    floor.CreateSizeAttr().Set(1.0)
    floor.AddTranslateOp().Set(Gf.Vec3d(0.3, 0.2, -0.025))
    floor.AddScaleOp().Set(Gf.Vec3f(2.0, 2.0, 0.05))
    UsdPhysics.CollisionAPI.Apply(floor.GetPrim())
    collision = PhysxSchema.PhysxCollisionAPI.Apply(floor.GetPrim())
    collision.CreateContactOffsetAttr().Set(0.0002)
    collision.CreateRestOffsetAttr().Set(0.0)

    assets = {}
    for case in cases:
        for role, color in (("lower", (0.16, 0.40, 0.90)), ("upper", (0.94, 0.27, 0.15))):
            shape = tuple(case[role + "_shape"])
            key = (shape, role)
            if key not in assets:
                assets[key] = generate_brick_usd(
                    out / "assets" / f"{role}_{shape[0]}x{shape[1]}.usda",
                    shape, color, case[role + "_mass_kg"], stiffness=args.stiffness,
                    damping=args.damping, interference=args.interference, segments=args.segments,
                )
            path = case[role + "_path"]
            prim = stage.DefinePrim(path, "Xform")
            prim.GetReferences().AddReference(str(assets[key]))
            z = BODY_HEIGHT/2 + (BODY_HEIGHT + START_GAP if role == "upper" else 0)
            UsdGeom.Xformable(prim).AddTranslateOp().Set(Gf.Vec3d(*case[role + "_xy"], z))
            UsdPhysics.RigidBodyAPI(prim).CreateKinematicEnabledAttr().Set(role == "upper")
            report = PhysxSchema.PhysxContactReportAPI.Apply(prim)
            report.CreateThresholdAttr().Set(0.0)

    # Isaac Lab 3 disables contact processing globally during context setup.
    # Its own contact sensor enables this setting before simulation reset.
    sim.set_setting("/physics/disableContactProcessing", False)
    # Read each completed step directly, following NVIDIA's installed
    # ContactReportImmediateAPIDemo. No render/event-loop callback is required.
    # Keep only scalar summaries and actual collider identifiers; commanded
    # actuator motion is never used to infer forces.
    actor_case = {case[role + "_path"]: case["index"] for case in cases for role in ("lower", "upper")}
    step_contacts = [{} for _ in cases]
    maxima = [{"pair_normal_axis_force_N": 0.0, "hard_penetration_m": 0.0,
               "soft_penetration_m": 0.0, "contact_points": 0,
               "pair_contact_points": 0} for _ in cases]

    def contacts(headers, data):
        for header in headers:
            actors = [str(PhysicsSchemaTools.intToSdfPath(header.actor0)),
                      str(PhysicsSchemaTools.intToSdfPath(header.actor1))]
            found = [actor_case[a] for a in actors if a in actor_case]
            if not found:
                continue
            index = found[0]
            if any(i != index for i in found):
                raise RuntimeError("probe cells collided; their evidence is invalid")
            pair = len(found) == 2
            colliders = [str(PhysicsSchemaTools.intToSdfPath(header.collider0)),
                         str(PhysicsSchemaTools.intToSdfPath(header.collider1))]
            soft = any("/socket_" in c and ("_land_" in c or "_taper_" in c) for c in colliders)
            current = step_contacts[index]
            for offset in range(header.contact_data_offset, header.contact_data_offset + header.num_contact_data):
                point = data[offset]
                penetration = max(0.0, -float(point.separation))
                key = "soft_penetration_m" if soft else "hard_penetration_m"
                current[key] = max(current.get(key, 0.0), penetration)
                current["contact_points"] = current.get("contact_points", 0) + 1
                if pair:
                    current["pair_contact_points"] = current.get("pair_contact_points", 0) + 1
                    current["pair_normal_axis_force_N"] = current.get("pair_normal_axis_force_N", 0.0) + abs(float(point.impulse[2])) / DT

    physx_sim = omni.physx.get_physx_simulation_interface()
    sim.reset()
    if sim.get_setting("/physics/disableContactProcessing"):
        raise RuntimeError("contact processing was disabled during simulation reset")
    # Isaac Lab 3 explicitly supplies its stage ID when creating tensor views.
    # Its CPU backend intentionally does not call physx_sim.attach_stage():
    # doing so would double-initialize CPU collision broadphase. Omitting this
    # stage_id works accidentally on GPU, but fails on the CPU backend.
    tensor_sim = physics_tensors.create_simulation_view("torch", stage_id=get_current_stage_id())
    lower_view = tensor_sim.create_rigid_body_view([case["lower_path"] for case in cases])
    upper_view = tensor_sim.create_rigid_body_view([case["upper_path"] for case in cases])
    if lower_view.count != len(cases) or upper_view.count != len(cases):
        raise RuntimeError("probe rigid-body view does not contain exactly one body per case")

    def mapping(view, role):
        measured = view.get_transforms().detach().cpu().numpy()
        order = []
        for case in cases:
            distances = np.linalg.norm(measured[:, :2] - np.array(case[role + "_xy"]), axis=1)
            index = int(distances.argmin())
            if distances[index] > 1e-5 or index in order:
                raise RuntimeError("could not uniquely map tensor bodies to their probe cells")
            order.append(index)
        return order

    lower_order, upper_order = mapping(lower_view, "lower"), mapping(upper_view, "upper")
    targets = upper_view.get_transforms().clone()
    indices = torch.arange(upper_view.count, device=targets.device, dtype=torch.int32)
    stopped_gaps = [None] * len(cases)
    actual_seated_gaps = [case["final_gap_m"] for case in cases]
    records = [[] for _ in cases]
    lift_start = SETTLE_S + INSERT_S + SEAT_HOLD_S
    with (out / "trajectory.jsonl").open("x") as stream:
        for step in range(round(total_s / DT)):
            t = (step + 1) * DT
            phase = phase_at(t)
            for i, case in enumerate(cases):
                if phase in ("insert", "seat_hold"):
                    previous_force = step_contacts[i].get("pair_normal_axis_force_N", 0.0)
                    if stopped_gaps[i] is None and previous_force > args.normal_force_limit:
                        stopped_gaps[i] = max(case["final_gap_m"], desired_gap(case, t-DT))
                gap = stopped_gaps[i] if stopped_gaps[i] is not None else desired_gap(case, t)
                actual_seated_gaps[i] = gap
                lift = min(LIFT_DISTANCE, max(0.0, (t-lift_start)/LIFT_S) * LIFT_DISTANCE)
                targets[upper_order[i], 2] = BODY_HEIGHT * 1.5 + gap + lift
            step_contacts = [{} for _ in cases]
            upper_view.set_kinematic_targets(targets, indices)
            sim.step(render=False)
            contact_headers, contact_data = physx_sim.get_contact_report()
            contacts(contact_headers, contact_data)
            lower = lower_view.get_transforms().detach().cpu().numpy()[lower_order]
            upper = upper_view.get_transforms().detach().cpu().numpy()[upper_order]
            if not np.isfinite(lower).all() or not np.isfinite(upper).all():
                raise RuntimeError("non-finite measured rigid-body pose")
            frame = {"time": t, "phase": phase, "cases": []}
            for i, case in enumerate(cases):
                contact = step_contacts[i]
                for key in maxima[i]:
                    if key in ("contact_points", "pair_contact_points"):
                        maxima[i][key] += contact.get(key, 0)
                    else:
                        maxima[i][key] = max(maxima[i][key], contact.get(key, 0.0))
                metrics = geometry_metrics(case, lower[i], upper[i])
                item = {"case": case["name"], "lower_root_pose_xyzw": lower[i].tolist(),
                        "upper_root_pose_xyzw": upper[i].tolist(), "contacts": contact,
                        "metrics": metrics, "descent_limited": stopped_gaps[i] is not None}
                frame["cases"].append(item)
                if t >= total_s - 1.0 - 1e-9:
                    records[i].append(metrics)
            stream.write(json.dumps(frame, allow_nan=False) + "\n")
            if step % 240 == 0:
                stream.flush()
                print(f"probe {t:.2f}/{total_s:.2f}s: {phase}", flush=True)

    results = {"not_a_task_demonstration": True,
               "contact_processing_enabled": not sim.get_setting("/physics/disableContactProcessing"),
               "contact_report_source": "IPhysxSimulation.get_contact_report after each physics step",
               "cases": []}
    for i, case in enumerate(cases):
        last = records[i]
        airborne = all(m["lower_floor_clearance_m"] >= 0.02 for m in last)
        seated = all(abs(m["seat_gap_m"]) <= 0.0005 and m["target_xy_error_m"] <= 0.0005
                     and m["lower_tilt_deg"] <= 5 for m in last)
        reports_observed = maxima[i]["contact_points"] > 0
        pair_reports_observed = maxima[i]["pair_contact_points"] > 0
        diagnostics = dict(maxima[i])
        if not reports_observed:
            diagnostics["hard_penetration_m"] = None
            diagnostics["soft_penetration_m"] = None
        if not pair_reports_observed:
            diagnostics["pair_normal_axis_force_N"] = None
        hard_ok = (maxima[i]["hard_penetration_m"] <= 0.0005) if reports_observed else None
        # Pose retention is evidence in its own right. Missing collision telemetry
        # cannot establish either zero penetration or a successful force limit.
        retained = bool(airborne and seated)
        if case["mode"] == "hover_2mm":
            interpretation = "unexpected non-contact retention" if airborne else "no non-contact retention observed"
        elif case["mode"] == "misaligned_2mm":
            interpretation = ("lower brick physically self-aligned and retained" if retained
                              else "no correctly seated retention after offset approach")
        else:
            interpretation = "aligned material retention observed" if retained else "aligned material probe failed"
        results["cases"].append({
            "case": case["name"], "interpretation": interpretation,
            "retained_with_correct_geometry_for_final_1s": retained,
            "airborne_for_final_1s": airborne, "correct_geometry_for_final_1s": seated,
            "descent_limited": stopped_gaps[i] is not None,
            "last_metrics": last[-1], "contact_diagnostics": diagnostics,
            "contact_reports_observed": reports_observed,
            "brick_pair_contact_reports_observed": pair_reports_observed,
            "hard_collision_validation": ("unavailable" if hard_ok is None else
                                          "passed" if hard_ok else "failed"),
            "retention_and_hard_collision_validation_passed": retained and hard_ok is True,
            "normal_force_limit_status": ("observed brick-pair reports used to limit descent"
                                          if pair_reports_observed else "inactive: no brick-pair contact reports"),
        })
    (out / "summary.json").write_text(json.dumps(results, indent=2) + "\n")
    del lower_view, upper_view, tensor_sim
    sim.stop()
    return results


if __name__ == "__main__":
    raise SystemExit(main())
