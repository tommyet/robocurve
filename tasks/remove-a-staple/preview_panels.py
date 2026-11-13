"""Bounded native YAM panel-paper preview; no task success claim."""
import argparse
import gzip
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import time
import traceback
import signal
import numpy as np


def native_audit(stage):
    from pxr import UsdPhysics
    from arena_hardware import BODY_NAMES
    from arena_panels import SHELLS
    attachments=[];fixed=[];hardware=[];papers={}
    for prim in stage.Traverse():
        path=str(prim.GetPath());schemas=prim.GetAppliedSchemas()
        if any('Attachment' in x for x in schemas) or 'Attachment' in prim.GetTypeName():attachments.append(path)
        if '/hardware/' in path and prim.HasAPI(UsdPhysics.RigidBodyAPI):
            if UsdPhysics.RigidBodyAPI(prim).GetKinematicEnabledAttr().Get():raise RuntimeError('Kinematic hardware')
            hardware.append(path)
        if '/hardware/staple/' in path and prim.IsA(UsdPhysics.Joint):
            if not prim.GetRelationship('physics:body0').GetTargets() or not prim.GetRelationship('physics:body1').GetTargets():fixed.append(path)
    for name,shell in SHELLS.items():
        for path in shell['bodies']:
            prim=stage.GetPrimAtPath(path);shape=stage.GetPrimAtPath(path+'/Shape')
            if not prim.HasAPI(UsdPhysics.RigidBodyAPI) or UsdPhysics.RigidBodyAPI(prim).GetKinematicEnabledAttr().Get():raise RuntimeError('Paper panel must be free/dynamic')
            if shape.GetTypeName()!='Cube' or abs(shape.GetAttribute('xformOp:scale').Get()[2]-.0001)>1e-10:raise RuntimeError('Paper panel must be100um analytic box')
        for path in shell['joints']:
            prim=stage.GetPrimAtPath(path)
            if not prim.GetRelationship('physics:body0').GetTargets() or not prim.GetRelationship('physics:body1').GetTargets():fixed.append(path)
        papers[name]={'dynamic_panels':len(shell['bodies']),'passive_hinges':len(shell['joints']),
                      'surface_area_m2':shell['mesh'].audit()['surface_area_m2']}
    if len(papers)!=2 or len(hardware)!=len(BODY_NAMES) or attachments or fixed:raise RuntimeError('Incomplete native paper or hidden attachment')
    return dict(paper=papers,dynamic_hardware_bodies=len(hardware),attachments=attachments,fixed_material_joints=fixed)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--steps',type=int,default=10)
    p.add_argument('--physics-hz',type=int,choices=(2000,5000,10000),default=10000)
    p.add_argument('--plan',type=Path)
    p.add_argument('--recenter-at-paper',action='store_true',help='Fixed global origin shift including robot bases and fixed cameras before construction')
    p.add_argument('--reset-profile',choices=('pocket-support-candidate',),default='pocket-support-candidate')
    p.add_argument('--mesh-profile',choices=('clearance-candidate',),default='clearance-candidate')
    p.add_argument('--refined-contact-diagnostic',action='store_true')
    p.add_argument('--max-depenetration-m-s',type=float)
    a=p.parse_args()
    if not 1<=a.steps<=(2400 if a.plan else 100):p.error('Bounded preview step count exceeded')
    import runtime_config
    import coordinate_frame
    coordinate_frame.configure(a.recenter_at_paper)
    runtime_config.configure(a.reset_profile,a.mesh_profile,a.refined_contact_diagnostic,a.max_depenetration_m_s)
    plan=actions=None
    if a.plan:
        from motion_plan import load
        from yam_arena import YAM_URDF
        plan,actions=load(a.plan)
        if a.steps>len(actions):p.error('Requested steps exceed plan')
        if plan['reset_profile']!=a.reset_profile or plan['mesh_profile']!=a.mesh_profile:p.error('Plan and native reset must match')
        if hashlib.sha256(Path(YAM_URDF).read_bytes()).hexdigest()!=plan['urdf_sha256']:raise RuntimeError('Plan URDF mismatch')
        for name,digest in plan['source_sha256'].items():
            if hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()!=digest:raise RuntimeError('Stale plan source: '+name)
    if not version('isaacsim').startswith('6.1.'):raise RuntimeError('Use the pinned Isaac6.1 environment')
    a.out.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    report={'kind':'staple_panel_yam_integration_preview','status':'running','score':None,'robot_demo':False,
        'dream_requests':0,'requested_steps':a.steps,'control_hz':20,'phase':'launch',
        'policy':'ordinary fixed joint commands; no object state feedback',
        'paper_model':'native analytic100um box panels with passive bending/strength hinges',
        'world_coordinate_offset_m':coordinate_frame.OFFSET_M.tolist(),
        'plan_sha256':hashlib.sha256(a.plan.read_bytes()).hexdigest() if a.plan else None,
        'reset_profile':a.reset_profile,'mesh_profile':a.mesh_profile,
        'refined_contact':a.refined_contact_diagnostic,'max_depenetration_m_s':a.max_depenetration_m_s,
        'source_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in Path(__file__).parent.glob('*.py')}}
    def checkpoint():
        report['wall_seconds']=time.monotonic()-started
        temporary=a.out/'preview.tmp.json';temporary.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');temporary.replace(a.out/'preview.json')
    def terminated(signum,frame):raise TimeoutError('Preview stopped by external watchdog')
    signal.signal(signal.SIGTERM,terminated);checkpoint()
    app=video=trace=None;monitors=[]
    try:
        from isaaclab.app import AppLauncher
        app=AppLauncher(headless=True,enable_cameras=True,device='cpu').app
        import imageio.v2 as imageio
        import torch
        from PIL import Image
        import omni.usd
        import arena_panels,arena_hardware
        arena_hardware.PANEL_CONTACT_CANDIDATE=True
        from yam_arena import inspect_embodiment as wrapper,scene as adapter
        wrapper._APP=app;report['phase']='build'
        emb=wrapper.YamArenaEmbodiment(task=str(Path(__file__).with_name('task_panels.py')),object_jitter=0.,control_hz=20,cam_width=224,cam_height=224,device='cpu')
        original_dt=adapter.PHYSICS_DT;adapter.PHYSICS_DT=1/a.physics_hz
        original_configuration=adapter.env_cfg_callback
        def configure_callback(*args,**kwargs):
            configure=original_configuration(*args,**kwargs)
            def override(cfg):
                cfg=coordinate_frame.shift_scene_config(configure(cfg))
                from isaaclab_physx.physics import PhysxCfg
                if cfg.sim.physics is None:cfg.sim.physics=PhysxCfg()
                cfg.sim.physics.solver_type=1
                cfg.sim.physics.enable_ccd=True
                cfg.sim.physics.enable_external_forces_every_iteration=True
                return cfg
            return override
        adapter.env_cfg_callback=configure_callback
        try:emb._ensure_sim(None)
        finally:
            adapter.PHYSICS_DT=original_dt
            adapter.env_cfg_callback=original_configuration
        report['coordinate_configuration_audit']=list(coordinate_frame.CONFIG_AUDIT)
        base=emb._base;stage=omni.usd.get_context().get_stage()
        report['phase']='reset';emb._env.reset()
        report['native_audit']=native_audit(stage)
        arena_panels.install_material_hook(base,stage)
        monitors=[x['monitor'] for x in arena_hardware.ASSEMBLIES.values()]
        report['physics_dt_s']=float(base.sim.get_physics_dt())
        report['effective_device']=str(base.device)
        if report['effective_device']!='cpu':raise RuntimeError('Expected CPU native panel dynamics')
        from pxr import UsdPhysics,PhysxSchema
        scenes=[prim for prim in stage.Traverse() if prim.IsA(UsdPhysics.Scene)]
        if len(scenes)!=1:raise RuntimeError('Expected one native physics scene')
        phys=PhysxSchema.PhysxSceneAPI(scenes[0])
        report['native_physics']={'solver_type':str(phys.GetSolverTypeAttr().Get()),
            'gpu':bool(phys.GetEnableGPUDynamicsAttr().Get()),'ccd':bool(phys.GetEnableCCDAttr().Get()),
            'external_forces_every_iteration':bool(phys.GetEnableExternalForcesEveryIterationAttr().Get())}
        if report['native_physics']!={'solver_type':'TGS','gpu':False,'ccd':True,'external_forces_every_iteration':True}:
            raise RuntimeError('Native settings differ from the passing panel-paper control')
        stage.GetRootLayer().Export(str(a.out/'initial.usda'))
        trace=gzip.open(a.out/'trace.jsonl.gz','wt')
        video=imageio.get_writer(a.out/'preview.mp4',fps=20,codec='libx264',pixelformat='yuv420p',ffmpeg_params=['-movflags','+faststart'],macro_block_size=1)
        report['phase']='record'
        for step in range(a.steps+1):
            if step:
                action=emb._ready if actions is None else torch.as_tensor(actions[step-1][None],device=base.device,dtype=torch.float32)
                emb._env.step(action)
            # Observe every final substep too; the material callback inspects
            # preceding states before all intermediate native substeps.
            for monitor in monitors:monitor.inspect(update_material=False)
            observation=emb._observation()
            paper=[arena_panels.state(emb._env,'paper_'+str(i)) for i in range(2)]
            hardware=arena_hardware.hardware_state(emb._env,'hardware')
            trace.write(json.dumps({'step':step,'time_s':step/20,'joint_pos':np.asarray(observation.state['joint_pos']).tolist(),
                'commanded_action14':None if step==0 or actions is None else actions[step-1].tolist(),
                'paper_nodes':[x.nodes.tolist() for x in paper],
                'paper_continuity':[x.continuity for x in paper],'hardware_names':list(hardware.body_names),
                'hardware_poses':hardware.body_poses.tolist(),'material':[m.last for m in monitors]})+'\n')
            rgb=base.scene['top_cam'].data.output['rgb'];rgb=getattr(rgb,'torch',rgb)
            frame=rgb.detach().cpu().numpy()[0,:,:,:3].astype(np.uint8);video.append_data(frame)
            if step in (0,a.steps):Image.fromarray(frame).save(a.out/('setup.png' if not step else 'final.png'))
            report['completed_steps']=step
            if step%5==0:trace.flush();checkpoint()
        report.update(status='complete',meaning='Unscored integration only; no successful extraction demonstrated')
    except BaseException as error:
        report.update(status='invalid_model_domain' if type(error).__name__=='MaterialDomainError' else 'failed',
            error=f'{type(error).__name__}: {error}',traceback=traceback.format_exc(),material=[m.last for m in monitors]);raise
    finally:
        if trace:trace.close()
        if video:video.close()
        report['wall_seconds']=time.monotonic()-started
        checkpoint()
        if app:app.close()


if __name__=='__main__':main()
