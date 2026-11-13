"""CPU candidate for the simple/Oriental knot's single under/over wrap.

The technique is documented by tie makers:
https://www.ties.com/how-to-tie-a-tie/simple
https://www.otaa.com/en-us/pages/how-to-tie-a-simple-knot
It needs an explicitly reversed initial face before native validation. This
file does not relabel prior four-in-hand evidence as a successful simple knot.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np


def compile_simple_wrap():
    tail_z=.873;tail_y=.117;wide_rear=.400;wide_z=1.120;tail_yaw=0.
    from free_wrap_motion import compile_free_wrap
    from cross_motion import yaw_rotation
    from yam_arena import ik,station
    from yam_arena.constants import READY,SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    frames=compile_free_wrap()['frames'][:600];a=np.asarray(frames[-1]['action14'])
    q={s:a[7*i:7*i+6].copy() for i,s in enumerate(('left','right'))};opening={'left':0.,'right':1.};audits=[]
    schedule=[
        (3.,'park wide tip high and clear of other arm',{'left':((.240,-.180,1.200),0.,180.)}),
        (3.,'approach narrow tail from side',{'right':((.365,.025,tail_z),.6,tail_yaw)}),
        (2.,'move ahead of narrow tail below shoulders',{'right':((.410,.025,tail_z),.6,tail_yaw)}),
        (2.,'place fingers around hanging narrow tail',{'right':((.410,tail_y,tail_z),.6,tail_yaw)}),
        (1.,'stabilize narrow tail without pulling',{'right':((.410,tail_y,tail_z),0.,tail_yaw)}),
        (2.,'bring held narrow tail clear of shoulder front',{'right':((.350,.117,.840),0.,tail_yaw)}),
        (3.,'approach behind narrow tail from initial side',{'left':((wide_rear,-.14,wide_z),0.,90.)}),
        (4.,'pass wide end under narrow tail',{'left':((wide_rear,.21,wide_z),0.,90.)}),
        (3.,'bring wide end around to front',{'left':((.27,.21,wide_z),0.,160.)}),
        (4.,'lay wide end across simple front band',{'left':((.27,0.,wide_z),0.,90.)}),
        (3.,'hold candidate wrap',{}),
    ]
    for seconds,label,targets in schedule:
        poses={s:ik.tcp_pose(q[s],station.BASES[s]) for s in q};start_open=opening.copy();errors={s:[0.,0.] for s in targets}
        start_q={s:v.copy() for s,v in q.items()};joint_goals={}
        if label=='approach narrow tail from side':
            goal,pe,re=ik.solve(targets['right'][0],ik.matrix_to_quat_xyzw(yaw_rotation(targets['right'][2])),READY,base_pos=station.BASES['right'],iters=400)
            if pe>.004 or re>.04:raise ValueError('Unreachable low side approach')
            joint_goals['right']=goal
        for k in range(1,round(seconds*20)+1):
            t=ik.smoothstep(k/(seconds*20))
            for side,(position,grip,yaw) in targets.items():
                p0,r0=poses[side];target=p0+t*(np.asarray(position)-p0);rotation=ik.slerp_matrix(r0,yaw_rotation(yaw),t)
                if side in joint_goals:
                    q[side]=start_q[side]+t*(joint_goals[side]-start_q[side]);pe=re=0.
                else:q[side],pe,re=ik.solve(target,ik.matrix_to_quat_xyzw(rotation),q[side],base_pos=station.BASES[side],iters=100)
                errors[side][0]=max(errors[side][0],float(pe));errors[side][1]=max(errors[side][1],float(re));opening[side]=start_open[side]+t*(grip-start_open[side])
            frames.append(dict(action14=np.r_[q['left'],opening['left'],q['right'],opening['right']].tolist(),stage=label))
        audits.extend(dict(side=s,stage=label,seconds=seconds,target_xyz_m=list(targets[s][0]),max_position_error_m=e[0],max_rotation_error_rad=e[1]) for s,e in errors.items())
    actions=np.asarray([np.r_[READY,1.,READY,1.]]+[f['action14'] for f in frames]);limit=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
    if np.any(abs(np.diff(actions,axis=0))>limit*1.001):raise ValueError('Normal joint speed exceeded')
    bad=[a for a in audits if a['max_position_error_m']>.004 or a['max_rotation_error_rad']>.04]
    if bad:raise ValueError('Wrap IK gate failed: '+json.dumps(bad))
    return dict(schema='cloth-fixed-motion-v1',kind='diagnostic_not_submission_demo',control_hz=20,score=None,
        fixture_source_sha256=hashlib.sha256(Path(__file__).with_name('layout.py').read_bytes()).hexdigest(),
        feedback='none; frozen ordinary joint commands only',action_count=len(frames),frames=frames,kinematic_audit=audits,
        waypoint_evidence='First600 actions preserve handoff and unused-hand withdrawal; one under/over pass for a simple (Oriental) knot. This needs an explicitly inside-out initial face before any native trial.',
        requires_inside_out_reset=True,
        do_not_run_reason='Awaiting hull rejection audit and explicitly inside-out initial face; not released for native execution.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    plan=compile_simple_wrap();args.out.write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(dict(actions=plan['action_count'],max_position_error_m=max(a['max_position_error_m'] for a in plan['kinematic_audit'])),indent=2))
