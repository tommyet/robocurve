"""Bounded robot/camera integration test, not a successful truing demo."""
import argparse
import gzip
import hashlib
import json
import signal
from pathlib import Path
import time
import traceback
import numpy as np


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--steps', type=int, default=2)
    p.add_argument('--device',choices=('cpu','cuda:0'),default='cpu',help='Physics/tensor backend; cameras still use the GPU renderer')
    p.add_argument('--plan',type=Path,help='Frozen ordinary14-D joint commands; remains a diagnostic')
    p.add_argument('--wheel-clocking-deg',type=float,choices=(0.,10.,20.,50.),default=0.)
    p.add_argument('--nipple-flat-phase-deg',type=float,choices=(0.,45.),default=0.)
    p.add_argument('--physics-hz', type=int, choices=(10000,20000,40000,80000), default=40000)
    p.add_argument('--reset-profile',choices=('four-defect-reference','two-defect-candidate'),default='two-defect-candidate')
    p.add_argument('--solver-position-iterations',type=int,choices=(32,64,128),default=32)
    a = p.parse_args()
    plan=actions=None
    if a.plan is not None:
        from motion_plan import load
        plan,actions=load(a.plan)
        for name,expected in plan['source_sha256'].items():
            if hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()!=expected:
                p.error('Plan geometry/source changed; recompile: '+name)
        a.wheel_clocking_deg=plan['wheel_clocking_deg'];a.nipple_flat_phase_deg=plan['nipple_flat_phase_deg']
        a.reset_profile=plan['reset_profile']
        if a.steps>len(actions):p.error('Requested steps exceed frozen plan')
    if not 1 <= a.steps <= (1200 if plan else 100):
        p.error('Preview is limited to 100 control steps')
    a.out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    report = {'kind': 'wheel_yam_integration_preview', 'status': 'running', 'score': None,
        'robot_demo': False, 'dream_requests': 0, 'requested_steps': a.steps,
        'requested_device':a.device,
        'wheel_clocking_deg':a.wheel_clocking_deg,'nipple_flat_phase_deg':a.nipple_flat_phase_deg,
        'plan_sha256':hashlib.sha256(a.plan.read_bytes()).hexdigest() if a.plan else None,
        'phase':'launch','completed_steps':0,
        'reset_profile':a.reset_profile,'solver_position_iterations':a.solver_position_iterations,
        'source_sha256': {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                         for f in Path(__file__).parent.glob('*.py')}}
    def save():
        report['wall_seconds']=time.monotonic()-started
        temporary=a.out/'preview.json.tmp';temporary.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');temporary.replace(a.out/'preview.json')
    def interrupted(signum,frame):raise RuntimeError('Interrupted by '+signal.Signals(signum).name)
    previous={s:signal.signal(s,interrupted) for s in (signal.SIGTERM,signal.SIGINT)}
    save()
    app = video = trace = None
    try:
        from isaaclab.app import AppLauncher
        app = AppLauncher(headless=True, enable_cameras=True,device=a.device).app
        import imageio.v2 as imageio
        from PIL import Image
        import omni.usd
        import arena_wheel
        arena_wheel.RESET_PROFILE_OVERRIDE=a.reset_profile
        arena_wheel.SOLVER_ITERATIONS_OVERRIDE=a.solver_position_iterations
        arena_wheel.CLOCKING_RAD_OVERRIDE=np.deg2rad(a.wheel_clocking_deg)
        arena_wheel.FLAT_PHASE_RAD_OVERRIDE=np.deg2rad(a.nipple_flat_phase_deg)
        report['phase']='build';save()
        from yam_arena import inspect_embodiment as wrapper, scene as adapter
        wrapper._APP = app
        emb = wrapper.YamArenaEmbodiment(task=str(Path(__file__).with_name('task.py')),
            object_jitter=0., control_hz=20, cam_width=224, cam_height=224,device=a.device)
        original_dt = adapter.PHYSICS_DT
        adapter.PHYSICS_DT = 1/a.physics_hz
        try:
            emb._ensure_sim(None)
        finally:
            adapter.PHYSICS_DT = original_dt
        base = emb._base
        report['effective_device']=str(base.device)
        report['physics_step_s']=float(base.sim.get_physics_dt())
        report['control_step_wall_seconds']=[]
        arena_wheel.install_material_hook(base, omni.usd.get_context().get_stage())
        emb._env.reset()
        import torch
        ready=emb._ready.detach().cpu().numpy()[0].copy()
        if actions is not None:
            from yam_arena.constants import SHOULDER,WRIST,GRIPPER,FINGER_OPEN
            from yam_arena import YAM_URDF
            if hashlib.sha256(Path(YAM_URDF).read_bytes()).hexdigest()!=plan['urdf_sha256']:
                raise ValueError('Plan URDF differs from pinned runtime; recompile before physics trial')
            if np.any(actions<emb._low) or np.any(actions>emb._high):raise ValueError('Plan exceeds adapter limits')
            limit=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
            if np.any(np.abs(np.diff(np.vstack((ready,actions)),axis=0))>limit*1.001):raise ValueError('Plan exceeds ordinary speed limits')
        report['phase']='simulate';save()
        trace = gzip.open(a.out/'trace.jsonl.gz', 'wt')
        video = imageio.get_writer(a.out/'preview.mp4', fps=20, codec='libx264', pixelformat='yuv420p',
                                  ffmpeg_params=['-movflags', '+faststart'], macro_block_size=1)
        for step in range(a.steps+1):
            if step:
                command=emb._ready if actions is None else torch.as_tensor(actions[step-1][None],device=base.device,dtype=torch.float32)
                tick=time.perf_counter();emb._env.step(command)
                report['control_step_wall_seconds'].append(time.perf_counter()-tick)
                emb._t=step/20
            report['completed_steps']=step
            observation = emb._observation()
            state = arena_wheel.state(emb._env, 'wheel_station')
            materials = arena_wheel.ASSEMBLIES['wheel_station']['coupling'].observation_for_assessor()
            trace.write(json.dumps({'step': step, 'time_s': step/20,
                'joint_pos': np.asarray(observation.state['joint_pos']).tolist(),
                'action14':(ready if step==0 or actions is None else actions[step-1]).tolist(),
                'stage':'ready' if step==0 or plan is None else plan['frames'][step-1]['stage'],
                'body_names': list(state.body_names), 'body_poses': state.body_poses.tolist(),
                'body_velocities': state.body_velocities.tolist(), 'materials': materials})+'\n')
            rgb = base.scene['top_cam'].data.output['rgb']
            rgb = getattr(rgb, 'torch', rgb)
            frame = rgb.detach().cpu().numpy()[0, :, :, :3].astype(np.uint8)
            video.append_data(frame)
            trace.flush()
            if step%10==0:save()
            if step in (0, a.steps):
                Image.fromarray(frame).save(a.out/('setup.png' if step == 0 else 'final.png'))
        report['rim_integrity']=arena_wheel.ASSEMBLIES['wheel_station']['coupling'].audit_integrity()
        report.update(status='complete', completed_steps=a.steps, bodies=len(state.body_names),
                      physics_dt_s=float(base.sim.get_physics_dt()))
    except BaseException as error:
        report.update(status='failed', error=f'{type(error).__name__}: {error}',traceback=traceback.format_exc())
        raise
    finally:
        if trace: trace.close()
        if video: video.close()
        save()
        for sig,handler in previous.items():signal.signal(sig,handler)
        if app: app.close()


if __name__ == '__main__':
    main()
