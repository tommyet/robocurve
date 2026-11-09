"""Normal joint commands for a first physical magnifier pickup experiment.

This planner never changes a tool pose, joint attachment, collision or force.
Its nominal tool pose is only an offline clearance assumption, not grasp proof.
The simulator must independently measure whether the tool actually follows.
"""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import numpy as np


def build_plan(*, control_hz=20, grasp_opening=0., audit=False):
    """Return JSON-ready phases and timed 14-value joint command frames.

    The action order is left six arm joints, left normalized finger opening,
    right six arm joints, right normalized opening. Openings range from 0 to 1.
    Set ``audit=True`` in the full local repository to check every planned
    control pose against conservative complete-link collision envelopes.
    """
    if control_hz != 20:
        raise ValueError("This first experimental plan is specified at 20 Hz")
    if not 0 <= grasp_opening <= 1:
        raise ValueError("grasp_opening must be between zero and one")
    from yam_arena import ik, station
    from yam_arena.constants import READY, TCP_OFFSET
    from yam_arena.urdf import quat_xyzw_to_matrix

    down = np.diag([1., -1., -1.])
    camera_position = np.array([.35, .05, .955])
    camera_rotation = np.diag([-1., -1., 1.])
    mount = station.wrist_camera("left")
    left_rotation = camera_rotation @ quat_xyzw_to_matrix(np.asarray(mount.rot_xyzw)).T
    left_tcp = camera_position - left_rotation @ np.asarray(mount.pos) + left_rotation @ np.asarray(TCP_OFFSET)
    q = {side: np.asarray(READY, dtype=float) for side in ("left", "right")}
    opening = {"left": 1., "right": 1.}
    frames, phases = [], []
    worst_position, worst_rotation = 0., 0.

    def frame(label, holding):
        action = np.r_[q["left"], opening["left"], q["right"], opening["right"]]
        frames.append({"time_s": len(frames) / control_hz, "phase": label,
                       "action14": action.tolist(), "nominal_tool_held": holding})

    frame("initial READY", False)

    def phase(label, seconds, *, side=None, position=None, rotation=None,
              finger_side=None, finger_target=None, holding=False):
        nonlocal worst_position, worst_rotation
        steps = round(seconds * control_hz)
        start_index = len(frames)
        if side is not None:
            start_position, start_rotation = ik.tcp_pose(q[side], station.BASES[side])
            goal_position, goal_rotation = np.asarray(position), np.asarray(rotation)
        first_finger = opening[finger_side] if finger_side else None
        local_position, local_rotation = 0., 0.
        for step in range(1, steps + 1):
            u = ik.smoothstep(step / steps)
            if side is not None:
                target = start_position + u * (goal_position - start_position)
                target_rotation = ik.slerp_matrix(start_rotation, goal_rotation, u)
                q[side], pe, re = ik.solve(target, ik.matrix_to_quat_xyzw(target_rotation),
                                            q[side], station.BASES[side], iters=100)
                local_position = max(local_position, pe)
                local_rotation = max(local_rotation, math.degrees(re))
            if finger_side:
                opening[finger_side] = first_finger + u * (finger_target - first_finger)
            for arm in ("left", "right"):
                if np.any(q[arm] < ik.LOWER - 1e-10) or np.any(q[arm] > ik.UPPER + 1e-10):
                    raise RuntimeError(f"Joint-limit violation in {label}")
            frame(label, holding)
        worst_position = max(worst_position, local_position)
        worst_rotation = max(worst_rotation, local_rotation)
        phases.append({"label": label, "duration_s": seconds,
                       "first_frame": start_index, "last_frame": len(frames) - 1,
                       "moving_arm": side, "worst_position_error_m": local_position,
                       "worst_orientation_error_deg": local_rotation})

    # Carry on the right side while the left arm gets into its camera pose.
    # The final approach slides the horizontal lens under the stationary camera.
    phase("close unused left fingers", .5, finger_side="left", finger_target=0.)
    phase("approach handle", 2., side="right", position=(.20, -.30, .865), rotation=down)
    phase("descend to handle", 1.5, side="right", position=(.20, -.30, .765), rotation=down)
    phase("grasp handle", 1., finger_side="right", finger_target=grasp_opening)
    phase("lift tool clear", 2., side="right", position=(.20, -.30, .958), rotation=down, holding=True)
    phase("carry to camera side", 2., side="right", position=(.35, -.20, .908), rotation=down, holding=True)
    phase("position inspection camera", 3., side="left", position=left_tcp,
          rotation=left_rotation, holding=True)
    phase("lower outside camera view", 1.5, side="right", position=(.35, -.20, .838), rotation=down, holding=True)
    phase("align lens under camera", 2., side="right", position=(.35, -.05, .838), rotation=down, holding=True)
    phase("hold inspection view", 3., holding=True)
    actions = np.asarray([f["action14"] for f in frames])
    angular_speed = np.abs(np.diff(actions[:, [0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12]], axis=0)) * control_hz
    limits = np.tile([5.5, 5.5, 5.5, 20., 20., 20.], 2)
    velocity_ratio = float(np.max(angular_speed / limits))
    report = {
        "scope": "First nominal pickup plan; physical retention and optical hold are unverified.",
        "control_hz": control_hz, "duration_s": frames[-1]["time_s"],
        "frames": frames, "phases": phases,
        "initial_tool": {"lens_center_m": [.20, -.20, .757],
                         "handle_center_m": [.20, -.27, .757], "yaw_deg": -90.,
                         "lens_offset_from_handle_local_m": [-.070, 0., 0.]},
        "target": {"card_center_m": [.35, .05, .755], "lens_center_m": [.35, .05, .830],
                   "left_camera_eye_m": camera_position.tolist(),
                   "left_camera_rotation_opengl": camera_rotation.tolist(),
                   "left_tcp_m": left_tcp.tolist(), "left_rotation": left_rotation.tolist(),
                   "left_q": q["left"].tolist(), "right_q": q["right"].tolist(),
                   "right_tcp_m": [.35, -.05, .838], "right_rotation": down.tolist()},
        "kinematic_checks": {"worst_position_error_m": worst_position,
                             "worst_orientation_error_deg": worst_rotation,
                             "maximum_joint_speed_rad_s": angular_speed.max(axis=0).tolist(),
                             "maximum_joint_speed_fraction_of_urdf_limit": velocity_ratio,
                             "joint_position_limits_pass": True,
                             "passed": worst_position <= .001 and worst_rotation <= 1 and velocity_ratio <= 1},
        "assumptions": [
            f"Right jaws close to {grasp_opening:.3f} normalized opening "
            f"({grasp_opening * 93.9:.3f} mm nominal gap); actual grip must be measured.",
            "Pickup TCP is 8 mm above the tool centre and fingers extend 13 mm below TCP.",
            "Handle and glass remain horizontal after a successful grasp; this is only an audit assumption.",
            "Only ordinary joint and gripper targets are issued; no object pose or grasp constraint is imposed.",
            "No commanded motion is a substitute for measured robot/tool trajectory or rendered optical benefit.",
        ],
    }
    report["collision_audit"] = _audit(report) if audit else {"complete": False, "reason": "not requested"}
    report["safe_for_physical_trial"] = bool(report["kinematic_checks"]["passed"] and
                                               report["collision_audit"].get("passed", False))
    return report


