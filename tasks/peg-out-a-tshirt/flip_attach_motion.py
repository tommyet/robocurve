"""Candidate: remove a held spare peg, turn jaws downward, and clip from above/front.

The ordinary opening prefix is preserved from native037. The peg is withdrawn
downward from the line before translation/rotation; no attachment, kinematic
jaw or material feedback is used. The subsequent fabric carry is a candidate.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np


def compile_flip_attach(grasp_x=.220,clip_target=(.484,.115,1.114)):
    from feed_clear_motion import compile_feed,tilted_side_rotation
    from fixed_motion import front_rotation
    from yam_arena import ik,station
    from yam_arena.constants import READY,SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    from scene import PHYSICS_HZ,SUPPORT_BOARD_THICKNESS
    frames=compile_feed(grasp_x=grasp_x)['frames'][:540];a=np.asarray(frames[-1]['action14'])
    q={s:a[7*i:7*i+6].copy() for i,s in enumerate(('left','right'))};opening={'left':0.,'right':0.};audits=[]
    side=tilted_side_rotation(0.);angle=np.deg2rad(120.)
    turn=np.array([[np.cos(angle),0.,np.sin(angle)],[0.,1.,0.],[-np.sin(angle),0.,np.cos(angle)]])
    down=turn@side
    schedule=[
        (2.,'withdraw open peg downward from line',{'right':((.52,.115,.990),0.,side)}),
        (2.,'clear held peg forward of line',{'right':((.40,.115,.990),0.,side)}),
        (4.,'lift and turn held peg jaws downward',{'right':((.32,-.12,1.16),0.,down)}),
        (3.,'carry hem over line clear of peg hand',{'left':((.58,.18,1.18),0.,front_rotation(0.,'left'))}),
        (3.,'bring open peg above cloth and line',{'right':((.445,.115,1.137),0.,down)}),
        (3.,'lower jaws over cloth and line',{'right':(clip_target,0.,down)}),
        (3.,'ease handles to close clip',{'right':(clip_target,.6,down)}),
        (2.,'raise empty peg hand',{'right':((.445,.115,1.137),.6,down)}),
        (2.,'clear empty right hand',{'right':((.30,-.25,1.16),.6,down)}),
        (2.,'release supported garment',{'left':((.58,.18,1.18),.6,front_rotation(0.,'left'))}),
        (3.,'clear empty left hand',{'left':((.30,.25,1.18),.6,front_rotation(0.,'left'))}),
        (5.,'observe released first clip',{}),
    ]
    for seconds,label,targets in schedule:
        poses={s:ik.tcp_pose(q[s],station.BASES[s]) for s in q};start_open=opening.copy();start_q={s:v.copy() for s,v in q.items()};errors={s:[0.,0.] for s in targets}
        for k in range(1,round(seconds*20)+1):
            t=ik.smoothstep(k/(seconds*20))
            for hand,(position,grip,orientation) in targets.items():
                p0,r0=poses[hand];target=p0+t*(np.asarray(position)-p0);rotation=ik.slerp_matrix(r0,orientation,t)
                if label=='clear empty right hand':q[hand]=start_q[hand]+t*(np.asarray(READY)-start_q[hand]);pe=re=0.
                else:q[hand],pe,re=ik.solve(target,ik.matrix_to_quat_xyzw(rotation),q[hand],base_pos=station.BASES[hand],iters=100)
                errors[hand][0]=max(errors[hand][0],float(pe));errors[hand][1]=max(errors[hand][1],float(re));opening[hand]=start_open[hand]+t*(grip-start_open[hand])
            frames.append(dict(action14=np.r_[q['left'],opening['left'],q['right'],opening['right']].tolist(),stage=label))
        audits.extend(dict(side=s,stage=label,seconds=seconds,target_xyz_m=list(targets[s][0]),max_position_error_m=e[0],max_rotation_error_rad=e[1]) for s,e in errors.items())
    actions=np.asarray([np.r_[READY,1.,READY,1.]]+[f['action14'] for f in frames]);limit=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
    ratios=abs(np.diff(actions,axis=0))/limit
    if np.any(ratios>1.001):
        step,joint=np.unravel_index(np.argmax(ratios),ratios.shape)
        raise ValueError(f'Normal joint speed exceeded at action{step+1} joint{joint}: {ratios[step,joint]:.3f} times limit, {frames[step]["stage"]}')
    bad=[a for a in audits if a['max_position_error_m']>.004 or a['max_rotation_error_rad']>.04]
    if bad:raise ValueError('Peg-turn IK gate failed: '+json.dumps(bad))
    return dict(schema='cloth-fixed-motion-v1',kind='diagnostic_not_submission_demo',control_hz=20,score=None,
        fixture_board_thickness_m=SUPPORT_BOARD_THICKNESS,physics_hz=PHYSICS_HZ,line_pegs_required=True,
        line_peg_source_sha256=hashlib.sha256(Path(__file__).with_name('line_pegs.py').read_bytes()).hexdigest(),
        feedback='none; frozen ordinary joint commands only',action_count=len(frames),frames=frames,kinematic_audit=audits,
        source_waypoints='Native037 opening prefix; native035 open peg transform relative to the hand supplies approximate ordinary tip alignment. Withdraw peg downward from empty line, rotate120degrees in free space, then clip fabric from above/front with jaws30degrees downward. A vertical jaws-down pose exceeds normal YAM reach. No object-state feedback.',
        do_not_run_reason='Awaiting full commanded hull rejection check; peg retention through lift/rotation and clipping are not demonstrated.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);args=p.parse_args();plan=compile_flip_attach()
    args.out.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(dict(actions=plan['action_count'],max_position_error_m=max(a['max_position_error_m'] for a in plan['kinematic_audit'])),indent=2))
