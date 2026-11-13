"""Compile one complete quarter cycle in the explicit relocated diagnostic.

This uses a recorded grasp only to plan ordinary robot targets. No live object
state is changed. The complete repair and a native run remain unvalidated.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from motion_plan import Compiler, load
from plan_turns import nominal_nipple, rz
from thread_coupling import rotation
from fixture_layout import RELOCATED, offset


def validate_source(source):
    if (source.get('fixture_layout', 'reference') != 'reference' or
        source.get('wheel_clocking_deg') != 55. or
        source.get('nipple_flat_phase_deg') != 45. or
        source.get('reset_profile') != 'two-defect-candidate'):
        raise ValueError('Relocation requires the reference 55-degree wheel, 45-degree flats and two-defect reset')


def compile_relocated(source, trace):
    from yam_arena import ik, station
    from yam_arena.constants import READY, SHOULDER, WRIST, GRIPPER, FINGER_OPEN
    old, _ = load(source)
    validate_source(old)
    if old['frames'][81]['stage'] != 'Hold pickup for inspection':
        raise ValueError('Expected the82-action native-tested pickup prefix')
    with gzip.open(trace, 'rt') as stream:
        rows = {row['step']: row for row in map(json.loads, stream)}
    ref = rows[84]
    shift = offset(RELOCATED)
    c = Compiler()
    q = np.array(READY)
    # Preserve every right-hand pickup command. Re-solve the relocated left
    # approach smoothly from READY, then retain its new rim-holding pose.
    for i, frame in enumerate(old['frames'][:82]):
        a = np.asarray(frame['action14']).copy()
        p, R = ik.tcp_pose(a[:6], station.BASES['left'])
        p += shift*ik.smoothstep(min((i+1)/30, 1.))
        q, pe, re = ik.solve(p, ik.matrix_to_quat_xyzw(R), q, station.BASES['left'],
                             iters=500, damping=.008, tol=1e-7)
        if pe > .0001 or re > .001:
            raise ValueError(f'Relocated left pickup unreachable at{i+1}: {pe},{re}')
        a[:6] = q
        c.frames.append(dict(frame, action14=a.tolist()))
    a = np.array(c.frames[-1]['action14'])
    c.q = {'left': a[:6], 'right': a[7:13]}
    c.opening = {'left': a[6], 'right': a[13]}
    wi = ref['body_names'].index('wrench')
    pose = np.asarray(ref['body_poses'][wi])
    R = rotation(pose[3:])
    p, tcp_R = ik.tcp_pose(np.asarray(ref['joint_pos'])[7:13], station.BASES['right'])
    gp, gR = R.T@(p-pose[:3]), R.T@tcp_R
    c.tool_tcp, c.grip = gp, gR
    centre, n = nominal_nipple(0, np.deg2rad(45), np.deg2rad(55))
    centre += shift
    R0 = n[:, [1, 2, 0]]@np.diag((1., -1., -1.))@rz(np.pi)
    R1 = R0@rz(np.pi/2)
    tcp = lambda p, R: (p+R@gp, R@gR)
    park = np.array((.23, -.035, .87))
    c.segment('Move wrench to front workspace', 1., targets={'right': tcp(park, np.eye(3))})
    c.segment('Orient the wrench in front of wheel', 2.,
              tool_path=lambda u: (park, ik.slerp_matrix(np.eye(3), R0, u)))
    clear = centre-.022*R0[:, 1]-np.array((.045, 0., 0.))
    before = len(c.frames)
    c.segment('Clear approach nipple 0', 2., targets={'right': tcp(clear, R0)}, joint=True)
    count = len(c.frames)-before
    for i in range(count):
        c.frames[before+i]['nipple_feedback_fraction'] = float(ik.smoothstep((i+1)/count))
    c.segment('Approach nipple 0 high lead', 2., targets={'right': tcp(centre-.022*R0[:, 1], R0)})
    c.segment('Approach nipple 0 high lead settle', 1.5)
    c.segment('Approach nipple 0', 3., targets={'right': tcp(centre-.014*R0[:, 1], R0)})
    c.segment('Approach nipple 0 settle', 1.5)
    c.segment('Nipple 0 quarter 1 insert', 3., targets={'right': tcp(centre, R0)})
    c.segment('Nipple 0 quarter 1 insertion settle', 1.5)
    c.segment('Nipple 0 quarter 1 tighten', 4., tool_path=lambda u: (centre, R0@rz(u*np.pi/2)))
    c.segment('Nipple 0 quarter 1 tightening settle', 1.)
    withdrawn = centre-.016*R1[:, 1]
    c.segment('Nipple 0 quarter 1 disengage', 3., targets={'right': tcp(withdrawn, R1)})
    c.segment('Nipple 0 quarter 1 disengagement settle', 1.5)
    c.segment('Nipple 0 quarter 1 clear front', 1.5,
              targets={'right': tcp(withdrawn-np.array((.045, 0., 0.)), R1)})
    commands = np.asarray([np.r_[READY, 1., READY, 1.]]+[f['action14'] for f in c.frames])
    limits = np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+
                             [GRIPPER['velocity']/abs(FINGER_OPEN)/20]), 2)
    fraction = float(np.max(np.abs(np.diff(commands, axis=0))/limits))
    if fraction > 1.001:
        raise ValueError('Ordinary robot command-speed limit exceeded')
    for frame in c.frames:
        frame['nominal_wheel_clocking_deg'] = 55.
    result = dict(old, frames=c.frames, kinematic_audit=c.audit,
        action_count=len(c.frames), seconds=len(c.frames)/20, max_speed_fraction=fraction,
        fixture_layout=RELOCATED, fixture_translation_m=shift.tolist(),
        native_compatible=True, native_validated=False,
        requested_stage='relocated_first_quarter_diagnostic', compile_success=True,
        base_plan_sha256=hashlib.sha256(Path(source).read_bytes()).hexdigest(),
        measured_grasp_trace_sha256=hashlib.sha256(Path(trace).read_bytes()).hexdigest(),
        held_grasp_calibration=dict(source='Recorded native grasp at action84', applies_from_step=83,
            tcp_position_in_tool_m=gp.tolist(), tcp_rotation_in_tool=gR.tolist()),
        limitations=['No native relocated-scene, pickup, contact or withdrawal proof.',
                     'One quarter cycle, not a complete repair or released revolution.'])
    names=('relocated_plan.py','fixture_layout.py','wheel_scene.py','motion_plan.py','plan_turns.py','tool_pose_servo.py')
    result['source_sha256'] = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                               for name in names}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--measured-trace', type=Path, required=True)
    parser.add_argument('--relocated-fixture-diagnostic', action='store_true', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = compile_relocated(args.source, args.measured_trace)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in ('action_count','seconds','max_speed_fraction','fixture_layout')}))
