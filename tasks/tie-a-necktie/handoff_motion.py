"""Compile a physical wide-tip handoff candidate using offline run015 geometry.

The proven 240-action pickup prefix is preserved exactly. The receiving hand
closes around material 80 mm from the wide tip before the first hand opens.
This is a diagnostic candidate, not a demonstrated knot or successful transfer.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def compile_handoff():
    from fixed_motion import compile_contact
    from yam_arena import ik,station
    from yam_arena.constants import READY,FINGER_OPEN,SHOULDER,WRIST,GRIPPER
    prefix=compile_contact()
    frames=prefix['frames'][:240]
    actions=np.asarray(frames[-1]['action14'])
    q={side:actions[7*i:7*i+6].copy() for i,side in enumerate(('left','right'))}
    opening={side:float(actions[7*i+6]) for i,side in enumerate(('left','right'))}
    angle=np.deg2rad(30.)
    right_rotation=np.array([[np.cos(angle),0.,np.sin(angle)],[-np.sin(angle),0.,np.cos(angle)],[0.,-1.,0.]])
    rotations={'right':right_rotation,'left':right_rotation@np.diag((-1.,1.,-1.))}
    # A None target preserves the exact ordinary command of that hand.
    schedule=[
        (3.,'approach clear of collar shoulders',{'left':((.250,-.060,.863),.6,'joint')}),
        (2.,'align receiving fingers with wide strand',{'left':((.328,-.1104,.863),.6,'Cartesian')}),
        (2.,'receive wide tip region',{'left':((.278,-.197,.863),.6,'Cartesian')}),
        (1.,'pinch wide tip region',{'left':((.278,-.197,.863),0.,'Cartesian')}),
        (2.,'release original strand grasp',{'right':((.300,-.160,1.080),1.,'Cartesian')}),
        (2.,'clear original hand',{'right':((.240,-.220,1.130),1.,'Cartesian')}),
        (2.,'lift with receiving hand',{'left':((.300,-.140,1.030),0.,'Cartesian')}),
        (2.,'hold transferred tip',{}),
        (2.,'release transferred tip',{'left':((.300,-.140,1.030),1.,'Cartesian')}),
        (2.,'withdraw receiving hand',{'left':((.250,-.140,1.030),1.,'Cartesian')}),
    ]
    audits=[]
    for seconds,label,targets in schedule:
        startq={side:v.copy() for side,v in q.items()};starto=opening.copy()
        poses={side:ik.tcp_pose(q[side],station.BASES[side]) for side in q}
        goals={};errors={side:[0.,0.] for side in targets}
        for side,(position,target_opening,interpolation) in targets.items():
            if interpolation=='joint':
                goal,pe,re=ik.solve(position,ik.matrix_to_quat_xyzw(rotations[side]),q[side],base_pos=station.BASES[side],iters=400)
                if pe>.004 or re>.04:raise ValueError(f'Unreachable approach {side}: {pe}, {re}')
                goals[side]=goal
        for step in range(1,round(seconds*20)+1):
            fraction=ik.smoothstep(step/(seconds*20))
            for side,(position,target_opening,interpolation) in targets.items():
                if side in goals:q[side]=startq[side]+fraction*(goals[side]-startq[side]);pe=re=0.
                else:
                    p0,r0=poses[side]
                    target=p0+fraction*(np.asarray(position)-p0)
                    rotation=ik.slerp_matrix(r0,rotations[side],fraction)
                    q[side],pe,re=ik.solve(target,ik.matrix_to_quat_xyzw(rotation),q[side],base_pos=station.BASES[side],iters=60)
                errors[side][0]=max(errors[side][0],float(pe));errors[side][1]=max(errors[side][1],float(re))
                opening[side]=starto[side]+fraction*(target_opening-starto[side])
            frames.append(dict(action14=np.r_[q['left'],opening['left'],q['right'],opening['right']].tolist(),stage=label))
        audits.extend(dict(side=side,stage=label,seconds=seconds,target_xyz_m=list(targets[side][0]),
                           max_position_error_m=e[0],max_rotation_error_rad=e[1]) for side,e in errors.items())
    all_actions=np.array([np.r_[READY,1.,READY,1.]]+[f['action14'] for f in frames])
    limit=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
    if np.any(np.abs(np.diff(all_actions,axis=0))>limit*1.001):raise ValueError('Normal joint speed exceeded')
    if max(x['max_position_error_m'] for x in audits)>.004 or max(x['max_rotation_error_rad'] for x in audits)>.04:
        raise ValueError('Handoff exceeds 4 mm / 2.3 degree IK gate: '+json.dumps([a for a in audits if a['max_position_error_m']>.004 or a['max_rotation_error_rad']>.04]))
    return dict(schema='cloth-fixed-motion-v1',kind='diagnostic_not_submission_demo',control_hz=20,score=None,
        feedback='none; frozen ordinary joint commands only',action_count=len(frames),frames=frames,
        kinematic_audit=prefix['kinematic_audit'][:6]+audits,
        fixture_source_sha256=hashlib.sha256(Path(__file__).with_name('layout.py').read_bytes()).hexdigest(),
        waypoint_evidence='First240 actions of native batch015 grasp; receiving pose from offline s=0.08 m material measurement. No online cloth feedback.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();plan=compile_handoff();args.out.write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(dict(actions=plan['action_count'],seconds=plan['action_count']/20,
        max_position_error_m=max(x['max_position_error_m'] for x in plan['kinematic_audit']),
        max_rotation_error_rad=max(x['max_rotation_error_rad'] for x in plan['kinematic_audit'])),indent=2))
