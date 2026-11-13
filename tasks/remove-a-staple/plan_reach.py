"""Offline reach checks for the proposed lever-removal sequence.

Uses only the published fixed geometry and robot kinematics. These targets are
not a collision-tested trajectory, a manipulation policy or task evidence.
The remover approaches from the supported right side of the staple; a left
approach would place its heel beyond the document support.
"""
import argparse
import json
import math
from pathlib import Path
import numpy as np
from full_scene import SUPPORT_TOP,TABLE_TOP,STAPLE_XY


def tool_frame(pitch):
    c,s=math.cos(pitch),math.sin(pitch)
    z=np.array(((0.,-1.,0.),(1.,0.,0.),(0.,0.,1.)))
    return z@np.array(((1.,0.,0.),(0.,c,-s),(0.,s,c)))


def heel_supported_pose(pitch):
    # The heel bottom, local(y=-4mm,z=-3mm), contacts the document support.
    return np.array((STAPLE_XY[0]+.025,STAPLE_XY[1],
                     SUPPORT_TOP+.004*math.sin(pitch)+.003*math.cos(pitch)))


def targets():
    down=np.array(((0.,-1.,0.),(-1.,0.,0.),(0.,0.,-1.)))
    grip=np.array((0.,-.043,.013))
    initial=np.array((.28,-.20,TABLE_TOP+.003))
    yield 'pickup_above',initial+grip+(0.,0.,.08),down
    yield 'pickup',initial+grip,down
    yield 'pickup_lift',initial+grip+(0.,0.,.06),down
    pitch=-.07;R=tool_frame(pitch);root=heel_supported_pose(pitch)
    yield 'orient_clear',root+R@grip+(0.,0.,.06),R@down
    yield 'approach_crown',root+R@grip+(.012,0.,.006),R@down
    yield 'insert_candidate',root+R@grip,R@down
    # Stop at level: lowering the handle beyond level would collide with the
    # flat support. Continued extraction lifts the whole ordinary held tool.
    R=tool_frame(0.);root=heel_supported_pose(0.)
    yield 'lever_level',root+R@grip,R@down
    yield 'extract_lift',root+R@grip+(0.,0.,.012),R@down
    yield 'carry_clear',root+R@grip+(0.,0.,.07),R@down


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    from yam_arena import ik,station
    from yam_arena.constants import READY
    report={'kind':'offline_reach_candidates','native_runtime':False,'collision_validated':False,'task_score':None,
            'notes':['Proposed insertion must be verified against paper and crown contact.','No object-state feedback or object motion is used.'],
            'targets':[]}
    for name,position,R in targets():
        q,pe,re=ik.solve(position,ik.matrix_to_quat_xyzw(R),np.asarray(READY),station.BASES['right'],
                         iters=500,tol=1e-7,damping=.015)
        report['targets'].append({'name':name,'tcp_position_m':position.tolist(),'tcp_rotation':R.tolist(),
            'right_arm_joints_rad':q.tolist(),'position_error_m':pe,'orientation_error_rad':re,
            'kinematically_reachable':bool(pe<.0001 and re<.001)})
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'targets':len(report['targets']),'reachable':sum(x['kinematically_reachable'] for x in report['targets']),
        'collision_validated':False,'task_score':None}))


if __name__=='__main__':main()
