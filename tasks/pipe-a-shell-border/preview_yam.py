"""Record native YAM diagnostics, frozen-plan demos or direct Dream trials.

Requires the pinned team simulator. Policies receive standard observations;
measured tool state is used only by physical coupling and assessment. Saved
execution must be independently judged before claiming task completion.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import traceback
import signal
import shutil
import numpy as np


def array(value):
    value=getattr(value,'torch',value)
    return value.detach().cpu().numpy() if hasattr(value,'detach') else np.asarray(value)


def main(*, default_policy='diagnostic', default_steps=60, default_review=False):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--steps',type=int,default=default_steps)
    p.add_argument('--policy',choices=('diagnostic','demo','dream'),default=default_policy)
    p.add_argument('--plan',type=Path,help='Optional precompiled fixed action plan; no object feedback')
    p.add_argument('--joint-feedback',action='store_true',help='Bounded demo PI tracking from standard joint observations only')
    p.add_argument('--judging-views',action='store_true',default=default_review,help='Record close-up review views; never policy inputs')
    a=p.parse_args()
    if not 1<=a.steps<=2400:p.error('Trial limited to 2400 control steps')
    if a.policy=='demo' and a.plan is None:p.error('Demo requires a frozen joint plan')
    if a.policy=='dream' and (a.plan or a.joint_feedback):p.error('Dream uses its own ordinary actions')
    plan=None
    if a.plan:
        plan=json.loads(a.plan.read_text())
        if plan.get('control_hz')!=20 or not plan.get('no_object_feedback') or not plan.get('frames'):
            p.error('Expected fixed 20 Hz joint plan with no object feedback')
        actions=np.asarray([f['action14'] for f in plan['frames']],float)
        if actions.shape!=(len(plan['frames']),14) or not np.isfinite(actions).all():p.error('Invalid plan actions')
        a.steps=min(a.steps,len(actions))
    a.out.mkdir(parents=True,exist_ok=False);start=time.monotonic()
    frozen=a.out/'task-source';frozen.mkdir()
    for source in Path(__file__).parent.glob('*.py'):shutil.copyfile(source,frozen/source.name)
    metadata_path=Path(__file__).with_name('task.json')
    if not metadata_path.exists():metadata_path=Path(__file__).with_name('task.draft.json')
    metadata=json.loads(metadata_path.read_text())
    shutil.copyfile(metadata_path,frozen/'task-description.json')
    if a.plan:shutil.copyfile(a.plan,frozen/'fixed-plan.json')
    report={'status':'running','robot_demo':a.policy=='demo','policy':a.policy,
            'full_score_demonstrated':False,'preview_steps':a.steps,'control_hz':20,
            'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in frozen.glob('*') if p.is_file()},
            'plan_sha256':hashlib.sha256(a.plan.read_bytes()).hexdigest() if a.plan else None,
            'joint_feedback':a.joint_feedback}
    app=None;video=None;trace=[];dream_policy=None;request_audit=[];session_audit={'session_count':0}
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
        report['tool_body_paths']={name:roots[name] for name in ('barrel','plunger')}
        sim=tensors.create_simulation_view('torch');sim.set_subspace_roots('/')
        barrel=sim.create_rigid_body_view(roots['barrel']);plunger=sim.create_rigid_body_view(roots['plunger'])
        import omni.usd
        from contact_audit import NativeContactAudit
        other_contact=NativeContactAudit(omni.usd.get_context().get_stage(),sim,coupling.material,
            excluded_body_paths=(),
            allowed_shape_paths=[roots['barrel']+f'/NozzleSector{i:02d}' for i in range(24)])
        base=emb._base;write=base.scene.write_data_to_sim
        report['physics_dt_s']=float(base.physics_dt)
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
            if a.judging_views:
                from review_views import composite_frame
                rgb=composite_frame(base)
            video.append_data(rgb)
            if not step:Image.fromarray(rgb).save(a.out/'setup.png')
            trace.append({'step':step,
                          'time_s':step/20,
                          'native_physics_step':int(base.sim._physics_step_count),
                          'observed_action14':np.asarray(emb._observation().state['joint_pos'],float).tolist(),
                          'robot_joints':{name:array(base.scene[name].data.joint_pos)[0].tolist() for name in ('left_robot','right_robot')},
                          'robot_links_xyzw':{name:array(base.scene[name].data.body_link_pose_w)[0].tolist() for name in ('left_robot','right_robot')},
                          'rigid_bounds_m':dict(other_contact.world_bounds),
                          'barrel_pose_xyzw':array(barrel.get_transforms())[0].tolist(),
                          'plunger_pose_xyzw':array(plunger.get_transforms())[0].tolist(),
                          'piston_m':coupling.last_piston_m,'pressure_reaction_n':coupling.last_reaction_n,
                          'nozzle_contact_force_n':coupling.last_contact_force.tolist(),
                          'nozzle_contact_torque_nm':coupling.last_contact_torque.tolist(),
                          'emitted_ml':coupling.material.emitted_m3*1e6,
                          'material_contact_invalid':bool(other_contact.events)})
        snapshot(0)
        if a.policy=='dream':
            from inspect_robots import Scene
            from dream_policy import make_policy
            instruction=metadata['instruction']
            dream_policy=make_policy(request_audit,session_audit,rows_per_request=8)
            dream_policy.bind(emb.info)
            dream_policy.reset(Scene(id='pipe-shell-border',instruction=instruction))
            report['dream_model']=dream_policy.info.checkpoint
        progress('fixed action preview',0)
        from joint_tracking import JointTracking
        tracking=JointTracking()
        report['joint_tracking_parameters']={k:getattr(tracking,k) for k in ('kp','ki','limit','slew')}
        for i in range(a.steps):
            observation=emb._observation()
            if dream_policy is not None:
                chunk=dream_policy.act(observation)
                if len(chunk.actions)!=1:raise RuntimeError('Expected one ordinary Dream control action')
                reference=np.asarray(chunk.actions[0].data,float)
            else:
                reference=emb._ready[0].detach().cpu().numpy() if plan is None else actions[i]
            observed=np.asarray(observation.state['joint_pos'],float)
            requested=tracking.action(reference,observed,enabled=a.joint_feedback and i>=340)
            applied=np.clip(requested,emb._low,emb._high)
            action=torch.tensor([applied],device=base.device,dtype=torch.float32)
            emb._env.step(action);emb._t=(i+1)/20;coupling.update_surface();snapshot(i+1)
            trace[-1].update(reference_action14=reference.tolist(),requested_action14=requested.tolist(),
                             applied_action14=applied.tolist(),joint_tracking_bias12=tracking.bias.tolist())
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
                      note='Execution complete; independently rescore saved material and trajectory before any task-success claim.')
    except BaseException as exc:
        report.update(status='failed',error=f'{type(exc).__name__}: {exc}',traceback=traceback.format_exc());raise
    finally:
        if video is not None:video.close()
        if dream_policy is not None:
            from dream_policy import public_transcript
            (a.out/'dream-transcript.json').write_text(json.dumps(public_transcript(dream_policy),indent=2)+'\n')
        report.update(dream_requests=len(request_audit),dream_session_audit=session_audit)
        if request_audit:(a.out/'dream-requests.json').write_text(json.dumps(request_audit,indent=2)+'\n')
        report['wall_seconds']=time.monotonic()-start
        (a.out/'preview.json').write_text(json.dumps(report,indent=2)+'\n')
        if trace:(a.out/'trace.json').write_text(json.dumps(trace,indent=2)+'\n')
        if app:app.close()


if __name__=='__main__':main()
