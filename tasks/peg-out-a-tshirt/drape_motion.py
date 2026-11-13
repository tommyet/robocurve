"""Compile a higher physical lift and line-drape diagnostic after the proven pinch.

The first200 ordinary actions match the measured batch016 pickup. Cloth and
line contact must determine the resulting drape; no fabric state is prescribed.
Release controls are diagnostic only. This sequence does not operate the pegs.
"""
import argparse
import json
from pathlib import Path
import numpy as np


def compile_drape():
    from fixed_motion import compile_grasp,front_rotation
    from yam_arena import ik,station
    from yam_arena.constants import READY,SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    from scene import PHYSICS_HZ,SUPPORT_BOARD_THICKNESS
    prior=compile_grasp();frames=prior['frames'][:200]
    action=np.array(frames[-1]['action14']);q={s:action[i*7:i*7+6].copy() for i,s in enumerate(('left','right'))}
    opening={'left':0.,'right':0.};audits=[]
    schedule=[
        (3.,(.260,1.200),(0.,0.),'lift garment clear of laundry board'),
        (4.,(.560,1.200),(0.,0.),'carry held hem across the line'),
        (3.,(.560,1.145),(0.,0.),'lower hem beyond line'),
        (2.,(.560,1.145),(0.,0.),'hold physical line drape'),
        (2.,(.560,1.145),(0.,.5),'release right hem for drape test'),
        (2.,(.560,1.145),(0.,.5),'hold one-handed line drape'),
        (2.,(.560,1.145),(.5,.5),'release remaining hem'),
        (3.,(.480,1.220),(1.,1.),'withdraw and observe free drape'),
    ]
    for seconds,(x,z),grippers,label in schedule:
        poses={s:ik.tcp_pose(q[s],station.BASES[s]) for s in q};start_open=opening.copy()
        errors={s:[0.,0.] for s in q}
        for k in range(1,round(seconds*20)+1):
            t=ik.smoothstep(k/(seconds*20))
            for i,(side,sign) in enumerate((('left',1),('right',-1))):
                p0,r0=poses[side];target=p0+t*(np.array((x,sign*.115,z))-p0)
                rotation=ik.slerp_matrix(r0,front_rotation(0.,side),t)
                q[side],pe,re=ik.solve(target,ik.matrix_to_quat_xyzw(rotation),q[side],base_pos=station.BASES[side],iters=60)
                errors[side][0]=max(errors[side][0],float(pe));errors[side][1]=max(errors[side][1],float(re))
                opening[side]=start_open[side]+t*(grippers[i]-start_open[side])
            frames.append(dict(action14=np.r_[q['left'],opening['left'],q['right'],opening['right']].tolist(),stage=label))
        audits.extend(dict(side=s,stage=label,seconds=seconds,max_position_error_m=e[0],max_rotation_error_rad=e[1]) for s,e in errors.items())
    actions=np.array([np.r_[READY,1.,READY,1.]]+[f['action14'] for f in frames])
    limit=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
    if np.any(abs(np.diff(actions,axis=0))>limit*1.001):raise ValueError('Normal joint speed exceeded')
    if max(a['max_position_error_m'] for a in audits)>.004 or max(a['max_rotation_error_rad'] for a in audits)>.04:
        raise ValueError('Drape candidate fails ordinary IK gate')
    return dict(schema='cloth-fixed-motion-v1',kind='diagnostic_not_submission_demo',control_hz=20,score=None,
        fixture_board_thickness_m=SUPPORT_BOARD_THICKNESS,physics_hz=PHYSICS_HZ,
        feedback='none; frozen ordinary joint commands only',action_count=len(frames),frames=frames,
        kinematic_audit=prior['kinematic_audit'][:5]+prior['kinematic_audit'][10:15]+audits,
        source_waypoints='First200 actions match batch016 native pickup; higher clearance and line transfer are untested physical candidates.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();plan=compile_drape();args.out.write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(dict(actions=plan['action_count'],seconds=plan['action_count']/20,
        max_position_error_m=max(a['max_position_error_m'] for a in plan['kinematic_audit']),
        max_rotation_error_rad=max(a['max_rotation_error_rad'] for a in plan['kinematic_audit'])),indent=2))
