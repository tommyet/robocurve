"""Slow the last2mm of the paper brace without changing task physics.

Native093/094 showed rapid first contact while the wrist was still levelling.
This candidate pauses above the paper, lowers slowly, then resumes the same
remover path. It uses only ordinary robot commands and remains unvalidated.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from motion_plan import Compiler, load


def compile_gentle(source):
    from yam_arena import ik, station
    from yam_arena.constants import READY, SHOULDER, WRIST, GRIPPER, FINGER_OPEN
    plan, actions = load(source)
    if (plan['frames'][29]['stage'] != 'Approach remover and papers' or
            plan['frames'][45]['stage'] != 'Lower to handle and hold papers'):
        raise ValueError('Expected verified30-action approach and46-action lowering endpoints')
    c = Compiler()
    c.frames = [dict(f) for f in plan['frames'][:30]]
    a = actions[29]
    c.q = {'left': a[:6].copy(), 'right': a[7:13].copy()}
    c.opening = {'left': float(a[6]), 'right': float(a[13])}
    left = ik.tcp_pose(actions[45, :6], station.BASES['left'])
    right = ik.tcp_pose(actions[45, 7:13], station.BASES['right'])
    c.segment('Lower beside papers before gentle brace', .8,
              targets={'left': (left[0]+np.array((0.,0.,.002)),left[1]), 'right': right})
    c.segment('Level fingers2mm above papers', 1.)
    c.segment('Gently brace papers through final2mm', 1.5, targets={'left': left})
    c.segment('Settle the paper brace', .5)
    changed_end = len(c.frames)
    # At the shared endpoint the nominal target is unchanged. The microscopic
    # IK tolerance difference remains within ordinary speed limits below.
    c.frames.extend(dict(frame) for frame in plan['frames'][46:])
    commands = np.asarray([np.r_[READY,1.,READY,1.]]+[f['action14'] for f in c.frames])
    limits = np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+
                             [GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
    fraction = float(np.max(np.abs(np.diff(commands,axis=0))/limits))
    if fraction > 1.001:
        raise ValueError('Ordinary robot command speed exceeded')
    result = dict(plan)
    result.update(frames=c.frames, action_count=len(c.frames), seconds=len(c.frames)/20,
                  max_speed_fraction=fraction, requested_stage='gentle_brace_complete_candidate',
                  first_changed_action=31, last_changed_action=changed_end,
                  source_prefix_actions_replaced=46, unchanged_suffix_starts_at=changed_end+1,
                  base_plan_sha256=hashlib.sha256(Path(source).read_bytes()).hexdigest(),
                  limitations=['Native094 showed growing paper separation at first brace contact.',
                               'This slower touchdown and complete extraction remain unvalidated.'])
    result['kinematic_audit'] = c.audit
    result['source_sha256'] = dict(plan['source_sha256'])
    result['source_sha256']['gentle_touchdown_plan.py'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return result


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();plan=compile_gentle(a.source)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps({key:plan[key] for key in ('action_count','seconds','last_changed_action','max_speed_fraction')}))
