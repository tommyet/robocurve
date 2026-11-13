"""Frozen contact-only peg pickup/squeeze/release candidate for the raised rests.

The ordinary stepped rests passed passive native settling in batch020.
The controller never sets jaw angles, alters the spring or attaches the peg.
"""
import argparse
import json
from pathlib import Path
import numpy as np


def compile_peg():
    from fixed_motion import front_rotation
    from yam_arena import ik,station
    from yam_arena.constants import READY,FINGER_OPEN,SHOULDER,WRIST,GRIPPER
    from scene import PHYSICS_HZ,SUPPORT_BOARD_THICKNESS
    rotation=front_rotation(-15.,'right')
    schedule=[
        (3.,(.240,-.30,.894),.5,'joint approach ahead of peg handles'),
        (2.,(.292,-.30,.880),.5,'insert open fingers around peg handles'),
        (1.,(.292,-.30,.880),0.,'squeeze handles through real hinge'),
        (2.,(.280,-.30,1.020),0.,'lift held open peg off rest'),
        (2.,(.280,-.30,1.020),0.,'hold lifted peg'),
        (2.,(.292,-.30,.880),0.,'replace peg on ordinary rest'),
        (1.,(.292,-.30,.880),.5,'release peg handles'),
        (2.,(.240,-.30,.894),.5,'withdraw empty gripper'),
    ]
    q=np.array(READY,dtype=float);opening=1.;frames=[];audits=[]
    for index,(seconds,position,target_opening,label) in enumerate(schedule):
        p0,r0=ik.tcp_pose(q,station.BASES['right']);q0=q.copy();o0=opening;goal=None;maxpe=maxre=0.
        if index==0:
            goal,pe,re=ik.solve(position,ik.matrix_to_quat_xyzw(rotation),q,base_pos=station.BASES['right'],iters=400)
            if pe>.004 or re>.04:raise ValueError('Unreachable peg approach')
        for k in range(1,round(seconds*20)+1):
            t=ik.smoothstep(k/(seconds*20))
            if goal is not None:q=q0+t*(goal-q0);pe=re=0.
            else:
                target=p0+t*(np.asarray(position)-p0);r=ik.slerp_matrix(r0,rotation,t)
                q,pe,re=ik.solve(target,ik.matrix_to_quat_xyzw(r),q,base_pos=station.BASES['right'],iters=60)
            maxpe=max(maxpe,float(pe));maxre=max(maxre,float(re));opening=o0+t*(target_opening-o0)
            frames.append(dict(action14=np.r_[READY,1.,q,opening].tolist(),stage=label))
        audits.append(dict(stage=label,seconds=seconds,target_xyz_m=list(position),max_position_error_m=maxpe,max_rotation_error_rad=maxre))
    actions=np.array([np.r_[READY,1.,READY,1.]]+[f['action14'] for f in frames])
    limit=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
    if np.any(abs(np.diff(actions,axis=0))>limit*1.001):raise ValueError('Normal joint speed exceeded')
    if max(a['max_position_error_m'] for a in audits)>.004 or max(a['max_rotation_error_rad'] for a in audits)>.04:
        raise ValueError('Peg candidate fails ordinary IK gate')
    import hashlib
    return dict(schema='cloth-fixed-motion-v1',kind='diagnostic_not_submission_demo',control_hz=20,score=None,
        fixture_board_thickness_m=SUPPORT_BOARD_THICKNESS,physics_hz=PHYSICS_HZ,peg_rests_required=True,
        peg_rest_source_sha256=hashlib.sha256(Path(__file__).with_name('peg_rests.py').read_bytes()).hexdigest(),
        feedback='none; frozen ordinary joint commands only',action_count=len(frames),frames=frames,kinematic_audit=audits,
        source_waypoints='Declared ordinary stepped rests; native batch020 passive settling. Grasp still requires native confirmation.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();plan=compile_peg();args.out.write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(dict(actions=plan['action_count'],seconds=plan['action_count']/20,
        max_position_error_m=max(a['max_position_error_m'] for a in plan['kinematic_audit']),
        max_rotation_error_rad=max(a['max_rotation_error_rad'] for a in plan['kinematic_audit'])),indent=2))
