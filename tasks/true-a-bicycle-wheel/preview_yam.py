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
    p.add_argument('--contact-audit-diagnostic',action='store_true',help='Read native bench/stand contact patches and their torque')
    p.add_argument('--external-forces-once-diagnostic',action='store_true',help='Diagnostic override of ordinary proportional force integration')
    p.add_argument('--no-rewind-diagnostic',action='store_true',help='Preserve constructor native state; not a repeatable task reset')
    p.add_argument('--freeze-thread-diagnostic',action='store_true',help='Isolate native assembly without custom thread writes or torques')
    p.add_argument('--joint-tracking-diagnostic',action='store_true',help='Bounded integral tracking from ordinary robot joint measurements only; requires --plan')
    p.add_argument('--central-spring-candidate',action='store_true')
    p.add_argument('--solver-type',choices=('TGS','PGS'),default='TGS')
    p.add_argument('--distance-tolerance-compensation-m',type=float,choices=(0.,.025),default=0.)
    p.add_argument('--preloaded-reset-candidate',action='store_true',help='Use the measured loaded internal shape only when constructing/resetting the scene')
    p.add_argument('--tool-pose-servo-diagnostic',action='store_true',help='Disclosed scripted-demo tool-pose feedback; ordinary joint commands only, never used by Dream')
    p.add_argument('--nipple-target-servo-diagnostic',action='store_true',help='Also latch measured square-nipple frame before each ordinary quarter-turn; requires tool servo')
    p.add_argument('--plan',type=Path,help='Frozen ordinary14-D joint commands; remains a diagnostic')
    p.add_argument('--wheel-clocking-deg',type=float,choices=(0.,10.,20.,50.,55.),default=0.)
    p.add_argument('--nipple-flat-phase-deg',type=float,choices=(0.,45.),default=0.)
    p.add_argument('--physics-hz', type=int, choices=(2000,10000,20000,40000,80000), default=40000)
    p.add_argument('--reset-profile',choices=('four-defect-reference','two-defect-candidate'),default='two-defect-candidate')
    p.add_argument('--solver-position-iterations',type=int,choices=(32,64,128),default=32)
    a = p.parse_args()
    if a.distance_tolerance_compensation_m and not a.central_spring_candidate:p.error('Distance tolerance requires central-spring candidate')
    if a.central_spring_candidate and a.device!='cpu':p.error('Native DistanceJoint is CPU only')
    if a.solver_type=='PGS' and (not a.central_spring_candidate or a.external_forces_once_diagnostic):
        p.error('PGS candidate requires the central spring and has no TGS force-integration override')
    if a.joint_tracking_diagnostic and a.plan is None:p.error('Joint tracking requires a frozen nominal plan')
    if a.tool_pose_servo_diagnostic and (a.plan is None or not a.joint_tracking_diagnostic):
        p.error('Tool pose servo requires a plan and bounded joint tracking')
    if a.nipple_target_servo_diagnostic and not a.tool_pose_servo_diagnostic:p.error('Nipple targeting requires tool pose servo')
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
        'requested_device':a.device,'joint_tracking_diagnostic':a.joint_tracking_diagnostic,
        'external_forces_once_diagnostic':a.external_forces_once_diagnostic,
        'no_rewind_diagnostic':a.no_rewind_diagnostic,'freeze_thread_diagnostic':a.freeze_thread_diagnostic,
        'preloaded_reset_candidate':a.preloaded_reset_candidate,
        'central_spring_candidate':a.central_spring_candidate,
        'solver_type':a.solver_type,
        'distance_tolerance_compensation_m':a.distance_tolerance_compensation_m,
        'tool_pose_servo_diagnostic':a.tool_pose_servo_diagnostic,
        'nipple_target_servo_diagnostic':a.nipple_target_servo_diagnostic,
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
        arena_wheel.CONTACT_AUDIT_DIAGNOSTIC=a.contact_audit_diagnostic
        arena_wheel.NO_REWIND_DIAGNOSTIC=a.no_rewind_diagnostic
        arena_wheel.FROZEN_MATERIAL_DIAGNOSTIC=a.freeze_thread_diagnostic
        arena_wheel.PRELOADED_RESET_CANDIDATE=a.preloaded_reset_candidate
        arena_wheel.CENTRAL_SPRING_CANDIDATE=a.central_spring_candidate
        arena_wheel.SOLVER_TYPE=a.solver_type
        arena_wheel.DISTANCE_TOLERANCE_COMPENSATION_M=a.distance_tolerance_compensation_m
        report['phase']='build';save()
        from yam_arena import inspect_embodiment as wrapper, scene as adapter
        wrapper._APP = app
        emb = wrapper.YamArenaEmbodiment(task=str(Path(__file__).with_name('task.py')),
            object_jitter=0., control_hz=20, cam_width=224, cam_height=224,device=a.device)
        original_dt = adapter.PHYSICS_DT
        original_cfg_callback=adapter.env_cfg_callback
        if a.external_forces_once_diagnostic:
            def configure_callback(*args,**kwargs):
                configure=original_cfg_callback(*args,**kwargs)
                def override(cfg):
                    cfg=configure(cfg)
                    if cfg.sim.physics is None:
                        from isaaclab_physx.physics import PhysxCfg
                        cfg.sim.physics=PhysxCfg()
                    cfg.sim.physics.enable_external_forces_every_iteration=False
                    return cfg
                return override
            adapter.env_cfg_callback=configure_callback
        adapter.PHYSICS_DT = 1/a.physics_hz
        try:
            emb._ensure_sim(None)
        finally:
            adapter.PHYSICS_DT = original_dt
            adapter.env_cfg_callback=original_cfg_callback
        base = emb._base
        report['effective_device']=str(base.device)
        report['physics_step_s']=float(base.sim.get_physics_dt())
        report['control_step_wall_seconds']=[]
        arena_wheel.install_material_hook(base, omni.usd.get_context().get_stage())
        emb._env.reset()
        from momentum import MomentumAudit
        item=arena_wheel.ASSEMBLIES['wheel_station'];coupling=item['coupling'];io=coupling.native_io
        momentum=MomentumAudit(io.view,item['metadata']['wrench_path'])
        report['native_mass_properties']=momentum.properties()
        report['reset_diagnostics']=list(arena_wheel.RESET_DIAGNOSTICS)
        stage=omni.usd.get_context().get_stage()
        from pxr import UsdPhysics,PhysxSchema
        scenes=[prim for prim in stage.Traverse() if prim.IsA(UsdPhysics.Scene)]
        if len(scenes)!=1:raise RuntimeError('Expected one native physics scene')
        phys=PhysxSchema.PhysxSceneAPI(scenes[0])
        report['effective_external_forces_every_iteration']=bool(phys.GetEnableExternalForcesEveryIterationAttr().Get())
        report['effective_solver_type']=str(phys.GetSolverTypeAttr().Get())
        if report['effective_solver_type']!=a.solver_type:raise RuntimeError('Requested native solver did not reach scene')
        expected_forces_every_iteration=a.central_spring_candidate and not a.external_forces_once_diagnostic and a.solver_type=='TGS'
        if report['effective_external_forces_every_iteration'] != expected_forces_every_iteration:
            raise RuntimeError('Requested external-force integration did not reach native scene')
        stage.GetRootLayer().Export(str(a.out/'initial.usda'))
        contact_audit=None
        if a.contact_audit_diagnostic:
            from contact_audit import FixedContactAudit
            contact_audit=FixedContactAudit(item['tensor_view'],stage,item['metadata'])
            report['fixed_contact_audit_filters']=contact_audit.filters
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
        tracker=None
        tool_servo=None
        if a.tool_pose_servo_diagnostic:
            from tool_pose_servo import ToolPoseServo
            tool_servo=ToolPoseServo(plan,nipple_feedback=a.nipple_target_servo_diagnostic)
            report['tool_pose_servo_disclosure']='State-assisted scripted demonstration reads native wrench pose and ordinary robot joints. Only standard speed/position/effort-limited joint targets are issued. Dream does not receive this observation or controller.'
        if a.joint_tracking_diagnostic:
            from joint_tracking import JointTracker
            tracker=JointTracker(ready,emb._low,emb._high,limit)
            report['joint_tracking_parameters']={'gain_per_s':tracker.gain,'maximum_offset_rad':tracker.offset_limit,
                'input':'Observed robot joints only; no object state or contact','actuator_efforts_changed':False}
        issued=ready.copy()
        observation=emb._observation()
        state=arena_wheel.state(emb._env,'wheel_station')
        report['phase']='simulate';save()
        trace = gzip.open(a.out/'trace.jsonl.gz', 'wt')
        video = imageio.get_writer(a.out/'preview.mp4', fps=20, codec='libx264', pixelformat='yuv420p',
                                  ffmpeg_params=['-movflags', '+faststart'], macro_block_size=1)
        for step in range(a.steps+1):
            if step:
                nominal=ready if actions is None else actions[step-1]
                target=nominal.copy()
                if tool_servo is not None:
                    spoke=tool_servo.target_spoke(step)
                    nipple_pose=None if spoke is None else state.body_poses[list(state.body_names).index(f'wheel/nipple_{spoke:02d}')]
                    target=tool_servo.command(step,target,np.asarray(observation.state['joint_pos']),state.body_poses[list(state.body_names).index('wrench')],nipple_pose)
                issued=target if tracker is None else tracker.command(target,np.asarray(observation.state['joint_pos']))
                command=torch.as_tensor(issued[None],device=base.device,dtype=torch.float32)
                tick=time.perf_counter();emb._env.step(command)
                report['control_step_wall_seconds'].append(time.perf_counter()-tick)
                emb._t=step/20
            report['completed_steps']=step
            observation = emb._observation()
            state = arena_wheel.state(emb._env, 'wheel_station')
            materials = arena_wheel.ASSEMBLIES['wheel_station']['coupling'].observation_for_assessor()
            native_transforms=io.view.get_transforms().detach().cpu().numpy().copy()
            trace.write(json.dumps({'step': step, 'time_s': step/20,
                'joint_pos': np.asarray(observation.state['joint_pos']).tolist(),
                'action14':issued.tolist(),
                'nominal_action14':(ready if step==0 or actions is None else actions[step-1]).tolist(),
                'joint_tracking':None if tracker is None else tracker.last,
                'tool_pose_servo':None if tool_servo is None else tool_servo.last,
                'stage':'ready' if step==0 or plan is None else plan['frames'][step-1]['stage'],
                'body_names': list(state.body_names), 'body_poses': state.body_poses.tolist(),
                'body_velocities': state.body_velocities.tolist(), 'materials': materials,
                'custom_torque_audit':getattr(coupling,'custom_torque_audit',None),
                'fixed_contacts':contact_audit.measure(1/a.physics_hz,np.array((.35,0.,1.005))) if contact_audit and step else None,
                'momentum':momentum.measure(native_transforms,np.array((.35,0.,1.005)))})+'\n')
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
