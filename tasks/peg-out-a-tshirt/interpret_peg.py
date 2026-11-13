"""Offline passive-peg measurements from native assessor records, never a policy.

A retained rigid-body transform can support visual grasp review. It does not
prove cloth capture or assign a score, and it never drives a robot action.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from interpret_motion import rotation_xyzw


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('trial',type=Path)
    p.add_argument('--side',choices=('left','right'),default='right')
    p.add_argument('--every',type=int,default=20);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.every<1:p.error('--every must be positive')
    plan=json.loads((args.trial/'task-source/fixed-motion.json').read_text());frames=plan['frames']
    endpoints={i+1 for i,f in enumerate(frames) if i==len(frames)-1 or f['stage']!=frames[i+1]['stage']}
    report=json.loads((args.trial/'run.json').read_text());samples=[];initial=None
    with gzip.open(args.trial/'trace.jsonl.gz','rt') as f:
        for line in f:
            row=json.loads(line);step=row['step']
            if step%args.every and step not in endpoints and step!=report['completed_steps']:continue
            peg=row['objects'][args.side+'_peg'];body=np.asarray(peg['body_poses']);lower,upper=body
            lr=rotation_xyzw(lower[3:]);ur=rotation_xyzw(upper[3:]);relative=lr.T@ur
            robot=row['robot_links'][args.side+'_robot'];grip=np.asarray(robot['poses_xyzw'][robot['names'].index('gripper')]);gr=rotation_xyzw(grip[3:])
            tcp=grip[:3]+gr@np.array((0.,0.,.134))
            lower_inner=lower[:3]+lr@np.array((.030,0.,-.0005));upper_inner=upper[:3]+ur@np.array((.030,0.,.0005))
            if initial is None:initial=lower[:3].copy()
            samples.append(dict(step=step,time_s=row['time_s'],stage='reset' if step==0 else frames[step-1]['stage'],
                lower_root_m=lower[:3].tolist(),upper_root_m=upper[:3].tolist(),lower_displacement_m=(lower[:3]-initial).tolist(),
                hinge_root_separation_m=float(np.linalg.norm(upper[:3]-lower[:3])),
                relative_upper_y_angle_rad=float(np.arctan2(relative[0,2],relative[0,0])),
                inner_jaw_gap_at_30mm_m=float((upper_inner-lower_inner)@lr[:,2]),
                actual_tcp_m=tcp.tolist(),lower_root_relative_to_gripper_m=((lower[:3]-tcp)@gr).tolist(),
                lower_rotation_relative_to_gripper=(gr.T@lr).tolist(),
                nominal_gripper_opening=float(row['action14'][6 if args.side=='left' else 13])))
    out=dict(kind='offline_native_peg_measurements_not_score',run_status=report['status'],completed_steps=report['completed_steps'],
        source_trace_sha256=hashlib.sha256((args.trial/'trace.jsonl.gz').read_bytes()).hexdigest(),
        samples=samples,score=None,retained_grasp=None,
        limitation='Body pose and jaw separation are assessor measurements; actual grasp and line/cloth capture require visual contact and release review.')
    args.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(samples=len(samples),status=report['status'],max_lift_m=max(s['lower_displacement_m'][2] for s in samples)),indent=2))


if __name__=='__main__':main()
