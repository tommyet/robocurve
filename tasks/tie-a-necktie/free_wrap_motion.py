"""Offline candidate: wrap the wide end around a freely hanging narrow tail.

The first 560 ordinary actions preserve the native handoff. The unused hand
withdraws before the wide tip crosses. This is a physical technique candidate,
not a demonstrated wrap or knot; no material positions drive the controller.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def compile_free_wrap():
    from handoff_motion import compile_handoff
    from cross_motion import yaw_rotation
    from yam_arena import ik,station
    from yam_arena.constants import READY,SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    prior=compile_handoff();frames=prior['frames'][:560]
    action=np.asarray(frames[-1]['action14']);q=action[:6].copy();right=action[7:13].copy()
    for k in range(1,41):
        t=ik.smoothstep(k/40)
        frames.append(dict(action14=np.r_[q,0.,right+t*(READY-right),1.].tolist(),stage='withdraw unused hand'))
    schedule=[
        (4.,'cross wide tip in front of free narrow tail',(.27,.21,1.0),160.),
        (3.,'carry wide tip outside narrow tail',(.445,.21,1.0),90.),
        (3.,'pass wide tip behind narrow tail',(.445,0.,1.0),90.),
        (3.,'bring wide tip to front',(.27,0.,1.0),90.),
        (3.,'lay wide end across front wrap',(.27,.21,1.0),160.),
        (3.,'hold candidate wrap',(.27,.21,1.0),160.),
    ];audits=[]
    for seconds,label,position,yaw in schedule:
        p0,r0=ik.tcp_pose(q,station.BASES['left']);errors=[0.,0.]
        for k in range(1,round(seconds*20)+1):
            t=ik.smoothstep(k/(seconds*20));target=p0+t*(np.asarray(position)-p0)
            rotation=ik.slerp_matrix(r0,yaw_rotation(yaw),t)
            q,pe,re=ik.solve(target,ik.matrix_to_quat_xyzw(rotation),q,base_pos=station.BASES['left'],iters=100)
            errors[0]=max(errors[0],float(pe));errors[1]=max(errors[1],float(re))
            frames.append(dict(action14=np.r_[q,0.,READY,1.].tolist(),stage=label))
        audits.append(dict(side='left',stage=label,seconds=seconds,target_xyz_m=list(position),
                           max_position_error_m=errors[0],max_rotation_error_rad=errors[1]))
    actions=np.array([np.r_[READY,1.,READY,1.]]+[f['action14'] for f in frames])
    limit=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
    if np.any(abs(np.diff(actions,axis=0))>limit*1.001):raise ValueError('Normal joint speed exceeded')
    bad=[a for a in audits if a['max_position_error_m']>.004 or a['max_rotation_error_rad']>.04]
    if bad:raise ValueError('Wrap IK gate failed: '+json.dumps(bad))
    return dict(schema='cloth-fixed-motion-v1',kind='diagnostic_not_submission_demo',control_hz=20,score=None,
        feedback='none; frozen ordinary joint commands only',action_count=len(frames),frames=frames,
        kinematic_audit=audits,fixture_source_sha256=hashlib.sha256(Path(__file__).with_name('layout.py').read_bytes()).hexdigest(),
        waypoint_evidence='First560 actions preserve native batch022 wide-tip handoff. Free narrow strand initially supported only by collar friction/gravity. No online cloth feedback.',
        do_not_run_reason='Awaiting full commanded collision-hull rejection audit.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();plan=compile_free_wrap();args.out.write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(dict(actions=plan['action_count'],seconds=plan['action_count']/20,
        max_position_error_m=max(a['max_position_error_m'] for a in plan['kinematic_audit']),
        max_rotation_error_rad=max(a['max_rotation_error_rad'] for a in plan['kinematic_audit'])),indent=2))
