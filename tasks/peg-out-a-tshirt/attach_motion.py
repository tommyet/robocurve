"""Unreleased continuation: one hand supports the garment while the other pegs it.

Held transform comes from native batch022; line capture still needs a trial.
The scene uses only passive jaws, ordinary contacts and frozen robot commands.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def compile_attachment():
    from drape_motion import compile_drape
    from fixed_motion import front_rotation
    from yam_arena import ik,station
    from yam_arena.constants import READY,SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    from scene import PHYSICS_HZ,SUPPORT_BOARD_THICKNESS
    prior=compile_drape();frames=prior['frames'][:480]
    action=np.asarray(frames[-1]['action14']);q={s:action[7*i:7*i+6].copy() for i,s in enumerate(('left','right'))}
    opening={s:float(action[7*i+6]) for i,s in enumerate(('left','right'))};audits=[]
    schedule=[
        (2.,'clear the free hand above the line',{'right':((.450,-.115,1.220),1.,0.)}),
        (3.,'approach peg rest from outside garment',{'right':((.200,-.300,1.020),.5,-15.)}),
        (2.,'lower ahead of peg handles',{'right':((.240,-.300,.894),.5,-15.)}),
        (2.,'insert open fingers around peg handles',{'right':((.292,-.300,.880),.5,-15.)}),
        (1.,'squeeze the passive peg handles',{'right':((.292,-.300,.880),0.,-15.)}),
        (3.,'lift the open peg clear of its rest',{'right':((.280,-.300,1.150),0.,-15.)}),
        (2.,'settle held open peg',{}),
        (3.,'present open jaws ahead of the line',{'right':((.410,-.093,1.089),0.,0.)}),
        (2.,'insert line and cloth between the jaws',{'right':((.4625,-.093,1.089),0.,0.)}),
        (2.,'release peg handles to close on line and cloth',{'right':((.4625,-.093,1.089),.35,0.)}),
        (2.,'withdraw from the passive peg',{'right':((.390,-.093,1.089),.6,0.)}),
        (2.,'release remaining garment grasp',{'left':((.560,.115,1.145),.5,0.)}),
        (3.,'withdraw empty garment hand',{'left':((.480,.115,1.220),1.,0.)}),
        (5.,'observe released garment and passive peg',{}),
    ]
    for seconds,label,targets in schedule:
        poses={s:ik.tcp_pose(q[s],station.BASES[s]) for s in q};start_open=opening.copy();errors={s:[0.,0.] for s in targets}
        for k in range(1,round(seconds*20)+1):
            t=ik.smoothstep(k/(seconds*20))
            for side,(position,target_opening,pitch) in targets.items():
                p0,r0=poses[side];target=p0+t*(np.asarray(position)-p0);rotation=ik.slerp_matrix(r0,front_rotation(pitch,side),t)
                q[side],pe,re=ik.solve(target,ik.matrix_to_quat_xyzw(rotation),q[side],base_pos=station.BASES[side],iters=60)
                errors[side][0]=max(errors[side][0],float(pe));errors[side][1]=max(errors[side][1],float(re))
                opening[side]=start_open[side]+t*(target_opening-start_open[side])
            frames.append(dict(action14=np.r_[q['left'],opening['left'],q['right'],opening['right']].tolist(),stage=label))
        audits.extend(dict(side=s,stage=label,seconds=seconds,target_xyz_m=list(targets[s][0]),max_position_error_m=e[0],max_rotation_error_rad=e[1]) for s,e in errors.items())
    actions=np.array([np.r_[READY,1.,READY,1.]]+[f['action14'] for f in frames])
    limit=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
    if np.any(abs(np.diff(actions,axis=0))>limit*1.001):raise ValueError('Normal joint speed exceeded')
    bad=[a for a in audits if a['max_position_error_m']>.004 or a['max_rotation_error_rad']>.04]
    if bad:raise ValueError('Attachment IK gate failed: '+json.dumps(bad))
    return dict(schema='cloth-fixed-motion-v1',kind='diagnostic_not_submission_demo',control_hz=20,score=None,
        fixture_board_thickness_m=SUPPORT_BOARD_THICKNESS,physics_hz=PHYSICS_HZ,peg_rests_required=True,
        peg_rest_source_sha256=hashlib.sha256(Path(__file__).with_name('peg_rests.py').read_bytes()).hexdigest(),
        feedback='none; frozen ordinary joint commands only',action_count=len(frames),frames=frames,kinematic_audit=audits,
        source_waypoints='First480 actions preserve batch020 cloth transfer. Line insertion uses offline batch022 retained-peg transform after2s hold. No online object feedback.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();plan=compile_attachment();args.out.write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(dict(actions=plan['action_count'],seconds=plan['action_count']/20,
        max_position_error_m=max(a['max_position_error_m'] for a in plan['kinematic_audit']),
        max_rotation_error_rad=max(a['max_rotation_error_rad'] for a in plan['kinematic_audit'])),indent=2))
