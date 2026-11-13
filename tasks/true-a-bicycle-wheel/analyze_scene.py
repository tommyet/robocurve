"""Assess a bounded settling diagnostic; never certify robot task success."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from integrity import rim_strain
from thread_coupling import rotation_batch


def analyze(report):
    samples=report.get('samples',[])
    if len(samples)<3 or not report.get('complete'):
        return {'physical_gate_pass':False,'reason':'Incomplete native evidence'}
    indices=[report['native_body_paths'].index(f'/WheelTask/wheel/rim_{i:02d}') for i in range(32)]
    strain=[]
    for sample in samples:
        poses=np.asarray(sample['native_body_poses'])[indices]
        strain.append(rim_strain(poses[:,:3],rotation_batch(poses[:,3:])))
    peak={key:max(s[key] for s in strain) for key in strain[0]}
    late=[s for s in samples if s['time_s']>=samples[-1]['time_s']-.020-1e-10 and s['thread_state']]
    span=late[-1]['time_s']-late[0]['time_s']
    if span<.019:return {'physical_gate_pass':False,'reason':'Less than20ms of final measured history'}
    points=np.asarray([s['rim_positions_in_hub_m'] for s in late])
    turns=np.asarray([[t['turns'] for t in s['thread_state']] for s in late])
    time=np.asarray([s['time_s'] for s in late]);time-=time.mean()
    rate=np.sum(time[:,None]*(turns-turns.mean(0)),axis=0)/np.sum(time*time)
    tensions=np.asarray([[s['tension_n'] for s in t['thread_state']] for t in late])
    result={'complete_native_execution':bool(report.get('complete')),
        'frozen_material_diagnostic':bool(report.get('frozen_material_diagnostic')),
        'seconds':report['seconds'],'dt':report['dt'],'wall_seconds':report['wall_seconds'],
        'maximum_runout_m':max(s['lateral_runout_m'] for s in samples),
        'final_runout_m':samples[-1]['lateral_runout_m'],
        'late_maximum_rim_displacement_m':float(np.linalg.norm(points-points[-1],axis=2).max()),
        'late_maximum_thread_rate_turns_s':float(np.abs(rate).max()),
        'late_tension_range_n':[float(tensions.min()),float(tensions.max())],
        'peak_rim_domain':peak,'robot_demo':False,'task_score':None,
        'interpretation':'Short settling gate only. Does not test wrench interaction, full-duration stability or robot feasibility.'}
    result['geometry_gate_pass']=bool(result['maximum_runout_m']<.010 and
        result['late_maximum_rim_displacement_m']<.00005 and tensions.max()<1500. and
        peak['maximum_axial_bending_strain']<=.003 and peak['maximum_twist_rad']<=.01 and
        peak['maximum_locked_joint_gap_m']<=.0001)
    result['thread_holding_gate_pass']=bool(result['late_maximum_thread_rate_turns_s']<.0001)
    result['physical_gate_pass']=bool(result['geometry_gate_pass'] and result['thread_holding_gate_pass'] and
                                      not result['frozen_material_diagnostic'])
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path);parser.add_argument('--out',type=Path)
    args=parser.parse_args();source=args.report.read_bytes()
    result=analyze(json.loads(source));result['native_report_sha256']=hashlib.sha256(source).hexdigest()
    encoded=json.dumps(result,indent=2,allow_nan=False)+'\n'
    if args.out:args.out.write_text(encoded)
    print(encoded)


if __name__=='__main__':main()
