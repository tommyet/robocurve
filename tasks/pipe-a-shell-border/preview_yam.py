"""Unscored YAM integration preview. Robot stays at its ordinary ready pose.

Requires the pinned team simulator. No Dream call, privileged demo controller,
or object-state writes. This is an integration check, not task completion.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import traceback
import signal
import numpy as np


def array(value):
    value=getattr(value,'torch',value)
    return value.detach().cpu().numpy() if hasattr(value,'detach') else np.asarray(value)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--steps',type=int,default=60)
    p.add_argument('--plan',type=Path,help='Optional precompiled fixed action plan; no object feedback')
    p.add_argument('--judging-views',action='store_true',help='Render final close-up photos after motion; never policy inputs')
    a=p.parse_args()
    if not 1<=a.steps<=800:p.error('Preview limited to 800 control steps')
    plan=None
    if a.plan:
        plan=json.loads(a.plan.read_text())
        if plan.get('control_hz')!=20 or not plan.get('no_object_feedback') or not plan.get('frames'):
            p.error('Expected fixed 20 Hz joint plan with no object feedback')
        actions=np.asarray([f['action14'] for f in plan['frames']],float)
        if actions.shape!=(len(plan['frames']),14) or not np.isfinite(actions).all():p.error('Invalid plan actions')
        a.steps=min(a.steps,len(actions))
    a.out.mkdir(parents=True,exist_ok=False);start=time.monotonic()
    report={'status':'running','robot_demo':False,'preview_steps':a.steps,
            'source_sha256':{n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest()
                             for n in ('scene.py','native.py','material.py','preview_yam.py','contact_audit.py','review_views.py')},
            'plan_sha256':hashlib.sha256(a.plan.read_bytes()).hexdigest() if a.plan else None}
    app=None;video=None;trace=[]
    def progress(phase,step=0):
        report.update(phase=phase,completed_control_steps=step,wall_seconds=time.monotonic()-start)
        (a.out/'preview.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'phase':phase,'control_steps':step,'wall_seconds':round(report['wall_seconds'],2)}),flush=True)
        if trace:(a.out/'trace.json').write_text(json.dumps(trace,indent=2)+'\n')
    def terminate(signum,frame):
        raise SystemExit(f'Bounded preview stopped by signal {signum}')
    signal.signal(signal.SIGTERM,terminate)
    try:
        progress('application launch')
        from isaaclab.app import AppLauncher
        app=AppLauncher(headless=True,enable_cameras=True).app
        import omni.physics.tensors as tensors
        import imageio.v2 as imageio
        from PIL import Image
        import torch
        from yam_arena import inspect_embodiment as wrapper
        wrapper._APP=app
        emb=wrapper.YamArenaEmbodiment(task=str(Path(__file__).with_name('scene.py')),
            object_jitter=0.,control_hz=20,cam_width=224,cam_height=224)
        progress('build YAM scene and initialize renderer')
        from yam_arena import scene as adapter
        original_make_env=adapter.make_env
        if a.judging_views:
            from review_views import configure
            def make_env(embodiment,**kwargs):
                configure(embodiment)
                return original_make_env(embodiment,**kwargs)
            adapter.make_env=make_env
        try:
            emb._ensure_sim(None)
        finally:
            adapter.make_env=original_make_env
        progress('native tensor and contact views')
        import sys
        # The task loader may give scene.py a generated module name. Its hook
        # closure owns the exact runtime, avoiding a second scene import.
        from yam_arena import scene as adapter
        namespace=adapter.task_object.__globals__
        roots,coupling=namespace['ROOTS'],namespace['COUPLING']
        sim=tensors.create_simulation_view('torch');sim.set_subspace_roots('/')
        barrel=sim.create_rigid_body_view(roots['barrel']);plunger=sim.create_rigid_body_view(roots['plunger'])
        import omni.usd
        from contact_audit import NativeContactAudit
        other_contact=NativeContactAudit(omni.usd.get_context().get_stage(),sim,coupling.material,
            excluded_body_paths=(),
            allowed_shape_paths=[roots['barrel']+f'/NozzleSector{i:02d}' for i in range(24)])
        base=emb._base;write=base.scene.write_data_to_sim
        report['robot_body_names']={name:list(base.scene[name].body_names) for name in ('left_robot','right_robot')}
        def step_material(*args,**kwargs):
            out=write(*args,**kwargs)
            fb,fp=coupling.advance(array(barrel.get_transforms())[0],array(barrel.get_velocities())[0],
                                   array(plunger.get_transforms())[0],float(base.physics_dt))
            for view,force,torque in ((barrel,fb,coupling.last_contact_torque),(plunger,fp,np.zeros(3))):
                view.apply_forces_and_torques_at_position(force_data=torch.as_tensor(force,dtype=torch.float32,device=base.device).reshape(1,3),
                    torque_data=torch.as_tensor(torque,dtype=torch.float32,device=base.device).reshape(1,3),position_data=None,
                    indices=torch.tensor([0],dtype=torch.int32,device=base.device),is_global=True)
            other_contact.update(coupling.material.time_s)
            return out
        base.scene.write_data_to_sim=step_material
        progress('episode reset')
        emb._env.reset()
        coupling.reset()
        other_contact.events.clear()
        video=imageio.get_writer(a.out/'preview.mp4',fps=20,codec='libx264',pixelformat='yuv420p',
                                ffmpeg_params=['-movflags','+faststart'],macro_block_size=1)
        def snapshot(step):
            rgb=array(base.scene['top_cam'].data.output['rgb'])[0,:,:,:3].astype(np.uint8)
            video.append_data(rgb)
            if not step:Image.fromarray(rgb).save(a.out/'setup.png')
            trace.append({'step':step,
                          'robot_joints':{name:array(base.scene[name].data.joint_pos)[0].tolist() for name in ('left_robot','right_robot')},
                          'robot_links_xyzw':{name:array(base.scene[name].data.body_link_pose_w)[0].tolist() for name in ('left_robot','right_robot')},
                          'barrel_pose_xyzw':array(barrel.get_transforms())[0].tolist(),
                          'plunger_pose_xyzw':array(plunger.get_transforms())[0].tolist(),
                          'piston_m':coupling.last_piston_m,'pressure_reaction_n':coupling.last_reaction_n,
                          'emitted_ml':coupling.material.emitted_m3*1e6,
                          'material_contact_invalid':bool(other_contact.events)})
        snapshot(0)
        progress('fixed action preview',0)
        for i in range(a.steps):
            action=emb._ready if plan is None else torch.tensor([actions[i]],device=base.device,dtype=torch.float32)
            emb._env.step(action);coupling.update_surface();snapshot(i+1)
            if (i+1)%20==0 or i+1==a.steps:progress('fixed action preview',i+1)
        video.close();video=None
        for name in ('top_cam','left_cam','right_cam'):
            Image.fromarray(array(base.scene[name].data.output['rgb'])[0,:,:,:3].astype(np.uint8)).save(a.out/f'final-{name}.png')
        (a.out/'trace.json').write_text(json.dumps(trace,indent=2)+'\n')
        coupling.material.save(a.out/'material.npz')
        report.update(balance=coupling.material.balance(),other_contact=other_contact.summary())
        if a.judging_views:
            progress('final judging photographs',a.steps)
            from review_views import capture_final
            report['judging_cameras']=capture_final(base,a.out)
        report.update(status='complete',balance=coupling.material.balance(),score=None,
                      other_contact=other_contact.summary(),
                      note='Unscored integration preview; no full task, Dream trial or media evidence.')
    except BaseException as exc:
        report.update(status='failed',error=f'{type(exc).__name__}: {exc}',traceback=traceback.format_exc());raise
    finally:
        if video is not None:video.close()
        report['wall_seconds']=time.monotonic()-start
        (a.out/'preview.json').write_text(json.dumps(report,indent=2)+'\n')
        if trace:(a.out/'trace.json').write_text(json.dumps(trace,indent=2)+'\n')
        if app:app.close()


if __name__=='__main__':main()
