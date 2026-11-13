"""Offline continuation candidate: stabilize narrow end and cross the wide end.

This is not yet released for native use. The handoff and the narrow-end position
must first be checked in a native trajectory. No cloth geometry drives actions.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def yaw_rotation(degrees):
    a=np.deg2rad(degrees)
    return np.array([[np.cos(a),0.,np.sin(a)],[-np.sin(a),0.,np.cos(a)],[0.,-1.,0.]])


def compile_cross():
    from handoff_motion import compile_handoff
    from yam_arena import ik,station
    from yam_arena.constants import READY,SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    prior=compile_handoff();frames=prior['frames'][:560]
    action=np.asarray(frames[-1]['action14']);q={s:action[7*i:7*i+6].copy() for i,s in enumerate(('left','right'))}
    opening={s:float(action[7*i+6]) for i,s in enumerate(('left','right'))};audits=[]
    schedule=[
        (2.,'raise wide tip clear for second grip',{'left':((.25,-.15,1.15),0.,180.)}),
        (2.,'approach narrow strand',{'right':((.357,.0204,.956),.6,30.)}),
        (2.,'align narrow strand pinch',{'right':((.407,.107,.956),.6,30.)}),
        (1.,'grasp narrow strand',{'right':((.407,.107,.956),0.,30.)}),
        (2.,'position held narrow strand',{'right':((.34,-.03,.95),0.,30.)}),
        (3.,'carry wide tip across front',{'left':((.25,.18,1.15),0.,150.)}),
        (2.,'lower wide tip into front crossing',{'left':((.25,.18,1.0),0.,150.)}),
        (3.,'hold both strands after crossing',{}),
    ]
    for seconds,label,targets in schedule:
        poses={s:ik.tcp_pose(q[s],station.BASES[s]) for s in q};start_open=opening.copy();errors={s:[0.,0.] for s in targets}
        for k in range(1,round(seconds*20)+1):
            t=ik.smoothstep(k/(seconds*20))
            for side,(position,target_opening,yaw) in targets.items():
                p0,r0=poses[side];target=p0+t*(np.asarray(position)-p0);rotation=ik.slerp_matrix(r0,yaw_rotation(yaw),t)
                q[side],pe,re=ik.solve(target,ik.matrix_to_quat_xyzw(rotation),q[side],base_pos=station.BASES[side],iters=60)
                errors[side][0]=max(errors[side][0],float(pe));errors[side][1]=max(errors[side][1],float(re))
                opening[side]=start_open[side]+t*(target_opening-start_open[side])
            frames.append(dict(action14=np.r_[q['left'],opening['left'],q['right'],opening['right']].tolist(),stage=label))
        audits.extend(dict(side=s,stage=label,seconds=seconds,max_position_error_m=e[0],max_rotation_error_rad=e[1]) for s,e in errors.items())
    actions=np.array([np.r_[READY,1.,READY,1.]]+[f['action14'] for f in frames])
    limit=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
    if np.any(abs(np.diff(actions,axis=0))>limit*1.001):raise ValueError('Normal joint speed exceeded')
    bad=[a for a in audits if a['max_position_error_m']>.004 or a['max_rotation_error_rad']>.04]
    if bad:raise ValueError('Crossing IK gate failed: '+json.dumps(bad))
    return dict(schema='cloth-fixed-motion-v1',kind='diagnostic_not_submission_demo',control_hz=20,score=None,
        feedback='none; frozen ordinary joint commands only',action_count=len(frames),frames=frames,
        kinematic_audit=audits,fixture_source_sha256=hashlib.sha256(Path(__file__).with_name('layout.py').read_bytes()).hexdigest(),
        waypoint_evidence='First560 actions preserve retained native batch022 handoff. Narrow position measured offline from batch022 s=1.0m. No online cloth feedback.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();plan=compile_cross();args.out.write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(dict(actions=plan['action_count'],seconds=plan['action_count']/20,
        max_position_error_m=max(a['max_position_error_m'] for a in plan['kinematic_audit']),
        max_rotation_error_rad=max(a['max_rotation_error_rad'] for a in plan['kinematic_audit'])),indent=2))
