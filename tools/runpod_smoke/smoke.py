"""Bounded, model-free YAM RGB and rigid-body physics compatibility probe.

This is a diagnostic, not task-success evidence. It changes the die's initial
height once to test gravity and table contact, then uses ordinary joint targets.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time
import traceback

REPO = Path(__file__).resolve().parents[2]
CAMERAS = ('top_cam', 'left_cam', 'right_cam')


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def worker(args):
    import numpy as np
    started = time.monotonic()
    report = {'status':'running', 'purpose':'platform compatibility, not a scored task',
              'dream_calls':0, 'steps_requested':args.steps, 'steps_completed':0,
              'initial_condition':'die lifted 0.12 m once before the diagnostic; no later object-state writes',
              'checks':{}, 'python':platform.python_version()}
    out = args.out
    write_json(out/'result.json', report)
    manifest = json.loads((REPO/'tasks/use-a-magnifying-glass/ENVIRONMENT.json').read_text())
    report['packages'] = {name:importlib.metadata.version(name) for name in manifest['packages']}
    report['checks']['recorded_versions'] = (report['packages']==manifest['packages'] and report['python']==manifest['python'])
    if not report['checks']['recorded_versions']:
        report['status']='failed'
        write_json(out/'result.json', report)
        raise RuntimeError('Package versions differ from the recorded simulator environment')
    report['source_sha256'] = {str(path.relative_to(REPO)):hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (Path(__file__), REPO/'tasks/roll-a-die/task.py')}
    os.environ.setdefault('OMNI_KIT_ACCEPT_EULA','YES')
    os.environ.setdefault('ACCEPT_EULA','Y')
    os.environ.setdefault('OMNI_KIT_ALLOW_ROOT','1')
    app = env = video = trace = None
    samples = []
    camera_stats = {name:[] for name in CAMERAS}
    try:
        from isaaclab.app import AppLauncher
        app = AppLauncher(headless=True, enable_cameras=True).app
        import cv2
        import imageio.v2 as imageio
        import torch
        from yam_arena import inspect_embodiment as wrapper
        from yam_arena.scene import object_states
        from yam_arena.task_file import TABLE_TOP
        wrapper._APP = app
        np.random.seed(0)
        torch.manual_seed(0)
        env = wrapper.YamArenaEmbodiment(task=str(REPO/'tasks/roll-a-die/task.py'),
            object_jitter=0., control_hz=20, cam_width=224, cam_height=224, headless=True)
        env._ensure_sim(None)
        env._env.reset()
        env._instruction = 'Diagnostic camera and physical response test.'
        env._t = 0.
        base = env._base
        die = base.scene['die']
        pose = die.data.default_root_pose.torch.clone()
        pose[:,:3] += base.scene.env_origins
        pose[:,2] += 0.12
        die.write_root_pose_to_sim_index(root_pose=pose)
        die.write_root_velocity_to_sim_index(root_velocity=torch.zeros_like(die.data.default_root_vel.torch))
        for _ in range(4):
            base.sim.render()
        dt = float(base.step_dt)
        report['step_dt']=dt
        report['gpu']=torch.cuda.get_device_name(0)
        report['device']=str(base.device)
        report['table_top_m']=TABLE_TOP['station']
        report['checks']['20_hz_control']=abs(dt-.05)<1e-8
        video = imageio.get_writer(str(out/'smoke.mp4'), fps=20, codec='libx264',
            pixelformat='yuv420p', macro_block_size=1, ffmpeg_params=['-movflags','+faststart'])
        trace = (out/'trace.jsonl').open('x')

        def array(value):
            value = value.torch if hasattr(value,'torch') else value
            return value.detach().cpu().numpy() if hasattr(value,'detach') else np.asarray(value)

        def record(step, target):
            state = object_states(env._env,('die',))['die']
            q = array(base.scene['left_robot'].data.joint_pos)[0]
            arm_ids = env._ids['left_robot'][0]
            row = {'step':step, 'sim_time':step*dt, 'die_position':state.pos.tolist(),
                   'die_velocity':state.lin_vel.tolist(), 'left_arm_joints':q[arm_ids].tolist(),
                   'target':target[0].tolist()}
            if not all(np.isfinite(row[key]).all() for key in ('die_position','die_velocity','left_arm_joints','target')):
                raise RuntimeError('Non-finite physics state')
            samples.append(row)
            trace.write(json.dumps(row,allow_nan=False)+'\n')
            trace.flush()
            panels=[]
            observation = env._observation() if step in (0,args.steps) else None
            for name in CAMERAS:
                rgb = np.ascontiguousarray(array(base.scene[name].data.output['rgb'])[0,:,:,:3],dtype=np.uint8)
                if rgb.shape != (360,640,3):
                    raise RuntimeError(f'{name}: unexpected native RGB shape {rgb.shape}')
                camera_stats[name].append({'mean':float(rgb.mean()),'std':float(rgb.std()),
                    'range':int(np.ptp(rgb)),'sha256':hashlib.sha256(rgb.tobytes()).hexdigest()})
                if step in (0,args.steps):
                    if not cv2.imwrite(str(out/f'{"setup" if step==0 else "final"}-{name}.png'),cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR)):
                        raise RuntimeError(f'Could not save {name} screenshot')
                    if not np.array_equal(observation.images[name],cv2.resize(rgb,(224,224))):
                        raise RuntimeError(f'{name}: YAM policy observation differs from native camera resize')
                panels.append(cv2.resize(rgb,(320,180)))
            video.append_data(np.concatenate(panels,axis=1))

        ready = array(env._ready).copy()
        record(0,ready)
        # Smooth small excursion and return, with normal open-gripper commands.
        for step in range(1,args.steps+1):
            target=ready.copy()
            phase=np.clip((step-20)/max(1,args.steps-40),0,1)
            target[0,0] += .15*np.sin(np.pi*phase)**2
            env._env.step(torch.as_tensor(target,device=base.device,dtype=torch.float32))
            env._t=step*dt
            record(step,target)
            report['steps_completed']=step
        z=np.asarray([s['die_position'][2] for s in samples])
        q=np.asarray([s['left_arm_joints'] for s in samples])
        last_z=z[-20:]
        table=float(TABLE_TOP['station'])
        metrics={'die_drop_m':float(z.max()-z.min()),'final_die_height_m':float(z[-1]),
                 'final_height_span_m':float(np.ptp(last_z)),
                 'left_yaw_excursion_rad':float(np.ptp(q[:,0])),
                 'last_die_speed_m_s':float(np.linalg.norm(samples[-1]['die_velocity']))}
        report['physics']=metrics
        report['checks'].update({'gravity_drop':metrics['die_drop_m']>.05,
            'table_support':table-.002<=z[-1]<=table+.03,
            'settled_object':metrics['final_height_span_m']<.005 and metrics['last_die_speed_m_s']<.05,
            'robot_responded':metrics['left_yaw_excursion_rad']>.05,
            'all_states_finite':True, 'completed_steps':len(samples)==args.steps+1})
        report['cameras']={name:{'frames':len(stats),'nonblank_frames':sum(s['std']>3 and s['range']>20 for s in stats),
            'unique_frames':len({s['sha256'] for s in stats}),'last_mean':stats[-1]['mean'],'last_std':stats[-1]['std']}
            for name,stats in camera_stats.items()}
        report['checks']['three_cameras_rendered']=all(s['nonblank_frames']>=args.steps-5 for s in report['cameras'].values())
        # The right arm is intentionally still and its view may be static.
        # Require temporal response from the moving left wrist camera instead.
        report['checks']['moving_camera_updates']=report['cameras']['left_cam']['unique_frames']>10
        report['checks']['yam_policy_rgb_matches_native']=True
        # NumPy comparisons can return np.bool_, which JSON cannot serialize.
        report['checks']={name:bool(value) for name,value in report['checks'].items()}
        report['status']='passed' if all(report['checks'].values()) else 'failed'
    except BaseException as error:
        report['status']='failed'
        report['error']=f'{type(error).__name__}: {error}'
        traceback.print_exc()
    finally:
        if video is not None:
            try: video.close()
            except Exception as error:
                report['status']='failed'; report['video_error']=str(error)
        if trace is not None: trace.close()
        report['elapsed_wall_seconds']=time.monotonic()-started
        write_json(out/'result.json',report)
        if app is not None: app.close()
    return 0 if report['status']=='passed' else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--steps',type=int,default=150)
    parser.add_argument('--timeout-seconds',type=int,default=600)
    parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    args.out=args.out.resolve()
    if not 100<=args.steps<=200 or not 60<=args.timeout_seconds<=900:
        parser.error('Use 100..200 steps and 60..900 seconds timeout')
    if args.worker: return worker(args)
    args.out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    with (args.out/'simulator.log').open('w') as log:
        command=[sys.executable,str(Path(__file__).resolve()),'--worker','--out',str(args.out),'--steps',str(args.steps)]
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        timed_out=False
        try: code=process.wait(timeout=args.timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out=True
            os.killpg(process.pid,signal.SIGTERM)
            try: code=process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL); code=process.wait()
    path=args.out/'result.json'
    report=json.loads(path.read_text()) if path.exists() else {'status':'failed','error':'worker produced no result'}
    report['supervisor']={'exit_code':code,'timed_out':timed_out,'wall_seconds':time.monotonic()-started}
    if timed_out or code!=0: report['status']='failed'
    if report.get('status')!='passed': report['status']='failed'
    write_json(path,report)
    print(json.dumps(report,indent=2))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':
    raise SystemExit(main())
