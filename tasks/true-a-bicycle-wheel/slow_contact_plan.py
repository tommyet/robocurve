"""Compile a slower first-quarter diagnostic after measured native tracking lag.

The first160 actions are unchanged. Later actions use the same tool centre,
square engagement,90-degree turn and ordinary robot limits. Settling holds and
longer motions give the native motors time to follow; no object forces change.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

from motion_plan import Compiler, load
from plan_turns import nominal_nipple, rz


def compile_slow_contact(source):
    from yam_arena.constants import READY, SHOULDER, WRIST, GRIPPER, FINGER_OPEN
    plan, actions = load(source)
    if plan['frames'][159]['stage'] != 'Approach nipple 0':
        raise ValueError('Expected the verified160-action approach prefix')
    c = Compiler()
    c.frames = [dict(frame) for frame in plan['frames'][:160]]
    c.audit = [entry for entry in plan['kinematic_audit']
               if entry['stage'] in {frame['stage'] for frame in c.frames}]
    a = actions[159]
    c.q = {'left': a[:6].copy(), 'right': a[7:13].copy()}
    c.opening = {'left': float(a[6]), 'right': float(a[13])}
    calibration = plan['held_grasp_calibration']
    c.tool_tcp = np.asarray(calibration['tcp_position_in_tool_m'])
    c.grip = np.asarray(calibration['tcp_rotation_in_tool'])
    clock = plan['wheel_clocking_deg']
    centre, n = nominal_nipple(0, np.deg2rad(plan['nipple_flat_phase_deg']), np.deg2rad(clock))
    R0 = n[:, [1, 2, 0]] @ np.diag((1., -1., -1.)) @ rz(np.pi)
    R1 = R0 @ rz(np.pi / 2)
    def tcp(p, R):
        return p + R @ c.tool_tcp, R @ c.grip
    def segment(label, seconds, **kwargs):
        before = len(c.frames)
        c.segment(label, seconds, **kwargs)
        for frame in c.frames[before:]:
            frame['nominal_wheel_clocking_deg'] = clock
    segment('Approach nipple 0 settle', 1.5)
    segment('Nipple 0 quarter 1 insert', 1.5, targets={'right': tcp(centre, R0)})
    segment('Nipple 0 quarter 1 insertion settle', 1.5)
    segment('Nipple 0 quarter 1 tighten', 4.,
            tool_path=lambda u: (centre, R0 @ rz(u * np.pi / 2)))
    segment('Nipple 0 quarter 1 tightening settle', 1.)
    withdrawn = centre - .010 * R1[:, 1]
    segment('Nipple 0 quarter 1 disengage', 1., targets={'right': tcp(withdrawn, R1)})
    segment('Nipple 0 quarter 1 clear front', .5,
            targets={'right': tcp(withdrawn - np.array((.045, 0., 0.)), R1)})
    commands = np.asarray([np.r_[READY, 1., READY, 1.]] + [f['action14'] for f in c.frames])
    limits = np.tile(np.array([SHOULDER['velocity']/20]*3 + [WRIST['velocity']/20]*3 +
                             [GRIPPER['velocity']/abs(FINGER_OPEN)/20]), 2)
    ratio = float(np.max(np.abs(np.diff(commands, axis=0))/limits))
    if ratio > 1.001:
        raise ValueError('Ordinary command speed exceeded')
    result = dict(plan)
    result.update(frames=c.frames, kinematic_audit=c.audit, action_count=len(c.frames),
                  seconds=len(c.frames)/20, max_speed_fraction=ratio,
                  requested_stage='slow_first_quarter_diagnostic', compile_success=True,
                  limitations=['Native091 shows trajectory lag and incomplete tightening.',
                               'This is a new unvalidated diagnostic, not a task demonstration.'],
                  base_plan_sha256=hashlib.sha256(Path(source).read_bytes()).hexdigest())
    result['source_sha256'] = dict(plan['source_sha256'])
    result['source_sha256']['slow_contact_plan.py'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    result = compile_slow_contact(a.source)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('compile_success', 'action_count', 'seconds', 'max_speed_fraction')}))
