"""Offline second-peg continuation candidate with the arm roles exchanged.

This fragment requires a separately demonstrated right-hand fabric grasp.
It is not a runnable whole episode. Reflect the first peg route across the
scene midplane so the left arm opens the negative-y spare peg, keeping its
palm clear of the negative-y post. Native cloth presentation is still needed.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np


def compile_fragment(first_plan):
    from yam_arena import ik,station
    from yam_arena.constants import READY,SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    reflect=np.diag((1.,-1.,1.));finger_swap=np.diag((-1.,1.,1.))
    q={side:np.asarray(READY,float) for side in ('left','right')};frames=[];errors=[]
    for index,f in enumerate(first_plan['frames'][300:]):
        original=np.asarray(f['action14']);a=np.empty(14)
        for i,side,source in ((0,'left','right'),(1,'right','left')):
            j=1-i;position,rotation=ik.tcp_pose(original[j*7:j*7+6],station.BASES[source]);position=reflect@position;rotation=reflect@rotation@finger_swap
            q[side],pe,re=ik.solve(position,ik.matrix_to_quat_xyzw(rotation),q[side],base_pos=station.BASES[side],iters=600 if index==0 else 100)
            if pe>.004 or re>.04:errors.append(dict(step=index+1,side=side,stage=f['stage'],position_error_m=float(pe),rotation_error_rad=float(re)))
            a[i*7:i*7+6]=q[side];a[i*7+6]=original[j*7+6]
        frames.append(dict(action14=a.tolist(),stage='second clip: '+f['stage']))
    limit=np.tile([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20],2)
    deltas=np.abs(np.diff(np.asarray([f['action14'] for f in frames]),axis=0))/limit
    return dict(schema='cloth-fixed-motion-fragment-v1',kind='unvalidated_continuation_not_episode',control_hz=20,score=None,
        action_count=len(frames),frames=frames,kinematic_failures=errors,max_normal_joint_speed_ratio=float(deltas.max()),
        line_pegs_required=True,peg_hand='left',
        clip_servo_window=[int(x)-300 for x in first_plan.get('clip_servo_window',[820,940])],
        joint_feedback_from=int(first_plan.get('requires_joint_feedback_from',700))-300,
        feedback='Candidate ordinary fixed continuation; missing right-hand state-assisted cloth pickup prefix',
        requires='Retained first clip at+y; unused spare at−y; right hand physically holding opposite cloth region; left hand clear before first fragment pose.',
        do_not_run_reason='Not a whole episode: missing native right-hand fabric presentation, continuity into initial fragment pose, and full contact validation.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('first_plan',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();plan=compile_fragment(json.loads(a.first_plan.read_text()));plan['first_plan_sha256']=hashlib.sha256(a.first_plan.read_bytes()).hexdigest();a.out.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(dict(actions=plan['action_count'],ik_failures=len(plan['kinematic_failures']),max_speed_ratio=plan['max_normal_joint_speed_ratio']),indent=2))
