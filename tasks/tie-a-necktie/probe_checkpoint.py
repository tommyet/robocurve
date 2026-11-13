"""Short reconstruction diagnostic, never a task reset or demonstration.

Initialize once from a recorded native cloth state and estimated robot velocity.
Solver warm starts are unavailable. Thereafter issue ordinary joint actions only.
This separates contact-controller experiments from the expensive pickup prefix;
a complete fresh-start episode is still required for every success claim.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import time
import traceback
import numpy as np


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state',type=Path,required=True)
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    source=Path(__file__).resolve().parent
    provenance=json.loads(args.state.with_suffix('.json').read_text())
    digest=hashlib.sha256(args.state.read_bytes()).hexdigest()
    if digest!=provenance['data_sha256']:raise ValueError('Checkpoint hash mismatch')
    for name,expected in provenance['physics_source_sha256'].items():
        if Path(name).name!=name or hashlib.sha256((source/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Physical source differs from recorded checkpoint: '+name)
    with np.load(args.state,allow_pickle=False) as archive:
        state={key:archive[key] for key in archive.files}
    plan=json.loads(args.plan.read_text())
    actions=np.asarray([frame['action14'] for frame in plan['frames']],float)
    if (plan.get('checkpoint_sha256')!=digest or actions.ndim!=2 or
            actions.shape[1]!=14 or not 1<=len(actions)<=400 or not np.isfinite(actions).all()):
        raise ValueError('Expected bounded ordinary commands for this checkpoint')
    if state['nodes'].shape!=state['velocities'].shape or state['action'].shape!=(14,):
        raise ValueError('Incomplete measured state')
    if not all(np.isfinite(x).all() for x in state.values()):raise ValueError('Nonfinite checkpoint')
    args.out.mkdir(parents=True,exist_ok=False)
    frozen=args.out/'task-source';frozen.mkdir()
    for file in source.iterdir():
        if file.suffix in ('.py','.json','.md','.npz') or file.name=='LICENSE':
            shutil.copyfile(file,frozen/file.name)
    (frozen/'fixed-motion.json').write_text(json.dumps(plan)+'\n')
    (args.out/'meshes.json').write_text(json.dumps({'tie':{'rest':state['rest'].tolist(),
        'faces':state['faces'].tolist()}})+'\n')
    started=time.monotonic()
    report=dict(kind='unscored_native_checkpoint_contact_diagnostic',status='initializing',
        score=None,demo=False,dream_requests=0,adult_collar_candidate=True,
        requested_steps=len(actions),completed_steps=0,provenance=provenance,
        plan_sha256=hashlib.sha256(args.plan.read_bytes()).hexdigest())
    def save():
        report['wall_seconds']=time.monotonic()-started
        tmp=args.out/'run.tmp.json';tmp.write_text(json.dumps(report,indent=2)+'\n')
        tmp.replace(args.out/'run.json')
    def terminated(signum,frame):raise TimeoutError('Bounded diagnostic interrupted')
    signal.signal(signal.SIGTERM,terminated);save()
    app=trace=video=dense=None
    try:
        os.environ['ROBOCURVE_TIE_INSIDE_OUT_RESET']='1'
        os.environ['ROBOCURVE_TIE_ADULT_COLLAR']='1'
        os.environ['ROBOCURVE_TIE_GRIP_REFINED']='1' if provenance.get('grip_mesh_refinement') else '0'
        os.environ['ROBOCURVE_TIE_SURFACE_CONTACT_DIAGNOSTIC']='1'
        from adult_layout import make_mesh
        authored=make_mesh()
        if (authored.rest.shape!=state['rest'].shape or
                not np.allclose(authored.rest,state['rest'],rtol=0.,atol=1e-12) or
                not np.array_equal(authored.faces,state['faces'])):
            raise ValueError('Checkpoint numerical mesh differs from the native scene')
        from isaaclab.app import AppLauncher
        app=AppLauncher(headless=True,enable_cameras=True).app
        import torch
        import imageio.v2 as imageio
        from PIL import Image
        import omni.usd
        import arena_cloth
        from yam_arena import inspect_embodiment as wrapper,scene
        from yam_arena.constants import ARM_JOINTS,FINGER_JOINTS,FINGER_OPEN,SHOULDER,WRIST,GRIPPER
        from run import encode,native_audit
        wrapper._APP=app
        emb=wrapper.YamArenaEmbodiment(task=str(source/'task.py'),object_jitter=0.,
            control_hz=20,cam_width=224,cam_height=224)
        emb._ensure_sim(None);base=emb._base;emb._env.reset()
        ids=torch.tensor([0],device=base.device,dtype=torch.long)
        for side,offset in (('left',0),('right',7)):
            robot=base.scene[side+'_robot']
            arm=robot.find_joints(list(ARM_JOINTS),preserve_order=True)[0]
            fingers=robot.find_joints(list(FINGER_JOINTS),preserve_order=True)[0]
            q=robot.data.default_joint_pos.torch.clone();v=torch.zeros_like(q)
            q[0,arm]=torch.as_tensor(state['action'][offset:offset+6],device=q.device,dtype=q.dtype)
            q[0,fingers]=float(state['action'][offset+6])*FINGER_OPEN
            v[0,arm]=torch.as_tensor(state['estimated_joint_velocity'][offset:offset+6],device=v.device,dtype=v.dtype)
            v[0,fingers]=float(state['estimated_joint_velocity'][offset+6])*FINGER_OPEN
            robot.write_joint_position_to_sim_index(position=q,env_ids=ids)
            robot.write_joint_velocity_to_sim_index(velocity=v,env_ids=ids)
            robot.actuators.target_command.set_position_index(value=q,env_ids=ids)
            robot.actuators.target_command.set_velocity_index(value=torch.zeros_like(v),env_ids=ids)
        cloth=base.scene['tie'];native=torch.as_tensor(np.c_[state['nodes'],state['velocities']][None],
            device=base.device,dtype=torch.float32)
        cloth.write_nodal_state_to_sim_index(native,env_ids=ids)
        cloth.reset(env_ids=ids)
        actual=arena_cloth.state(emb._env,'tie')
        error=float(np.max(abs(actual.nodes-state['nodes'])))
        if error>2e-6:raise RuntimeError('Checkpoint initialization mismatch')
        report.update(initial_node_error_m=error,physics_dt_s=float(base.sim.get_physics_dt()),
            native_scene_audit=native_audit(omni.usd.get_context().get_stage(),['tie'],[]),
            state_writes='One reset-only checkpoint reconstruction; none during action execution')
        limits=np.tile([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+
            [GRIPPER['velocity']/abs(FINGER_OPEN)/20],2)
        if np.any(actions<emb._low) or np.any(actions>emb._high):raise ValueError('Action bounds exceeded')
        if np.any(abs(np.diff(np.vstack((state['action'],actions)),axis=0))>limits*1.001):
            raise ValueError('Ordinary action speed exceeded')
        trace=gzip.open(args.out/'trace.jsonl.gz','wt',compresslevel=1)
        video=imageio.get_writer(args.out/'diagnostic.mp4',fps=20,codec='libx264',
            pixelformat='yuv420p',ffmpeg_params=['-movflags','+faststart'],macro_block_size=1)
        def array(value):return getattr(value,'torch',value).detach().cpu().numpy()
        from trace_data import DenseClothTrace
        dense=DenseClothTrace(args.out,arena_cloth.SPECS,len(actions)+1)
        def snapshot(step,action):
            obs=emb._observation()
            row=dict(step=step,time_s=step/20,action14=action.tolist(),
                measured_joint_pos=encode(np.asarray(obs.state['joint_pos'])),
                objects=dense.record(scene.object_states(emb._env,['tie']),step,encode),
                robot_links={name:{'names':list(base.scene[name].body_names),
                    'poses_xyzw':array(base.scene[name].data.body_link_pose_w)[0].tolist()}
                    for name in ('left_robot','right_robot')})
            trace.write(json.dumps(row,allow_nan=False)+'\n');trace.flush()
            pixels=np.asarray(obs.images['top_cam'],dtype=np.uint8);video.append_data(pixels)
            if step in (0,len(actions)):Image.fromarray(pixels).save(args.out/f'frame-{step:04d}.png')
        signal.signal(signal.SIGTERM,terminated)
        base.sim.render();base.scene.update(0.)
        snapshot(0,state['action']);report['status']='running';save()
        for step,action in enumerate(actions,1):
            emb._env.step(torch.as_tensor(action[None],device=base.device,dtype=torch.float32))
            snapshot(step,action);report['completed_steps']=step
            if step%20==0:save()
        report['status']='complete'
    except BaseException as error:
        report.update(status='failed',error=str(error),traceback=traceback.format_exc())
    finally:
        if dense is not None:dense.flush()
        if trace is not None:trace.close()
        if video is not None:video.close()
        save()
        print(json.dumps({k:report.get(k) for k in ('status','completed_steps','wall_seconds','error')}),flush=True)
        if app is not None:app.close()


if __name__=='__main__':main()