def _audit(plan):
    """Check sampled nominal poses; positive OBB gaps are conservative bounds."""
    from yam_arena import YAM_URDF, ik, station
    from yam_arena.constants import ARM_JOINTS, FINGER_OPEN
    from yam_arena.urdf import forward_kinematics

    helper = Path(__file__).resolve().parents[1] / "tasks/tie-overhand-knot/hand_geometry.py"
    if not helper.exists():
        raise RuntimeError("Local complete-link audit helper is absent; run audit in the full repository")
    spec = importlib.util.spec_from_file_location("magnifier_hand_geometry", helper)
    geometry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(geometry)

    def boxes(joints, side, finger):
        poses = forward_kinematics(YAM_URDF, {**dict(zip(ARM_JOINTS, joints)),
                                            "joint7": finger, "joint8": finger})
        for transform in poses.values():
            transform[:3, 3] += station.BASES[side]
        return geometry.boxes_from_link_poses(poses, include_all_links=True)

    def separation(a, b):
        ra, rb = np.asarray(a["rotation"]), np.asarray(b["rotation"])
        d = np.asarray(a["center"]) - np.asarray(b["center"])
        ha, hb = np.asarray(a["half_size"]), np.asarray(b["half_size"])
        axes = list(ra.T) + list(rb.T) + [np.cross(x, y) for x in ra.T for y in rb.T]
        axes = np.asarray([v / np.linalg.norm(v) for v in axes if np.linalg.norm(v) > 1e-9])
        return float((np.abs(axes @ d) - np.abs(axes @ ra) @ ha - np.abs(axes @ rb) @ hb).max())

    table = dict(rotation=np.eye(3).tolist(), center=station.TABLE_CENTER,
                 half_size=(np.asarray(station.TABLE_SIZE) / 2).tolist())
    minima, possible_overlaps = {}, []

    def record(kind, gap, frame, **labels):
        row = dict(kind=kind, lower_bound_m=gap, time_s=frame["time_s"], phase=frame["phase"], **labels)
        if kind not in minima or gap < minima[kind]["lower_bound_m"]:
            minima[kind] = row
        if gap <= 0:
            possible_overlaps.append(row)

    for frame in plan["frames"]:
        a = frame["action14"]
        left, right = boxes(a[:6], "left", a[6] * FINGER_OPEN), boxes(a[7:13], "right", a[13] * FINGER_OPEN)
        for lb in left:
            for rb in right:
                record("inter_arm", separation(lb, rb), frame, left=lb["link"], right=rb["link"])
        for side, arm_boxes in (("left", left), ("right", right)):
            for box in arm_boxes:
                if box["link"] not in ("base", "link1"):
                    record("moving_robot_table", separation(box, table), frame, side=side, link=box["link"])
        if frame["nominal_tool_held"]:
            tcp, _ = ik.tcp_pose(np.asarray(a[7:13]), station.BASES["right"])
            center = tcp + [0, .10, -.008]
            glass = dict(rotation=np.eye(3).tolist(), center=center.tolist(), half_size=[.03, .03, .005107])
            for side, arm_boxes in (("left", left), ("right", right)):
                for box in arm_boxes:
                    record("robot_nominal_glass", separation(box, glass), frame, side=side, link=box["link"])
            record("nominal_glass_table", separation(glass, table), frame)
    return {"complete": True, "passed": not possible_overlaps,
            "samples": len(plan["frames"]), "minima": minima,
            "possible_overlaps": possible_overlaps,
            "geometry": geometry.geometry_provenance(include_all_links=True),
            "limitations": ["Every 20 Hz commanded pose, not native physics substeps or actual tracking.",
                            "Complete-link OBBs overestimate geometry; any overlap needs mesh refinement.",
                            "Mounted base/link1 are excluded from table check.",
                            "Self-collision, camera housing, handle contacts, target board and dynamic tool motion are not audited."]}
