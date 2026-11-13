"""Candidate physical wide-tip handoff before a rear passage.

Preserve native039 through the outside pose at940, release the narrow tail,
receive the last15mm of the wide end, then let the first wrapping arm withdraw.
This avoids sending that entire arm around the narrow strand. No knot is
claimed and no cloth state drives the normal joint commands.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np


def compile_wrap_handoff():
    from cross_motion import yaw_rotation
    from yam_arena import ik,station
    from yam_arena.constants import READY,SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    frames=json.loads(Path(__file__).with_name('deeper-bite-wrap-plan.json').read_text())['frames'][:940];a=np.asarray(frames[-1]['action14']);q={s:a[7*i:7*i+6].copy() for i,s in enumerate(('left','right'))};opening={'left':0.,'right':0.};audits=[]
    schedule=[
        (1.,'release narrow tail for physical tip handoff',{'right':((.350,.117,.883),.6,-15.)}),
        (2.,'withdraw open right hand from narrow strand',{'right':((.30,.025,.883),.6,-15.)}),
        (3.,'present wide tip with palms on opposite sides',{'left':((.320,.200,1.080),0.,160.)}),
        (3.,'align receiving right hand below wide grasp',{'right':((.338,.150,1.015),.6,-20.)}),
        (3.,'insert receiving fingers around wide tip',{'right':((.309,.230,1.015),.6,-20.)}),
        (1.,'pinch wide tip with receiving hand',{'right':((.309,.230,1.015),0.,-20.)}),
        (2.,'release first wide grasp',{'left':((.320,.200,1.080),.6,160.)}),
        (3.,'withdraw first wrapping arm from strand route',{'left':((.240,.280,1.180),.6,160.)}),
        (3.,'lift transferred wide tip in clear front space',{'right':((.300,.050,1.060),0.,-20.)}),
        (2.,'observe retained second handoff',{}),
    ]
    for seconds,label,targets in schedule:
        poses={s:ik.tcp_pose(q[s],station.BASES[s]) for s in q};start_open=opening.copy();start_q={s:v.copy() for s,v in q.items()};errors={s:[0.,0.] for s in targets}
        for k in range(1,round(seconds*20)+1):
            t=ik.smoothstep(k/(seconds*20))
            for side,(position,grip,yaw) in targets.items():
                p0,r0=poses[side];target=p0+t*(np.asarray(position)-p0);rotation=ik.slerp_matrix(r0,yaw_rotation(yaw),t)
                if label=='withdraw first wrapping arm from strand route':q[side]=start_q[side]+t*(np.asarray(READY)-start_q[side]);pe=re=0.
                else:q[side],pe,re=ik.solve(target,ik.matrix_to_quat_xyzw(rotation),q[side],base_pos=station.BASES[side],iters=100)
                errors[side][0]=max(errors[side][0],float(pe));errors[side][1]=max(errors[side][1],float(re));opening[side]=start_open[side]+t*(grip-start_open[side])
            frames.append(dict(action14=np.r_[q['left'],opening['left'],q['right'],opening['right']].tolist(),stage=label))
        audits.extend(dict(side=s,stage=label,seconds=seconds,target_xyz_m=list(targets[s][0]),max_position_error_m=e[0],max_rotation_error_rad=e[1]) for s,e in errors.items())
    actions=np.asarray([np.r_[READY,1.,READY,1.]]+[f['action14'] for f in frames]);limit=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
    if np.any(abs(np.diff(actions,axis=0))>limit*1.001):raise ValueError('Normal joint speed exceeded')
    bad=[a for a in audits if a['max_position_error_m']>.004 or a['max_rotation_error_rad']>.04]
    if bad:raise ValueError('Wide-tip handoff IK gate failed: '+json.dumps(bad))
    return dict(schema='cloth-fixed-motion-v1',kind='diagnostic_not_submission_demo',control_hz=20,score=None,
        fixture_source_sha256=hashlib.sha256(Path(__file__).with_name('layout.py').read_bytes()).hexdigest(),feedback='none; frozen ordinary joint commands only',action_count=len(frames),frames=frames,kinematic_audit=audits,
        waypoint_evidence='First940 actions match native039. Native039 supplies the70–80mm free leader geometry. Presenting at a160degree yaw lets the receiving hand approach from the opposite side at minus20degrees; the predicted s0.015 patch is near(0.312,0.221,1.015)m. Grasp remains a native-test candidate, not a rigid cloth assumption during simulation. No fixture/material change.',
        do_not_run_reason='Awaiting complete commanded hull and held-strand route rejection checks. No second handoff or knot yet demonstrated.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);args=p.parse_args();plan=compile_wrap_handoff();args.out.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(dict(actions=plan['action_count'],max_position_error_m=max(a['max_position_error_m'] for a in plan['kinematic_audit'])),indent=2))
