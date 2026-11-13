"""Bounded frozen-action pickup coupon, with no cloth and no task score.

The exact seam tool is simulated on the same YAM station. This isolates tool
grasp/orientation from the separate expensive cloth-contact investigation.
Measured object state is logged only; it never changes the robot actions.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import signal
import time
import traceback
import numpy as np

HERE=Path(__file__).resolve().parent


def array(value):return getattr(value,'torch',value).detach().cpu().numpy().copy()


def fixed_actions(plan,steps,release_control=False):
    if plan.get('control_hz')!=20 or plan.get('no_object_feedback') is not True:
        raise ValueError('A frozen 20 Hz plan without object feedback is required')
    rows=plan['frames'][:steps]
    actions=np.asarray([row['action14'] for row in rows],float)
    phases=[row['phase'] for row in rows]
    if actions.shape!=(steps,14) or not np.isfinite(actions).all():
        raise ValueError('Incomplete or nonfinite frozen actions')
    if release_control:
        final=actions[-1].copy();extra=[final.copy() for _ in range(20)]
        phases+=['hold lifted tool']*20
        for i in range(1,21):
            action=final.copy();action[13]+=i/20*(1.-action[13]);extra.append(action)
        phases+=['open right gripper']*20
        extra += [extra[-1].copy() for _ in range(40)]
        phases+=['observe released tool']*40
        actions=np.vstack((actions,extra))
    return actions,phases


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--plan',type=Path,default=HERE/'evidence/pickup-plan.json')
    p.add_argument('--steps',type=int,default=140,help='140 actions end just after lifting the tool; 280 include high hover')
    p.add_argument('--physics-hz',type=int,choices=(240,480,960),default=240)
    p.add_argument('--release-control',action='store_true',help='Append a fixed 1 s hold, 1 s opening and 2 s free-fall observation')
    a=p.parse_args()
    if not 1<=a.steps<=280:p.error('Coupon limited to 1–280 plan actions')
    actions,phases=fixed_actions(json.loads(a.plan.read_text()),a.steps,a.release_control)
    a.out.mkdir(parents=True,exist_ok=False)
    source=a.out/'task-source';source.mkdir()
    hashes={}
    for path in HERE.glob('*.py'):
        compile(path.read_bytes(),str(path),'exec')
        hashes[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
        shutil.copyfile(path,source/path.name)
    shutil.copyfile(a.plan,source/'fixed-plan.json')
    hashes['fixed-plan.json']=hashlib.sha256(a.plan.read_bytes()).hexdigest()
    started=time.monotonic()
    report={'status':'running','scope':'tool-only contact pickup coupon; no cloth, cutting or material assessment',
            'robot_demo':False,'task_score':None,'dream_requests':0,
            'requested_steps':len(actions),'completed_steps':0,'control_hz':20,
            'physics_hz':a.physics_hz,'release_control':a.release_control,
            'policy':'frozen joint targets; no object feedback','source_sha256':hashes}
    app=video=trace=None
    def save():
        report['wall_seconds']=time.monotonic()-started
        pending=a.out/'tool-probe.json.tmp';pending.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        pending.replace(a.out/'tool-probe.json')
    def interrupted(signum,frame):raise InterruptedError('Tool coupon stopped by external wall-time limit')
    previous_handler=signal.signal(signal.SIGTERM,interrupted)
    try:
        from isaaclab.app import AppLauncher
        app=AppLauncher(headless=True,enable_cameras=True).app
        import torch
        import imageio.v2 as imageio
        from PIL import Image
        import omni.physics.tensors as tensors
        import omni.usd
        from yam_arena import inspect_embodiment as wrapper,scene as adapter
        from yam_arena.constants import SHOULDER,WRIST,GRIPPER,FINGER_OPEN,TCP_OFFSET
        from preview_yam import rotation
        wrapper._APP=app;adapter.PHYSICS_DT=1/a.physics_hz
        emb=wrapper.YamArenaEmbodiment(task=str(HERE/'tool_scene.py'),object_jitter=0.,
            control_hz=20,cam_width=224,cam_height=224)
        emb._ensure_sim(None);base=emb._base
        roots=adapter.task_object.__globals__['ROOTS']
        stage=omni.usd.get_context().get_stage()
        if any('Attachment' in prim.GetTypeName() for prim in stage.Traverse()):
            raise RuntimeError('Tool coupon cannot use hidden attachments')
        sim=tensors.create_simulation_view('torch');sim.set_subspace_roots('/')
        handle=sim.create_rigid_body_view(roots['ripper_handle'])
        blade=sim.create_rigid_body_view(roots['ripper_blade'])
        if handle.count!=1 or blade.count!=1:raise RuntimeError('Exact native tool bodies missing')
        if abs(float(base.physics_dt)-1/a.physics_hz)>1e-10:raise RuntimeError('Timestep mismatch')
        emb._env.reset()
        ready=array(emb._ready)[0]
        limits=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+
                               [GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
        if np.any(actions<emb._low) or np.any(actions>emb._high) or np.any(np.abs(np.diff(np.vstack((ready,actions)),axis=0))>limits*1.001):
            raise ValueError('Frozen coupon actions exceed ordinary limits')
        robot=base.scene['right_robot'];gripper_index=robot.body_names.index('gripper')
        video=imageio.get_writer(a.out/'tool-pickup.mp4',fps=20,codec='libx264',pixelformat='yuv420p',
                                ffmpeg_params=['-movflags','+faststart'],macro_block_size=1)
        trace=gzip.open(a.out/'tool-trace.jsonl.gz','wt')
        heights=[]
        def snapshot(step,action,phase):
            pose=array(handle.get_transforms())[0];blade_pose=array(blade.get_transforms())[0]
            hand=array(robot.data.body_link_pose_w)[0,gripper_index]
            hand_R=rotation(hand[3:]);tcp=hand[:3]+hand_R@np.asarray(TCP_OFFSET)
            rgb=array(base.scene['top_cam'].data.output['rgb'])[0,:,:,:3].astype(np.uint8)
            video.append_data(rgb)
            if step==0:Image.fromarray(rgb).save(a.out/'setup.png')
            heights.append(float(pose[2]))
            row={'step':step,'time_s':step/20,'phase':phase,'action14':action.tolist(),
                 'handle_pose_xyzw':pose.tolist(),'blade_pose_xyzw':blade_pose.tolist(),
                 'right_gripper_pose_xyzw':hand.tolist(),'right_tcp_position_m':tcp.tolist(),
                 'handle_position_in_gripper_m':(hand_R.T@(pose[:3]-hand[:3])).tolist(),
                 'handle_rotation_in_gripper':(hand_R.T@rotation(pose[3:])).tolist()}
            trace.write(json.dumps(row,allow_nan=False)+'\n');trace.flush()
            report['completed_steps']=step
            report['last_handle_pose_xyzw']=pose.tolist()
            report['maximum_handle_height_increase_m']=max(heights)-heights[0]
            return pose
        snapshot(0,ready,'reset');save()
        for step,(action,phase) in enumerate(zip(actions,phases),1):
            emb._env.step(torch.as_tensor(action[None],device=base.device,dtype=torch.float32))
            pose=snapshot(step,action,phase)
            if step==a.steps:report['plan_end_handle_z_m']=float(pose[2])
            if a.release_control and step==a.steps+20:report['before_release_handle_z_m']=float(pose[2])
            if step%20==0:save()
        for name in ('top_cam','left_cam','right_cam'):
            Image.fromarray(array(base.scene[name].data.output['rgb'])[0,:,:,:3].astype(np.uint8)).save(a.out/f'final-{name}.png')
        report['final_handle_height_increase_m']=heights[-1]-heights[0]
        if a.release_control:report['handle_drop_after_release_m']=report['before_release_handle_z_m']-heights[-1]
        report['status']='complete'
    except BaseException as exc:
        report.update(status='interrupted' if isinstance(exc,InterruptedError) else 'failed',
                      error=f'{type(exc).__name__}: {exc}',traceback=traceback.format_exc())
        raise
    finally:
        if trace:trace.close()
        if video:video.close()
        save();signal.signal(signal.SIGTERM,previous_handler)
        if app:app.close()


if __name__=='__main__':main()
