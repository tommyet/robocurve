"""Bounded native YAM camera/physics integration preview, never a task demo."""
import argparse
import gzip
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import time
import traceback
import numpy as np


def native_audit(stage):
    from pxr import UsdPhysics
    from arena_hardware import BODY_NAMES
    papers={};bodies=[];attachments=[];fixed_staple=[]
    for prim in stage.Traverse():
        path=str(prim.GetPath());schemas=prim.GetAppliedSchemas()
        if any('Attachment' in s for s in schemas) or 'Attachment' in prim.GetTypeName():attachments.append(path)
        if path.endswith(('/paper_0','/paper_1')):
            papers[path]={'schemas':list(schemas),'rigid':prim.HasAPI(UsdPhysics.RigidBodyAPI),
                          'self_collision':prim.GetAttribute('physxDeformableBody:selfCollision').Get()}
        if '/hardware/' in path and prim.HasAPI(UsdPhysics.RigidBodyAPI):
            if UsdPhysics.RigidBodyAPI(prim).GetKinematicEnabledAttr().Get():raise RuntimeError('Task hardware must be dynamic: '+path)
            bodies.append(path)
        if '/hardware/staple/' in path and prim.IsA(UsdPhysics.Joint):
            b0=prim.GetRelationship('physics:body0').GetTargets();b1=prim.GetRelationship('physics:body1').GetTargets()
            if not b0 or not b1:fixed_staple.append(path)
    if len(papers)!=2 or any(p['rigid'] or 'OmniPhysicsSurfaceDeformableSimAPI' not in p['schemas'] or p['self_collision'] is not True for p in papers.values()):raise RuntimeError('Missing genuine native paper')
    if len(bodies)!=len(BODY_NAMES) or attachments or fixed_staple:raise RuntimeError('Unexpected hardware count, attachment or fixed staple')
    return {'paper':papers,'dynamic_hardware_bodies':len(bodies),'attachments':attachments,'fixed_staple':fixed_staple}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--steps',type=int,default=10)
    p.add_argument('--physics-hz',type=int,choices=(2000,5000,10000),default=2000)
    a=p.parse_args()
    if not 1<=a.steps<=100:p.error('Integration preview limited to100 control steps')
    if not version('isaacsim').startswith('6.1.'):raise RuntimeError('Use the pinned Isaac6.1 environment')
    a.out.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    report={'kind':'staple_yam_integration_preview','status':'running','score':None,'robot_demo':False,
        'dream_requests':0,'requested_steps':a.steps,'control_hz':20,'phase':'launch',
        'policy':'ordinary constant ready-joint targets; no object state feedback',
        'source_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in Path(__file__).parent.glob('*.py')}}
    app=video=trace=None;monitors=[]
    try:
        from isaaclab.app import AppLauncher
        app=AppLauncher(headless=True,enable_cameras=True).app
        import imageio.v2 as imageio
        from PIL import Image
        import omni.usd
        import arena_paper,arena_hardware
        from yam_arena import inspect_embodiment as wrapper,scene as adapter
        wrapper._APP=app;report['phase']='build'
        emb=wrapper.YamArenaEmbodiment(task=str(Path(__file__).with_name('task.py')),object_jitter=0.,control_hz=20,cam_width=224,cam_height=224)
        original_dt=adapter.PHYSICS_DT;adapter.PHYSICS_DT=1/a.physics_hz
        try:emb._ensure_sim(None)
        finally:adapter.PHYSICS_DT=original_dt
        base=emb._base;stage=omni.usd.get_context().get_stage()
        report['phase']='reset';emb._env.reset()
        report['native_audit']=native_audit(stage)
        arena_hardware.install_material_hook(base,stage)
        monitors=[x['monitor'] for x in arena_hardware.ASSEMBLIES.values()]
        report['physics_dt_s']=float(base.sim.get_physics_dt())
        trace=gzip.open(a.out/'trace.jsonl.gz','wt')
        video=imageio.get_writer(a.out/'preview.mp4',fps=20,codec='libx264',pixelformat='yuv420p',ffmpeg_params=['-movflags','+faststart'],macro_block_size=1)
        report['phase']='record'
        for step in range(a.steps+1):
            if step:emb._env.step(emb._ready)
            # Observe every final substep too; the material callback inspects
            # preceding states before all intermediate native substeps.
            for monitor in monitors:monitor.inspect(update_material=False)
            observation=emb._observation()
            paper=[arena_paper.state(emb._env,'paper_'+str(i)) for i in range(2)]
            hardware=arena_hardware.hardware_state(emb._env,'hardware')
            trace.write(json.dumps({'step':step,'time_s':step/20,'joint_pos':np.asarray(observation.state['joint_pos']).tolist(),
                'paper_nodes':[x.nodes.tolist() for x in paper],'hardware_names':list(hardware.body_names),
                'hardware_poses':hardware.body_poses.tolist(),'material':[m.last for m in monitors]})+'\n')
            rgb=base.scene['top_cam'].data.output['rgb'];rgb=getattr(rgb,'torch',rgb)
            frame=rgb.detach().cpu().numpy()[0,:,:,:3].astype(np.uint8);video.append_data(frame)
            if step in (0,a.steps):Image.fromarray(frame).save(a.out/('setup.png' if not step else 'final.png'))
            report['completed_steps']=step
        report.update(status='complete',meaning='Unscored integration only; no successful extraction demonstrated')
    except BaseException as error:
        report.update(status='invalid_model_domain' if type(error).__name__=='MaterialDomainError' else 'failed',
            error=f'{type(error).__name__}: {error}',traceback=traceback.format_exc(),material=[m.last for m in monitors]);raise
    finally:
        if trace:trace.close()
        if video:video.close()
        report['wall_seconds']=time.monotonic()-started
        (a.out/'preview.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        if app:app.close()


if __name__=='__main__':main()
