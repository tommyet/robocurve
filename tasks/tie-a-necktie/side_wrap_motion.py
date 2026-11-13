"""Candidate rear pass with the wrapping wrist beside the narrow strand.

The successful pickup, transfer and narrow pinch are frozen through native039
step880. Only the wide hand's approach orientation changes: its palm stays
beside/behind the strand instead of sweeping from the front into it. This is an
ordinary joint trajectory, not a cloth constraint or material-state controller.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np


def compile_side_wrap():
    from cross_motion import yaw_rotation
    from yam_arena import ik,station
    from yam_arena.constants import READY,SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    plan=json.loads(Path(__file__).with_name('deeper-bite-wrap-plan.json').read_text());frames=plan['frames'][:880];a=np.asarray(frames[-1]['action14']);q=a[:6].copy();right=a[7:13].copy();audits=[]
    schedule=[
        (4.,'orient palm beside strand at outside of rear pass',(.455,.210,.970),135.),
        (3.,'align side-facing wrist before crossing narrow strand',(.455,.132,.970),180.),
        (4.,'pass wide tip behind narrow strand with wrist clear',(.455,-.120,.970),180.),
        (4.,'carry wide end forward clear of narrow strand',(.270,-.120,.970),180.),
        (4.,'lay wide end across front wrap',(.270,.210,1.),160.),
        (3.,'observe candidate side-oriented wrap',(.270,.210,1.),160.),
    ]
    for seconds,label,position,yaw in schedule:
        p0,r0=ik.tcp_pose(q,station.BASES['left']);errors=[0.,0.]
        for k in range(1,round(seconds*20)+1):
            t=ik.smoothstep(k/(seconds*20));target=p0+t*(np.asarray(position)-p0);rotation=ik.slerp_matrix(r0,yaw_rotation(yaw),t)
            q,pe,re=ik.solve(target,ik.matrix_to_quat_xyzw(rotation),q,base_pos=station.BASES['left'],iters=100)
            errors[0]=max(errors[0],float(pe));errors[1]=max(errors[1],float(re));frames.append(dict(action14=np.r_[q,0.,right,0.].tolist(),stage=label))
        audits.append(dict(side='left',stage=label,seconds=seconds,target_xyz_m=list(position),max_position_error_m=errors[0],max_rotation_error_rad=errors[1]))
    actions=np.asarray([np.r_[READY,1.,READY,1.]]+[f['action14'] for f in frames]);limit=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
    if np.any(abs(np.diff(actions,axis=0))>limit*1.001):raise ValueError('Normal joint speed exceeded')
    bad=[a for a in audits if a['max_position_error_m']>.004 or a['max_rotation_error_rad']>.04]
    if bad:raise ValueError('Side-oriented wrap IK gate failed: '+json.dumps(bad))
    return dict(schema='cloth-fixed-motion-v1',kind='diagnostic_not_submission_demo',control_hz=20,score=None,
        fixture_source_sha256=hashlib.sha256(Path(__file__).with_name('layout.py').read_bytes()).hexdigest(),
        feedback='none; frozen ordinary joint commands only',action_count=len(frames),frames=frames,kinematic_audit=audits,
        waypoint_evidence='First880 commands match native039. The rear pass now uses a sideways wrist orientation, keeping its palm out of the narrow strand path. Four-second stages reduce contact transients. No geometry/material changes or online object-state feedback.',
        do_not_run_reason='Awaiting commanded full-hull rejection check and reviewed cloth-length budget; no retained wrap demonstrated.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);args=p.parse_args();plan=compile_side_wrap();args.out.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(dict(actions=plan['action_count'],max_position_error_m=max(a['max_position_error_m'] for a in plan['kinematic_audit'])),indent=2))
