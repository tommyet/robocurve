"""Unvalidated local candidate after the measured lateral-pickup miss.

This pure planner re-observes the native garment at action100 and aims at the
continuous finger-pad region instead of the central notch. It is not wired
into the runner or claimed to grasp fabric. No simulation state is written.
"""
import copy
import hashlib
import numpy as np


def reobserve(reference, measured_action, rest, nodes):
    from yam_arena import ik, station
    from yam_arena.constants import READY, SHOULDER, WRIST, GRIPPER, FINGER_OPEN
    from fixed_motion import ROTATIONS
    rest = np.asarray(rest, float)
    nodes = np.asarray(nodes, float)
    observed = np.asarray(measured_action, float)
    if rest.shape != nodes.shape or observed.shape != (14,):
        raise ValueError('Expected native garment nodes and fourteen measured joints')
    if not np.isfinite(nodes).all() or not np.isfinite(observed).all():
        raise ValueError('Nonfinite measured candidate input')
    arms = {}
    patches = {}
    audits = []
    for index, (side, hx, sign) in enumerate((('left', -.12, 1.), ('right', .12, -1.))):
        ids = (abs(rest[:, 0] - hx) < .011) & (rest[:, 1] < .011)
        front = ids & (rest[:, 2] > 0)
        uv = rest[front, :2]
        points = nodes[front]
        fit = np.linalg.lstsq(np.c_[uv - uv.mean(0), np.ones(len(uv))],
                              points - points.mean(0), rcond=None)[0]
        width = fit[0] / np.linalg.norm(fit[0])
        normal = np.cross(width, fit[1])
        normal /= np.linalg.norm(normal)
        approach, closing = sign * width, sign * normal
        rotation = np.column_stack((closing, np.cross(approach, closing), approach))
        angle = np.deg2rad(-10. if side == 'right' else 0.)
        rotation = rotation @ np.array(((1., 0., 0.),
            (0., np.cos(angle), -np.sin(angle)), (0., np.sin(angle), np.cos(angle))))
        center = nodes[ids].mean(0)
        # Native hulls have no pad at local(y=0,z=-10mm). Both opposed pads
        # have continuous surfaces around(y=-8mm,z=-10mm), measured in125.
        desired_local = np.array((0., -.008, -.010))
        target = center - rotation @ desired_local
        q = observed[7 * index:7 * index + 6].copy()
        opening = float(observed[7 * index + 6])
        frames = []
        schedule = [
            (2., target, .2, rotation, 're-observed insertion at continuous pads'),
            (1., target, .018, rotation, 'ordinary finite pinch at continuous pads'),
            (1., np.array((.1494, target[1], target[2])), .018, rotation,
             'pull forward clear of support'),
            (1., np.array((.1494, sign * .115, .898 if side == 'left' else .902)),
             .018, ROTATIONS[side], 'turn held hem in clear space')]
        for seconds, position, grip, orientation, label in schedule:
            p0, r0 = ik.tcp_pose(q, station.BASES[side])
            opening0 = opening
            maximum_position_error = maximum_rotation_error = 0.
            for k in range(1, round(seconds * 20) + 1):
                fraction = ik.smoothstep(k / (seconds * 20))
                q, pe, re = ik.solve(p0 + fraction * (position - p0),
                    ik.matrix_to_quat_xyzw(ik.slerp_matrix(r0, orientation, fraction)),
                    q, base_pos=station.BASES[side], iters=120)
                maximum_position_error = max(maximum_position_error, float(pe))
                maximum_rotation_error = max(maximum_rotation_error, float(re))
                opening = opening0 + fraction * (grip - opening0)
                frames.append(dict(action=np.r_[q, opening].tolist(), stage=label))
            audits.append(dict(side=side, stage=label,
                max_position_error_m=maximum_position_error,
                max_rotation_error_rad=maximum_rotation_error))
            if maximum_position_error > .004 or maximum_rotation_error > .04:
                raise ValueError('Candidate pose unreachable: ' + repr(audits[-1]))
        arms[side] = frames
        patches[side] = dict(material_node_ids=np.flatnonzero(ids).tolist(),
            observed_center_m=center.tolist(), target_tcp_m=target.tolist(),
            rotation=rotation.tolist(), desired_patch_local_m=desired_local.tolist())
    result = copy.deepcopy(reference)
    result['frames'][100:200] = [dict(action14=a['action'] + b['action'], stage=a['stage'])
                               for a, b in zip(arms['left'], arms['right'])]
    actions = np.array([np.r_[READY, 1., READY, 1.]] +
                       [f['action14'] for f in result['frames']])
    limits = np.tile([SHOULDER['velocity'] / 20] * 3 + [WRIST['velocity'] / 20] * 3 +
                     [GRIPPER['velocity'] / abs(FINGER_OPEN) / 20], 2)
    if np.any(abs(np.diff(actions, axis=0)) > limits * 1.001):
        raise ValueError('Candidate exceeds ordinary action speeds')
    result['candidate_status'] = 'local-only; not wired or native tested'
    result['reobservation_at_action'] = 100
    result['pad_candidate_calibration'] = dict(patches=patches, kinematics=audits,
        input_nodes_sha256=hashlib.sha256(np.ascontiguousarray(nodes).tobytes()).hexdigest(),
        state_writes=False)
    return result
