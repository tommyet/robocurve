"""Prepare an explicitly approximate short contact replay from measured poses.

This is never an episode reset or demo. Native velocities are preferred when
recorded; older traces use disclosed unsmoothed adjacent-pose differences.
The original cloth rest geometry, dimensions, materials and cut law stay fixed.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation


def pose_velocity(previous,current,dt):
    previous,current=np.asarray(previous,float),np.asarray(current,float)
    if previous.shape!=current.shape or previous.shape[-1]!=7 or not dt>0:
        raise ValueError('Matched timed native poses required')
    angular=(Rotation.from_quat(current[...,3:])*Rotation.from_quat(previous[...,3:]).inv()).as_rotvec()/dt
    return np.concatenate(((current[...,:3]-previous[...,:3])/dt,angular),axis=-1)


def prepare(source,out,action=265):
    from yam_arena import ik,station
    from plan import DOWN
    from plan_cut import GRASP_OFFSET
    source,out=Path(source),Path(out)
    report=json.loads((source/'preview.json').read_text())
    rows=[json.loads(line) for line in gzip.open(source/'trace.jsonl.gz','rt')]
    before=next(row for row in rows if row['step']==action-1)
    current=next(row for row in rows if row['step']==action)
    if current['invalid'] or current['cut_events']:
        raise ValueError('Replay requires a valid state with all thread joints still intact')
    dt=current['time_s']-before['time_s']
    plan=json.loads((source/'task-source/fixed-plan.json').read_text())
    with np.load(source/'last-measured-state.npz') as archive:
        data={key:archive[key] for key in ('left_rest','right_rest','left_faces','right_faces','thread_lengths')}
    velocity_sources={}
    for side in range(2):
        old=np.array(before['facet_poses_xyzw'][side]);now=np.array(current['facet_poses_xyzw'][side])
        data[f'facet_poses{side}']=now
        direct=current.get('facet_velocity_m_s_rad_s')
        data[f'facet_velocity{side}']=np.asarray(direct[side]) if direct is not None else pose_velocity(old,now,dt)
        velocity_sources[f'patch{side}']='native endpoint readback' if direct is not None else 'unsmoothed adjacent-pose difference'
    for name,key in (('thread','thread_poses_xyzw'),('handle','handle_pose_xyzw'),('blade','blade_pose_xyzw')):
        old=np.asarray(before[key]);now=np.asarray(current[key])
        direct=current.get(name+'_velocity_m_s_rad_s')
        data[name]=now;data[name+'_velocity']=np.asarray(direct) if direct is not None else pose_velocity(old,now,dt)
        velocity_sources[name]='native endpoint readback' if direct is not None else 'unsmoothed adjacent-pose difference'
    jaw_current='moving_jaw_pose_xyzw' in current
    data['jaw']=np.asarray(current['moving_jaw_pose_xyzw'] if jaw_current else report['final_moving_jaw_pose'])
    data['jaw_velocity']=np.asarray(current['moving_jaw_velocity_m_s_rad_s'] if jaw_current else report['final_moving_jaw_velocity'])
    jaw_time=current['time_s'] if jaw_current else report['audited_physics_substeps']/report['runtime']['physics_hz']
    nominal=[]
    for frame in plan['frames'][action-1:]:
        tcp,hand_r=ik.tcp_pose(np.asarray(frame['action14'][7:13]),station.BASES['right'])
        tool_r=hand_r@DOWN.T
        nominal.append(np.r_[tcp-tool_r@GRASP_OFFSET,Rotation.from_matrix(tool_r).as_quat()])
    nominal=np.asarray(nominal)
    initial_r=Rotation.from_quat(data['handle'][3:])
    alignment=initial_r*Rotation.from_quat(nominal[0,3:]).inv()
    target_p=alignment.apply(nominal[:,:3]-nominal[0,:3])+data['handle'][:3]
    target_r=alignment*Rotation.from_quat(nominal[:,3:])
    data['tool_targets']=np.column_stack((target_p,target_r.as_quat()))
    data['tool_target_times']=np.arange(len(nominal))/20
    data['source_action']=np.asarray(action);data['source_time_s']=np.asarray(current['time_s'])
    if (not np.allclose(data['tool_targets'][0,:3],data['handle'][:3],rtol=0,atol=1e-12) or
            (Rotation.from_quat(data['tool_targets'][0,3:])*initial_r.inv()).magnitude()>1e-12):
        raise RuntimeError('Prescribed tool path does not begin at the measured pose')
    out.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(out,**data)
    metadata=dict(status='unscored approximate contact initialization; never a demo/reset',
        source_action=action,source_time_s=current['time_s'],velocity_interval_s=dt,
        velocity_sources=velocity_sources,
        velocities='Use native endpoint readback where recorded; otherwise use unsmoothed20Hz pose differences. Solver warm-start history is unavailable in either case.',
        moving_jaw='Same selected action readback' if jaw_current else 'Only available final native readback, recorded after the selected action; time mismatch is disclosed.',
        moving_jaw_time_offset_s=jaw_time-current['time_s'],
        tool_motion='Original fixed path, rigidly aligned to measured handle pose; native kinematic target, dynamic mounted blade. Robot removed only in diagnostic.',
        source_sha256={name:hashlib.sha256((source/name).read_bytes()).hexdigest() for name in ('preview.json','trace.jsonl.gz','initial.usda')},
        data_sha256=hashlib.sha256(out.read_bytes()).hexdigest())
    out.with_suffix('.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return metadata


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--action',type=int,default=265);a=p.parse_args()
    print(json.dumps(prepare(a.source,a.out,a.action),indent=2))
