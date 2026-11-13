"""Blocked continuation: physically raise the wide tip through the neck loop.

The prefix must first demonstrate a retained wrap. These are frozen ordinary
joint targets, not mesh motions or online material-state feedback.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np


def compile_neck_loop():
    from deeper_bite_wrap_motion import compile_deeper_bite
    from cross_motion import yaw_rotation
    from yam_arena import ik,station
    from yam_arena.constants import READY,SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    prior=compile_deeper_bite();frames=prior['frames'][:-60]
    a=np.asarray(frames[-1]['action14']);q=a[:6].copy();right=a[7:].copy();audits=[]
    schedule=[
        (3.,'bring wide tip outside front wrap',(.34,.21,1.06),90.),
        (3.,'approach neck loop from below',(.38,.10,1.02),90.),
        (4.,'raise held wide tip through neck loop',(.38,.035,1.19),90.),
        (3.,'present protruding wide tip above front band',(.30,.035,1.22),90.),
        (2.,'observe candidate neck loop passage',(.30,.035,1.22),90.),
    ]
    for seconds,label,position,yaw in schedule:
        p0,r0=ik.tcp_pose(q,station.BASES['left']);error=[0.,0.]
        for k in range(1,round(seconds*20)+1):
            t=ik.smoothstep(k/(seconds*20));target=p0+t*(np.asarray(position)-p0);rotation=ik.slerp_matrix(r0,yaw_rotation(yaw),t)
            q,pe,re=ik.solve(target,ik.matrix_to_quat_xyzw(rotation),q,base_pos=station.BASES['left'],iters=100)
            error[0]=max(error[0],float(pe));error[1]=max(error[1],float(re))
            frames.append(dict(action14=np.r_[q,0.,right].tolist(),stage=label))
        audits.append(dict(side='left',stage=label,seconds=seconds,target_xyz_m=list(position),max_position_error_m=error[0],max_rotation_error_rad=error[1]))
    actions=np.asarray([np.r_[READY,1.,READY,1.]]+[f['action14'] for f in frames]);limit=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
    if np.any(abs(np.diff(actions,axis=0))>limit*1.001):raise ValueError('Normal joint speed exceeded')
    bad=[a for a in audits if a['max_position_error_m']>.004 or a['max_rotation_error_rad']>.04]
    if bad:raise ValueError('Neck-loop IK gate failed: '+json.dumps(bad))
    return dict(schema='cloth-fixed-motion-v1',kind='diagnostic_not_submission_demo',control_hz=20,score=None,
        fixture_source_sha256=hashlib.sha256(Path(__file__).with_name('layout.py').read_bytes()).hexdigest(),
        feedback='none; frozen ordinary joint commands only',action_count=len(frames),frames=frames,kinematic_audit=audits,
        do_not_run_reason='Native retained-wrap prerequisite and full hull rejection audit are pending. This is not a demonstrated thread-through.',
        waypoint_evidence='Prepares the next physical stage on the primary four-in-hand path. Actual loop location must be reviewed from native retained-wrap evidence before release.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);args=p.parse_args();plan=compile_neck_loop()
    args.out.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps({'actions':plan['action_count'],'max_position_error_m':max(a['max_position_error_m'] for a in plan['kinematic_audit'])},indent=2))
