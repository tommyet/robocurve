"""Measured free-hem pickup candidate after a real first clip.

This is a planning helper, not a validated continuation. It reads the actual
sewn garment and emits ordinary robot commands. It never writes cloth state,
adds an attachment, or treats a nearby hand as proof of a grasp.
"""
import numpy as np


def frame_candidates(rest, nodes):
    rest = np.asarray(rest, float)
    nodes = np.asarray(nodes, float)
    if rest.shape != nodes.shape or rest.ndim != 2 or rest.shape[1] != 3:
        raise ValueError('Matching material and native positions are required')
    ids = np.flatnonzero((abs(rest[:, 0] - .12) < .011) & (rest[:, 1] < .021))
    if len(ids) < 8 or not np.isfinite(nodes[ids]).all():
        raise ValueError('Missing finite opposite-hem material patch')
    material = rest[ids, :2] - rest[ids, :2].mean(0)
    center = nodes[ids].mean(0)
    tangent, _, rank, _ = np.linalg.lstsq(material, nodes[ids] - center, rcond=None)
    if rank != 2:
        raise ValueError('Free hem has no two-dimensional material neighborhood')
    width = tangent[0] / np.linalg.norm(tangent[0])
    normal = np.cross(tangent[0], tangent[1])
    if np.linalg.norm(normal) < 1e-6:
        raise ValueError('Collapsed free-hem patch has no pinch plane')
    normal /= np.linalg.norm(normal)
    approach = -width
    rotations = []
    for sign in (1., -1.):
        closing = sign * normal
        rotation = np.column_stack((closing, np.cross(approach, closing), approach))
        rotations.append(rotation.tolist())
    return dict(material_node_ids=ids.tolist(), center_m=center.tolist(),
        target_tcp_m=(center + .020 * approach).tolist(),
        pregrasp_tcp_m=(center - .050 * approach).tolist(),
        rotations=rotations, desired_material_depth_m=-.020)


def compile_candidate(start_action, rest, nodes, pinch=.018):
    """Reach/speed screen only; actual fixture and cloth screens remain required."""
    from yam_arena import ik, station
    from yam_arena.constants import SHOULDER, WRIST, GRIPPER, FINGER_OPEN
    if not 0. <= pinch <= .04:
        raise ValueError('Unexpected ordinary finger target')
    start = np.asarray(start_action, float)
    grasp = frame_candidates(rest, nodes)
    target = np.asarray(grasp['target_tcp_m'])
    pregrasp = np.asarray(grasp['pregrasp_tcp_m'])
    candidates = []
    for raw_rotation in grasp['rotations']:
        rotation = np.asarray(raw_rotation)
        q = start[7:13].copy()
        opening = float(start[13])
        frames, errors = [], []
        schedule = [(3., pregrasp, .6, 'approach outside the free hem'),
                    (2., target, .6, 'insert fingers around both cloth layers'),
                    (1.5, target, pinch, 'pinch the free hem'),
                    (1., target, pinch, 'hold the physical pickup for assessment')]
        for seconds, position, goal_opening, label in schedule:
            p0, r0 = ik.tcp_pose(q, station.BASES['right'])
            o0 = opening
            pe_max = re_max = 0.
            count = round(seconds * 20)
            for k in range(1, count + 1):
                t = ik.smoothstep(k / count)
                q, pe, re = ik.solve(p0 + t * (position - p0),
                    ik.matrix_to_quat_xyzw(ik.slerp_matrix(r0, rotation, t)),
                    q, base_pos=station.BASES['right'], iters=120)
                opening = o0 + t * (goal_opening - o0)
                action = start.copy()
                action[7:13], action[13] = q, opening
                frames.append(dict(action14=action.tolist(), stage=label))
                pe_max, re_max = max(pe_max, float(pe)), max(re_max, float(re))
            errors.append(dict(stage=label, position_error_m=pe_max, rotation_error_rad=re_max))
        limits = np.tile([SHOULDER['velocity']/20]*3 + [WRIST['velocity']/20]*3
            + [GRIPPER['velocity']/abs(FINGER_OPEN)/20], 2)
        values = np.asarray([start] + [f['action14'] for f in frames])
        ratio = float((abs(np.diff(values, axis=0)) / limits).max())
        if ratio <= 1.001 and all(e['position_error_m'] < .004 and e['rotation_error_rad'] < .04 for e in errors):
            candidates.append(dict(schema='cloth-fixed-motion-fragment-v1', frames=frames,
                action_count=len(frames), grasp=grasp, selected_rotation=raw_rotation,
                kinematic_audit=errors, maximum_speed_ratio=ratio, score=None,
                do_not_run_reason='Requires actual first-clip state, complete fixture/cloth clearance screen and physical retention assessment.'))
    if not candidates:
        raise ValueError('Neither equivalent physical pinch orientation is reachable')
    return candidates
