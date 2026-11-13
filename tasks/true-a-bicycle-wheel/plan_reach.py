"""Offline YAM reach diagnostic for a known fixed setup; no simulator or API.

These joint solutions are not a collision-free motion plan or successful demo.
Run with the pinned yam_arena importable. Only robot kinematics and published
initial geometry are used; no live object or scorer state is consumed.
"""
import argparse
import json
import math
from pathlib import Path
import numpy as np
from mechanics import WheelSpec
from wheel_scene import x_frame


def candidate_tool_frames(spoke):
    s=WheelSpec();theta=spoke*2*math.pi/s.spokes;side=1 if spoke%2==0 else -1
    anchor=np.array((s.hub_flange_radius_m*math.cos(theta+side*s.cross_angle_rad),
                     s.hub_flange_radius_m*math.sin(theta+side*s.cross_angle_rad),side*s.hub_half_width_m))
    end=np.array((s.rim_radius_m*math.cos(theta),s.rim_radius_m*math.sin(theta),0.))
    R=np.array(((0.,0.,1.),(0.,1.,0.),(-1.,0.,0.)))
    frame=R@x_frame(end-anchor)
    center=np.array((.35,0.,1.005))+R@(end-x_frame(end-anchor)[:,0]*.006)
    base=frame[:,[2,1,0]]@np.diag((1.,1.,-1.))
    # Four equivalent square-nipple engagements; they are separate proposed
    # approach orientations, not arbitrary hidden changes to a held wrench.
    for quarter in range(4):
        a=quarter*math.pi/2;c,ss=math.cos(a),math.sin(a)
        yield center,base@np.array(((c,-ss,0.),(ss,c,0.),(0.,0.,1.)))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    from yam_arena import ik,station
    from yam_arena.constants import READY
    down=np.array(((0.,-1.,0.),(-1.,0.,0.),(0.,0.,-1.)))
    tool_to_tcp=np.array((0.,-.045,.011))
    report={'kind':'kinematic_reach_only','collision_validated':False,'task_score':None,'targets':[]}
    targets=[('pickup',np.array((.20,-.20,.7665)),down)]
    for spoke in (0,2,4,6):
        for j,(center,R) in enumerate(candidate_tool_frames(spoke)):
            targets.append((f'spoke_{spoke}_engagement_{j}',center+R@tool_to_tcp,R@down))
    for name,position,rotation in targets:
        q,pe,re=ik.solve(position,ik.matrix_to_quat_xyzw(rotation),np.asarray(READY),station.BASES['right'],
                         iters=500,tol=1e-7,damping=.015)
        report['targets'].append({'name':name,'tcp_position_m':position.tolist(),'tcp_rotation':rotation.tolist(),
             'right_arm_joints_rad':q.tolist(),'position_error_m':pe,'orientation_error_rad':re,
             'kinematically_reachable':bool(pe<.0001 and re<.001)})
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'targets':len(targets),'reachable':sum(x['kinematically_reachable'] for x in report['targets']),
                      'artifact':str(a.out),'collision_validated':False}))


if __name__=='__main__':main()
