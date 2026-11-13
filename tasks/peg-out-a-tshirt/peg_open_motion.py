"""Isolate ordinary handle opening with the shirt untouched on its support.

The reset and passive peg are unchanged. Only the right robot moves; this is
not a garment-hanging demo. The approach matches the released tilted feed plan.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np


def compile_open():
    from yam_arena import ik
    from yam_arena.constants import READY,SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    from scene import PHYSICS_HZ,SUPPORT_BOARD_THICKNESS
    source=Path(__file__).with_name('feed-tilted-plan.json');prior=json.loads(source.read_text())['frames']
    target=np.array(prior[479]['action14'][7:]);frames=[]
    def add(right,stage):frames.append(dict(action14=np.r_[READY,1.,right].tolist(),stage=stage))
    start=np.r_[READY,1.]
    for k in range(1,61):
        t=ik.smoothstep(k/60);add(start+t*(target-start),'joint approach below line')
    for f in prior[480:620]:add(f['action14'][7:],f['stage'])
    held=np.array(frames[-1]['action14'][7:])
    for _ in range(20):add(held,'observe opened jaw')
    for k in range(1,41):
        a=held.copy();a[6]=.6*ik.smoothstep(k/40);add(a,'ease empty peg closed')
    for f in prior[800:840]:add(f['action14'][7:],'withdraw from passive handles')
    for _ in range(40):add(frames[-1]['action14'][7:],'observe released empty peg')
    actions=np.asarray([np.r_[READY,1.,READY,1.]]+[f['action14'] for f in frames]);limit=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
    if np.any(abs(np.diff(actions,axis=0))>limit*1.001):raise ValueError('Normal joint speed exceeded')
    return dict(schema='cloth-fixed-motion-v1',kind='diagnostic_not_submission_demo',control_hz=20,score=None,
        fixture_board_thickness_m=SUPPORT_BOARD_THICKNESS,physics_hz=PHYSICS_HZ,line_pegs_required=True,
        line_peg_source_sha256=hashlib.sha256(Path(__file__).with_name('line_pegs.py').read_bytes()).hexdigest(),
        source_feed_plan_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        feedback='none; frozen ordinary joint commands only',action_count=len(frames),frames=frames,
        do_not_run_reason='Awaiting full commanded hull rejection audit; isolated peg opening only.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    plan=compile_open();args.out.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps({'actions':len(plan['frames'])}))
