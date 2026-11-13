"""Bounded robot/camera integration test, not a successful truing demo."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import time
import numpy as np


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--steps', type=int, default=40)
    p.add_argument('--physics-hz', type=int, choices=(1000, 2000), default=1000)
    a = p.parse_args()
    if not 1 <= a.steps <= 100:
        p.error('Preview is limited to 100 control steps')
    a.out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    report = {'kind': 'wheel_yam_integration_preview', 'status': 'running', 'score': None,
        'robot_demo': False, 'dream_requests': 0, 'requested_steps': a.steps,
        'source_sha256': {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                         for f in Path(__file__).parent.glob('*.py')}}
    app = video = trace = None
    try:
        from isaaclab.app import AppLauncher
        app = AppLauncher(headless=True, enable_cameras=True).app
        import imageio.v2 as imageio
        from PIL import Image
        import omni.usd
        import arena_wheel
        from yam_arena import inspect_embodiment as wrapper, scene as adapter
        wrapper._APP = app
        emb = wrapper.YamArenaEmbodiment(task=str(Path(__file__).with_name('task.py')),
            object_jitter=0., control_hz=20, cam_width=224, cam_height=224)
        original_dt = adapter.PHYSICS_DT
        adapter.PHYSICS_DT = 1/a.physics_hz
        try:
            emb._ensure_sim(None)
        finally:
            adapter.PHYSICS_DT = original_dt
        base = emb._base
        arena_wheel.install_material_hook(base, omni.usd.get_context().get_stage())
        emb._env.reset()
        trace = gzip.open(a.out/'trace.jsonl.gz', 'wt')
        video = imageio.get_writer(a.out/'preview.mp4', fps=20, codec='libx264', pixelformat='yuv420p',
                                  ffmpeg_params=['-movflags', '+faststart'], macro_block_size=1)
        for step in range(a.steps+1):
            if step:
                emb._env.step(emb._ready)
            observation = emb._observation()
            state = arena_wheel.state(emb._env, 'wheel_station')
            materials = arena_wheel.ASSEMBLIES['wheel_station']['coupling'].observation_for_assessor()
            trace.write(json.dumps({'step': step, 'time_s': step/20,
                'joint_pos': np.asarray(observation.state['joint_pos']).tolist(),
                'body_names': list(state.body_names), 'body_poses': state.body_poses.tolist(),
                'body_velocities': state.body_velocities.tolist(), 'materials': materials})+'\n')
            rgb = base.scene['top_cam'].data.output['rgb']
            rgb = getattr(rgb, 'torch', rgb)
            frame = rgb.detach().cpu().numpy()[0, :, :, :3].astype(np.uint8)
            video.append_data(frame)
            if step in (0, a.steps):
                Image.fromarray(frame).save(a.out/('setup.png' if step == 0 else 'final.png'))
        report.update(status='complete', completed_steps=a.steps, bodies=len(state.body_names),
                      physics_dt_s=float(base.sim.get_physics_dt()))
    except BaseException as error:
        report.update(status='failed', error=f'{type(error).__name__}: {error}')
        raise
    finally:
        if trace: trace.close()
        if video: video.close()
        report['wall_seconds'] = time.monotonic()-started
        (a.out/'preview.json').write_text(json.dumps(report, indent=2)+'\n')
        if app: app.close()


if __name__ == '__main__':
    main()
