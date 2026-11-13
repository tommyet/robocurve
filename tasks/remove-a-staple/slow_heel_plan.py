"""Stage and settle the remover's last 6 mm of descent, with unchanged physics.

Native114 overshot the corrected heel target and compressed through both thin
sheets before insertion. This candidate changes robot timing only. It does not
prove contact validity or extraction, and must retain all native integrity checks.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from motion_plan import Compiler, load


def compile_slow_heel(source):
    from yam_arena import ik, station
    from yam_arena.constants import READY, SHOULDER, WRIST, GRIPPER, FINGER_OPEN
    plan, actions = load(source)
    if (len(actions) != 386 or
            plan['frames'][117]['stage'] != 'Approach supported side of crown' or
            plan['frames'][129]['stage'] != 'Lower the heel to its support' or
            plan['frames'][130]['stage'] != 'Slide the fork below the crown'):
        raise ValueError('Expected corrected386-action plan with118-action approach prefix')
    c = Compiler()
    c.frames = [dict(frame) for frame in plan['frames'][:118]]
    a = actions[117]
    c.q = {'left': a[:6].copy(), 'right': a[7:13].copy()}
    c.opening = {'left': float(a[6]), 'right': float(a[13])}
    target = ik.tcp_pose(actions[129, 7:13], station.BASES['right'])
    c.segment('Settle the heel6mm above paper', 1.5)
    c.segment('Lower the heel to1mm above paper', 2.,
              targets={'right': (target[0]+np.array((0., 0., .001)), target[1])})
    c.segment('Settle the heel1mm above paper', 1.)
    c.segment('Creep the heel onto paper', 5., targets={'right': target})
    c.segment('Settle the heel before insertion', 1.)
    replaced_end = len(c.frames)
    c.frames.extend(dict(frame) for frame in plan['frames'][130:])
    commands = np.asarray([np.r_[READY, 1., READY, 1.]]+
                          [frame['action14'] for frame in c.frames])
    limits = np.tile(np.array([SHOULDER['velocity']/20]*3+
                             [WRIST['velocity']/20]*3+
                             [GRIPPER['velocity']/abs(FINGER_OPEN)/20]), 2)
    fraction = float(np.max(np.abs(np.diff(commands, axis=0))/limits))
    if fraction > 1.001 or len(c.frames) > 600:
        raise ValueError('Ordinary actuator speed or30-second task limit exceeded')
    if not np.array_equal(commands[1:119], actions[:118]):
        raise AssertionError('Pickup/approach prefix changed')
    if not np.array_equal(commands[replaced_end+1:], actions[130:]):
        raise AssertionError('Insertion/extraction/release suffix changed')
    result = dict(plan)
    result.update(frames=c.frames, action_count=len(c.frames), seconds=len(c.frames)/20,
        max_speed_fraction=fraction, requested_stage='slow_heel_complete_candidate',
        first_changed_action=119, last_changed_action=replaced_end,
        unchanged_suffix_starts_at=replaced_end+1,
        replaced_source_actions=[119,130],
        base_plan_sha256=hashlib.sha256(Path(source).read_bytes()).hexdigest(),
        touchdown=dict(final_distance_m=.001, final_descent_seconds=5.,
                       quintic_peak_commanded_speed_m_s=.001/5*1.875,
                       hold_before_contact_seconds=1., hold_after_contact_seconds=1.),
        limitations=['Native114 heel overshot the upper-sheet target before insertion.',
                     'Only ordinary command timing changes; all materials and contact guards remain.',
                     'Slow touchdown, intact extraction and release still require native proof.'])
    result['released_tool'] = dict(plan['released_tool'])
    result['released_tool']['from_step'] += replaced_end-130
    # Preserve source audits while replacing only the modified descent audit.
    previous = plan['kinematic_audit']
    split = next(i for i, entry in enumerate(previous)
                 if entry['stage'] == 'Lower the heel to its support')
    result['kinematic_audit'] = previous[:split]+c.audit+previous[split+1:]
    result['source_sha256'] = dict(plan['source_sha256'])
    result['source_sha256']['slow_heel_plan.py'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = compile_slow_heel(args.source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in
                     ('action_count','seconds','max_speed_fraction','touchdown')}))
