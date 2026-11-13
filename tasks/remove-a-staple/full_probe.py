"""Settle the full-size free-staple scene. No robot, fixture or task score."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import traceback
import numpy as np
from paper import ElasticDomainGuard
from contact_guard import PaperWireCrossingGuard
from full_scene import build_scene,PAPER_TOP,SHEET_CENTRES


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seconds',type=float,default=.5)
    p.add_argument('--physics-hz',type=int,choices=(2000,5000,10000),default=2000)
    a=p.parse_args()
    if not 0<a.seconds<=2:p.error('Diagnostic limited to two seconds')
    a.out.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    report={'kind':'full_size_free_staple_settling','status':'running','robot_demo':False,'score':None,
            'seconds':a.seconds,'physics_hz':a.physics_hz,'phase':'launch',
            'source_sha256':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                             for name in ('paper.py','full_scene.py','full_probe.py','native_paper.py','materials.py','physx_material.py','contact_guard.py')}}
    app=sim=stage=cache=None;attached=False
    try:
        from isaaclab.app import AppLauncher
        app=AppLauncher(headless=True,enable_cameras=False).app
        from pxr import Gf,Usd,UsdGeom,UsdPhysics,PhysxSchema,UsdUtils
        import omni.physics.tensors as tensors
        from omni.physx import get_physx_simulation_interface
        import carb
        from native_paper import update_staple,measured_wire_segments
        carb.settings.get_settings().set_bool('/physics/suppressReadback',True)
        carb.settings.get_settings().set_int('/physics/cudaDevice',0)
        cache=UsdUtils.StageCache.Get();stage=Usd.Stage.CreateInMemory();cache.Insert(stage)
        sid=cache.GetId(stage).ToLongInt();report['phase']='build'
        UsdGeom.SetStageMetersPerUnit(stage,1.);UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.z)
        ps=UsdPhysics.Scene.Define(stage,'/physicsScene');ps.CreateGravityDirectionAttr(Gf.Vec3f(0.,0.,-1.));ps.CreateGravityMagnitudeAttr(9.80665)
        api=PhysxSchema.PhysxSceneAPI.Apply(ps.GetPrim());api.CreateSolverTypeAttr('TGS');api.CreateEnableGPUDynamicsAttr(True);api.CreateBroadphaseTypeAttr('GPU');api.CreateEnableCCDAttr(False)
        metadata=build_scene(stage);meshes=metadata['paper_meshes'];staple=metadata['staple']
        guards=[ElasticDomainGuard(m) for m in meshes];crossing=[PaperWireCrossingGuard(m.faces) for m in meshes]
        report.update(meshes=[m.audit() for m in meshes],limitations=metadata['limitations'])
        stage.GetRootLayer().Export(str(a.out/'initial.usda'))
        report['phase']='attach';sim=get_physx_simulation_interface();sim.attach_stage(sid);attached=True
        native=tensors.create_simulation_view('torch',sid);native.set_subspace_roots('/')
        sheets=[native.create_surface_deformable_body_view(path) for path in metadata['paper_paths']]
        rigid=native.create_rigid_body_view(metadata['root']+'/*')
        class Physics:
            def refresh(self):self.frames=dict(zip(rigid.prim_paths,rigid.get_transforms().detach().cpu().numpy()))
            def get_rigidbody_transformation(self,path):
                r=self.frames.get(path)
                return {'ret_val':False} if r is None else {'ret_val':True,'position':r[:3],'rotation':r[3:]}
        physics=Physics();frames=[[],[]];samples=[];report['phase']='simulate'
        initial=[m.rest.mean(0)+np.array((xy[0],xy[1],PAPER_TOP-.00015+i*.0001)) for i,(m,xy) in enumerate(zip(meshes,SHEET_CENTRES))]
        final=None
        for step in range(1,round(a.seconds*a.physics_hz)+1):
            if step>1:update_staple(physics,staple)
            sim.simulate(1/a.physics_hz,(step-1)/a.physics_hz);sim.fetch_results();physics.refresh()
            wire=measured_wire_segments(physics,staple);measurements=[];final=[]
            for i,(view,mesh) in enumerate(zip(sheets,meshes)):
                nodes=view.get_simulation_nodal_positions().detach().cpu().numpy()[0,:len(mesh.rest)].copy()
                r=guards[i].update(nodes);r['contact_audit']=crossing[i].update(nodes,wire)
                r['valid']=r['valid'] and r['contact_audit']['valid'];measurements.append(r);final.append(nodes.mean(0))
                if step==1 or step%max(1,a.physics_hz//20)==0:frames[i].append(nodes)
            if step==1 or step%max(1,a.physics_hz//20)==0:samples.append({'step':step,'time_s':step/a.physics_hz,'paper':measurements,'remover_pose':physics.frames[metadata['remover_path']].tolist()})
            if any(not r['valid'] for r in measurements):
                report.update(status='invalid_model_domain',first_invalid_step=step);break
        np.savez_compressed(a.out/'state.npz',paper0=np.asarray(frames[0]),paper1=np.asarray(frames[1]),faces0=meshes[0].faces,faces1=meshes[1].faces)
        report.update(completed_steps=step,samples=samples,paper=[g.summary() for g in guards],
            contact_audit=[g.summary() for g in crossing],centroid_drop_m=[float(x[2]-y[2]) for x,y in zip(initial,final)])
        if report['status']=='running':report['status']='complete'
    except BaseException as error:
        report.update(status='failed',error=f'{type(error).__name__}: {error}',traceback=traceback.format_exc());raise
    finally:
        report['wall_seconds']=time.monotonic()-started
        (a.out/'full-probe.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        if attached:sim.detach_stage()
        if stage and cache:cache.Erase(stage)
        if app:app.close()


if __name__=='__main__':main()
