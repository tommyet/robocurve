"""Explicit pose-only restored-start mechanics; never task-success evidence."""
import hashlib,json
from pathlib import Path
import numpy as np
from capture import array


def load_snapshot(path):
    path=Path(path);s=json.loads(path.read_text());rowpath=path.with_name(s['source_row_file'])
    if hashlib.sha256(rowpath.read_bytes()).hexdigest()!=s['source_row_sha256']:raise ValueError('source-row hash mismatch')
    row=json.loads(rowpath.read_text())
    if abs(s['source_time_s']-row['time'])>1e-6 or s['source_trace_sha256']!='f7398d3c3d51f3446d56a71eb85730542826167e2db8f2854986f91b99bced2d' or len(s['poses'])!=12 or len(s['native_owner_poses'])!=31:raise ValueError('wrong011 postcut snapshot')
    if s['source_time_s']!=179. or s.get('unsealed_start') is not True:raise ValueError('requires actual011179s postcut state')
    for field in ('poses','cutter_pose','native_hands','native_owner_poses'):
        if s[field]!=row[field]:raise ValueError('snapshot differs from source row: '+field)
    if s['held_action_14d']!=row['action_14d']:raise ValueError('held command differs from issued source action')
    vectors=[*s['poses'].values(),s['cutter_pose'],*s['native_owner_poses'].values()]
    if any(np.asarray(p).shape!=(7,) or not np.isfinite(p).all() or abs(np.linalg.norm(p[3:])-1)>.002 for p in vectors):raise ValueError('invalid source native pose')
    if np.asarray(s['held_action_14d']).shape!=(14,) or not np.isfinite(s['held_action_14d']).all():raise ValueError('invalid held action')
    for h in s['native_hands']:
        if len(h['joints'])!=6 or len(h['finger_joints'])!=2 or not np.isfinite([*h['joints'],*h['finger_joints']]).all():raise ValueError('invalid source actual joint state')
    return s


def restore_once(env,snapshot,tensor):
    """ONE initialization write after reset, before any diagnostic stepping."""
    if getattr(env,'_coupon_restored',False):raise RuntimeError('restored start cannot be applied twice')
    if not np.isfinite(snapshot['held_action_14d']).all() or np.any(np.asarray(snapshot['held_action_14d'])<env._low) or np.any(np.asarray(snapshot['held_action_14d'])>env._high):raise ValueError('recorded motor command outside original action limits')
    env._coupon_restored=True;written=[]
    for name,pose in {**snapshot['poses'],'cutter':snapshot['cutter_pose']}.items():
        body=env._base.scene[name]
        body.write_root_pose_to_sim_index(root_pose=tensor([pose]),skip_forward=True)
        body.write_root_velocity_to_sim_index(root_velocity=tensor(np.zeros((1,6))),skip_forward=True);written.append(name)
    for side,hand in zip(('left','right'),snapshot['native_hands']):
        name=side+'_robot';body=env._base.scene[name];ids,fids=env._ids[name]
        positions=array(body.data.joint_pos).copy();positions[0,ids]=hand['joints'];positions[0,fids]=hand['finger_joints']
        body.write_joint_state_to_sim_index(position=tensor(positions),velocity=tensor(np.zeros_like(positions)),skip_forward=True);written.append(name)
    env._base.sim.forward()
    readback={name:float(np.linalg.norm(array(env._base.arena_world.get_pose_w(name))[0,:3]-np.asarray(pose[:3]))) for name,pose in {**snapshot['poses'],'cutter':snapshot['cutter_pose']}.items()}
    if max(readback.values())>1e-5:raise RuntimeError('native one-time pose readback disagrees with snapshot')
    return dict(native_pose_readback_translation_errors_m=readback,one_time_pose_writes=written,all_velocities_zeroed=True,source_time_s=snapshot['source_time_s'],
                scope='SYNTHETIC RESTORED ENGINEERING START; pose-only, not full dynamic replay or fresh task trial')

