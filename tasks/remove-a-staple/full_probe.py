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
from full_scene import build_scene,RESET_PROFILES,SHEET_CENTRES


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seconds',type=float,default=.5)
    p.add_argument('--physics-hz',type=int,choices=(2000,5000,10000),default=2000)
    p.add_argument('--observe-bending-diagnostic',action='store_true',help='Keep recording after bending boundary; still stop for tensile/crossing failures, no task validity claim')
    p.add_argument('--reset-profile',choices=RESET_PROFILES,default='floating-reference')
    p.add_argument('--refined-contact-diagnostic',action='store_true',help='Native speculative CCD and4x contact/pair updates; material/mesh unchanged')
    p.add_argument('--remove-staple-diagnostic',action='store_true',help='Remove the staple before physics to isolate full-paper solver/contact behavior; never task evidence')
    a=p.parse_args()
    if not 0<a.seconds<=2:p.error('Diagnostic limited to two seconds')
    a.out.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    report={'kind':'full_size_free_staple_settling','status':'running','robot_demo':False,'score':None,
            'seconds':a.seconds,'physics_hz':a.physics_hz,'phase':'launch',
            'observe_bending_diagnostic':a.observe_bending_diagnostic,
            'staple_removed_diagnostic':a.remove_staple_diagnostic,
            'refined_contact_diagnostic':a.refined_contact_diagnostic,
            'reset_profile':a.reset_profile,
            'source_sha256':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                             for name in ('paper.py','full_scene.py','full_probe.py','native_paper.py','materials.py','physx_material.py','contact_guard.py')},
            'asset_sha256':{path.name:hashlib.sha256(path.read_bytes()).hexdigest()
                            for path in sorted(Path(__file__).with_name('assets').glob('*')) if path.is_file()}}
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
        metadata=build_scene(stage,reset_profile=a.reset_profile);meshes=metadata['paper_meshes'];staple=metadata['staple']
        if a.remove_staple_diagnostic:
            stage.RemovePrim(metadata['root']+'/staple');staple=None
            report['kind']='full_size_paper_without_staple_diagnostic'
        if a.refined_contact_diagnostic:
            attributes={'physxDeformableBody:enableSpeculativeCCD':True,
                        'physxDeformableBody:collisionIterationMultiplier':4,
                        'physxDeformableBody:collisionPairUpdateFrequency':4}
            for path in metadata['paper_paths']:
                prim=stage.GetPrimAtPath(path)
                for name,value in attributes.items():
                    attr=prim.GetAttribute(name)
                    if not attr or not attr.Set(value):
                        raise RuntimeError('Native surface contact control unavailable: '+name)
            report['native_contact_overrides']=attributes
        guards=[ElasticDomainGuard(m) for m in meshes];crossing=[PaperWireCrossingGuard(m.faces) for m in meshes]
        report.update(meshes=[m.audit() for m in meshes],limitations=metadata['limitations'],
            initial_sheet_midplane_gap_m=metadata['initial_sheet_midplane_gap_m'],
            initial_crown_clearance_m=metadata['initial_crown_clearance_m'],reset_layout=metadata['reset_layout'])
        stage.GetRootLayer().Export(str(a.out/'initial.usda'))
        report['phase']='attach';sim=get_physx_simulation_interface();sim.attach_stage(sid);attached=True
        native=tensors.create_simulation_view('torch',sid);native.set_subspace_roots('/')
        sheets=[native.create_surface_deformable_body_view(path) for path in metadata['paper_paths']]
        rigid_paths=(staple['paths'] if staple else [])+[metadata['remover_path']]
        rigid=native.create_rigid_body_view(rigid_paths)
        report['native_hardware_bodies']=rigid.count
        if rigid.count!=len(rigid_paths):raise RuntimeError('Incomplete native staple/remover collection')
        class Physics:
            def refresh(self):self.frames=dict(zip(rigid.prim_paths,rigid.get_transforms().detach().cpu().numpy()))
            def get_rigidbody_transformation(self,path):
                r=self.frames.get(path)
                return {'ret_val':False} if r is None else {'ret_val':True,'position':r[:3],'rotation':r[3:]}
        physics=Physics();frames=[[],[]];samples=[];report['phase']='simulate'
        initial=[m.rest.mean(0)+np.array((xy[0],xy[1],metadata['reset_layout']['paper_centres_z'][i])) for i,(m,xy) in enumerate(zip(meshes,SHEET_CENTRES))]
        final=None
        for step in range(1,round(a.seconds*a.physics_hz)+1):
            if step>1 and staple:update_staple(physics,staple)
            sim.simulate(1/a.physics_hz,(step-1)/a.physics_hz);sim.fetch_results();physics.refresh()
            wire=measured_wire_segments(physics,staple) if staple else np.empty((0,2,3))
            measurements=[];final=[];step_nodes=[]
            for i,(view,mesh) in enumerate(zip(sheets,meshes)):
                nodes=view.get_simulation_nodal_positions().detach().cpu().numpy()[0,:len(mesh.rest)].copy()
                step_nodes.append(nodes)
                r=guards[i].update(nodes)
                r['contact_audit']=crossing[i].update(nodes,wire) if staple else {'valid':True,'diagnostic':'No staple exists in this diagnostic'}
                r['valid']=r['valid'] and r['contact_audit']['valid']
                r['centroid_m']=nodes.astype(float).mean(0).tolist();r['z_span_m']=float(np.ptp(nodes[:,2]))
                measurements.append(r);final.append(nodes.astype(float).mean(0))
                if step==1 or step%max(1,a.physics_hz//20)==0:frames[i].append(nodes)
            if step==1 or step%max(1,a.physics_hz//20)==0:samples.append({'step':step,'time_s':step/a.physics_hz,'paper':measurements,'remover_pose':physics.frames[metadata['remover_path']].tolist()})
            invalid=any(not r['valid'] for r in measurements)
            if invalid and 'first_invalid_step' not in report:
                report.update(status='invalid_model_domain',first_invalid_step=step,first_invalid_measurements=measurements)
                np.savez_compressed(a.out/'first-invalid-state.npz',paper0=step_nodes[0],paper1=step_nodes[1],
                    faces0=meshes[0].faces,faces1=meshes[1].faces,rest0=meshes[0].rest,rest1=meshes[1].rest,
                    wire_segments=wire)
            must_stop=invalid
            if a.observe_bending_diagnostic:
                must_stop=any((r['maximum_tensile_strain']>g.material.max_tensile_strain or
                    not r['contact_audit']['valid']) for r,g in zip(measurements,guards))
            if must_stop:
                report['stop_measurements']=measurements
                np.savez_compressed(a.out/'stop-state.npz',paper0=step_nodes[0],paper1=step_nodes[1],
                    faces0=meshes[0].faces,faces1=meshes[1].faces,rest0=meshes[0].rest,rest1=meshes[1].rest,
                    wire_segments=wire)
                break
        np.savez_compressed(a.out/'state.npz',paper0=np.asarray(frames[0]),paper1=np.asarray(frames[1]),faces0=meshes[0].faces,faces1=meshes[1].faces,
            rest0=meshes[0].rest,rest1=meshes[1].rest)
        report.update(completed_steps=step,samples=samples,paper=[g.summary() for g in guards],
            contact_audit=[g.summary() for g in crossing],centroid_drop_m=[float(x[2]-y[2]) for x,y in zip(initial,final)])
        if report['status']=='running':report['status']='complete'
        elif a.observe_bending_diagnostic and step==round(a.seconds*a.physics_hz):
            report['status']='complete_outside_elastic_bending_domain_diagnostic_only'
    except BaseException as error:
        report.update(status='failed',error=f'{type(error).__name__}: {error}',traceback=traceback.format_exc());raise
    finally:
        report['wall_seconds']=time.monotonic()-started
        (a.out/'full-probe.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        if attached:sim.detach_stage()
        if stage and cache:cache.Erase(stage)
        if app:app.close()


if __name__=='__main__':main()
