"""Candidate: open a spare line peg, feed the held shirt and ease it closed.

This uses ordinary joint commands. No peg is fixed to the line or robot, and
no material state is read by the policy. Native contact and released retention
remain unproven until a recorded trial is independently inspected.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np


def side_rotation(degrees):
    a=np.deg2rad(degrees)
    return np.array([[np.cos(a),0.,np.sin(a)],[-np.sin(a),0.,np.cos(a)],[0.,-1.,0.]])


def compile_feed():
    from fixed_motion import compile_grasp,front_rotation
    from yam_arena import ik,station
    from yam_arena.constants import READY,SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    from scene import PHYSICS_HZ,SUPPORT_BOARD_THICKNESS
    frames=compile_grasp()['frames'][:200];a=np.asarray(frames[-1]['action14'])
    q={s:a[7*i:7*i+6].copy() for i,s in enumerate(('left','right'))};opening={'left':0.,'right':0.};audits=[]
    def both(x,z):return {s:((x,sign*.115,z),0.,'front') for s,sign in [('left',1),('right',-1)]}
    schedule=[
        (3.,'lift flexible shirt',both(.26,1.20)),
        (3.,'carry shirt in front of line',both(.47,1.20)),
        (2.,'release right hem',{'right':((.47,-.115,1.20),.6,'front')}),
        (2.,'clear empty right hand',{'right':((.34,-.115,1.20),.6,'front')}),
        (2.,'present held left hem above peg',{'left':((.49,.115,1.15),0.,'front')}),
        (2.,'lower empty hand clear of line',{'right':((.35,-.115,1.038),.6,'side')}),
        (3.,'approach peg handles from the side',{'right':((.52,.025,1.038),.6,'side')}),
        (2.,'place fingers around passive handles',{'right':((.52,.115,1.038),.6,'side')}),
        (2.,'squeeze handles to open jaw',{'right':((.52,.115,1.038),0.,'side')}),
        (2.,'hold peg open',{}),
        (3.,'feed flexible hem into open jaw',{'left':((.513,.115,1.125),0.,'front')}),
        (4.,'ease handles open to close peg slowly',{'right':((.52,.115,1.038),.6,'side')}),
        (2.,'withdraw empty peg hand',{'right':((.52,.025,1.038),.6,'side')}),
        (2.,'release fabric',{'left':((.513,.115,1.125),.6,'front')}),
        (3.,'withdraw empty fabric hand',{'left':((.45,.115,1.20),.6,'front')}),
        (5.,'observe released garment',{}),
    ]
    for seconds,label,targets in schedule:
        poses={s:ik.tcp_pose(q[s],station.BASES[s]) for s in q};start_open=opening.copy();errors={s:[0.,0.] for s in targets}
        for k in range(1,round(seconds*20)+1):
            t=ik.smoothstep(k/(seconds*20))
            for side,(position,grip,orientation) in targets.items():
                p0,r0=poses[side];target=p0+t*(np.asarray(position)-p0)
                goal=front_rotation(0.,side) if orientation=='front' else side_rotation(0. if side=='right' else 180.)
                rotation=ik.slerp_matrix(r0,goal,t)
                q[side],pe,re=ik.solve(target,ik.matrix_to_quat_xyzw(rotation),q[side],base_pos=station.BASES[side],iters=100)
                errors[side][0]=max(errors[side][0],float(pe));errors[side][1]=max(errors[side][1],float(re));opening[side]=start_open[side]+t*(grip-start_open[side])
            frames.append(dict(action14=np.r_[q['left'],opening['left'],q['right'],opening['right']].tolist(),stage=label))
        audits.extend(dict(side=s,stage=label,seconds=seconds,target_xyz_m=list(targets[s][0]),max_position_error_m=e[0],max_rotation_error_rad=e[1]) for s,e in errors.items())
    actions=np.asarray([np.r_[READY,1.,READY,1.]]+[f['action14'] for f in frames]);limit=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
    if np.any(abs(np.diff(actions,axis=0))>limit*1.001):raise ValueError('Normal joint speed exceeded')
    bad=[a for a in audits if a['max_position_error_m']>.004 or a['max_rotation_error_rad']>.04]
    if bad:raise ValueError('Feed IK gate failed: '+json.dumps(bad))
    return dict(schema='cloth-fixed-motion-v1',kind='diagnostic_not_submission_demo',control_hz=20,score=None,
        fixture_board_thickness_m=SUPPORT_BOARD_THICKNESS,physics_hz=PHYSICS_HZ,line_pegs_required=True,
        line_peg_source_sha256=hashlib.sha256(Path(__file__).with_name('line_pegs.py').read_bytes()).hexdigest(),
        feedback='none; frozen ordinary joint commands only',action_count=len(frames),frames=frames,kinematic_audit=audits,
        source_waypoints='First200 native cloth pickup actions; spare peg handle position measured offline from native029. No online object feedback.',
        do_not_run_reason='Awaiting full commanded collision-hull rejection audit.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    plan=compile_feed();args.out.write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(dict(actions=plan['action_count'],max_position_error_m=max(a['max_position_error_m'] for a in plan['kinematic_audit'])),indent=2))
