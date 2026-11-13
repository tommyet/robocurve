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
    p.add_argument('--lower-sheet-only-diagnostic',action='store_true',help='Keep only the lower sheet; requires the no-staple control')
    p.add_argument('--max-depenetration-m-s',type=float,help='Bound native numerical contact correction speed; diagnostic only')
    p.add_argument('--staple-velocity-iterations',type=int,choices=(4,32),default=32,help='Native rigid solver diagnostic; unchanged physical mass/material')
    p.add_argument('--staple-max-depenetration-m-s',type=float,help='Separate correction cap on the native wire bodies; diagnostic only')
    p.add_argument('--observe-strain-diagnostic',action='store_true',help='Record beyond elastic-domain failure up to1% membrane strain; never a task validity claim')
    p.add_argument('--surface-iterations',type=int,choices=(64,128,255),default=64)
    p.add_argument('--mesh-profile',choices=('baseline','coarse'),default='baseline')
    p.add_argument('--self-filter-distance-um',type=float,help='Explicit native rest-neighbor self-collision filter, diagnostic only')
    p.add_argument('--reset-profile',choices=RESET_PROFILES,default='floating-reference')
    p.add_argument('--refined-contact-diagnostic',action='store_true',help='Native speculative CCD and4x contact/pair updates; material/mesh unchanged')
    p.add_argument('--fixed-crown-diagnostic',action='store_true',help='Explicit diagnostic fixture; not available in the task')
    p.add_argument('--remove-staple-diagnostic',action='store_true',help='Remove the staple before physics to isolate full-paper solver/contact behavior; never task evidence')
    a=p.parse_args()
    if not 0<a.seconds<=2:p.error('Diagnostic limited to two seconds')
    if a.fixed_crown_diagnostic and a.remove_staple_diagnostic:p.error('Cannot fix a removed staple')
    if a.lower_sheet_only_diagnostic and not a.remove_staple_diagnostic:p.error('Single-sheet isolation requires --remove-staple-diagnostic')
    if a.max_depenetration_m_s is not None and not .01<=a.max_depenetration_m_s<=1.:p.error('Contact correction speed must be .01–1m/s')
    if a.staple_max_depenetration_m_s is not None and not .01<=a.staple_max_depenetration_m_s<=1.:p.error('Wire correction speed must be .01–1m/s')
    if a.self_filter_distance_um is not None and not 100<=a.self_filter_distance_um<=1000:
        p.error('Self-neighbor diagnostic distance must be100–1000µm')
    a.out.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    report={'kind':'full_size_free_staple_settling','status':'running','robot_demo':False,'score':None,
            'seconds':a.seconds,'physics_hz':a.physics_hz,'phase':'launch',
            'observe_bending_diagnostic':a.observe_bending_diagnostic,
            'staple_removed_diagnostic':a.remove_staple_diagnostic,
            'fixed_crown_diagnostic':a.fixed_crown_diagnostic,
            'staple_velocity_iterations':a.staple_velocity_iterations,
            'refined_contact_diagnostic':a.refined_contact_diagnostic,
            'reset_profile':a.reset_profile,
            'self_filter_distance_um':a.self_filter_distance_um,'surface_iterations':a.surface_iterations,'mesh_profile':a.mesh_profile,
            'lower_sheet_only_diagnostic':a.lower_sheet_only_diagnostic,
            'max_depenetration_m_s':a.max_depenetration_m_s,
            'staple_max_depenetration_m_s':a.staple_max_depenetration_m_s,
            'observe_strain_diagnostic':a.observe_strain_diagnostic,
            'membrane_diagnostic_stop_strain':.01 if a.observe_strain_diagnostic else .003,
            'source_sha256':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                             for name in ('paper.py','full_scene.py','full_probe.py','native_paper.py','materials.py','physx_material.py','contact_guard.py')},
            'asset_sha256':{str(path.relative_to(Path(__file__).with_name('assets'))):hashlib.sha256(path.read_bytes()).hexdigest()
                            for path in sorted(Path(__file__).with_name('assets').rglob('*')) if path.is_file()}}
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
        metadata=build_scene(stage,reset_profile=a.reset_profile,mesh_profile=a.mesh_profile,fixed_crown_diagnostic=a.fixed_crown_diagnostic);meshes=metadata['paper_meshes'];staple=metadata['staple']
        if a.remove_staple_diagnostic:
            stage.RemovePrim(metadata['root']+'/staple');staple=None
            report['kind']='full_size_paper_without_staple_diagnostic'
        if staple:
            for path in staple['paths']:
                PhysxSchema.PhysxRigidBodyAPI.Get(stage,path).CreateSolverVelocityIterationCountAttr(a.staple_velocity_iterations)
        if staple and a.staple_max_depenetration_m_s is not None:
            for path in staple['paths']:
                PhysxSchema.PhysxRigidBodyAPI.Get(stage,path).CreateMaxDepenetrationVelocityAttr(a.staple_max_depenetration_m_s)
        if a.lower_sheet_only_diagnostic:
            stage.RemovePrim(metadata['paper_paths'][1])
            metadata['paper_paths']=metadata['paper_paths'][:1];meshes=meshes[:1]
            report['kind']='full_size_single_lower_paper_diagnostic'
        report['paper_count']=len(meshes)
        for path in metadata['paper_paths']:
            attr=stage.GetPrimAtPath(path).GetAttribute('physxDeformableBody:solverPositionIterationCount')
            if not attr or not attr.Set(a.surface_iterations):raise RuntimeError('Native surface iteration control unavailable')
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
        if a.self_filter_distance_um is not None:
            for path in metadata['paper_paths']:
                attr=stage.GetPrimAtPath(path).GetAttribute('physxDeformableBody:selfCollisionFilterDistance')
                if not attr or not attr.Set(a.self_filter_distance_um*1e-6):
                    raise RuntimeError('Native rest-neighbor self-collision filter unavailable')
        if a.max_depenetration_m_s is not None:
            for path in metadata['paper_paths']:
                attr=stage.GetPrimAtPath(path).GetAttribute('physxDeformableBody:maxDepenetrationVelocity')
                if not attr or not attr.Set(a.max_depenetration_m_s):
                    raise RuntimeError('Native maximum depenetration velocity unavailable')
        report['native_surface_contact']=[{name:stage.GetPrimAtPath(path).GetAttribute(name).Get()
            for name in ('physxCollision:restOffset','physxCollision:contactOffset',
                'physxDeformableBody:selfCollisionFilterDistance','physxDeformableBody:maxDepenetrationVelocity',
                'physxDeformableBody:enableSpeculativeCCD','physxDeformableBody:collisionIterationMultiplier',
                'physxDeformableBody:collisionPairUpdateFrequency')} for path in metadata['paper_paths']]
        # USD defaults may be infinite; preserve them as explicit strings inJSON.
        for row in report['native_surface_contact']:
            for key,value in row.items():
                if isinstance(value,float) and not np.isfinite(value):row[key]=str(value)
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
        physics=Physics();frames=[[] for _ in meshes];samples=[];report['phase']='simulate'
        def save_nodes(path,nodes,wire):
            fields={'wire_segments':wire}
            for i,(points,mesh) in enumerate(zip(nodes,meshes)):
                fields.update({f'paper{i}':points,f'faces{i}':mesh.faces,f'rest{i}':mesh.rest})
            np.savez_compressed(path,**fields)
        sample_stride=max(1,a.physics_hz//2000)
        frame_stride=max(1,a.physics_hz//1000)
        initial=[m.rest.mean(0)+np.array((xy[0],xy[1],metadata['reset_layout']['paper_centres_z'][i])) for i,(m,xy) in enumerate(zip(meshes,SHEET_CENTRES))]
        final=None
        for step in range(1,round(a.seconds*a.physics_hz)+1):
            if step>1 and staple:update_staple(physics,staple)
            sim.simulate(1/a.physics_hz,(step-1)/a.physics_hz);sim.fetch_results();physics.refresh()
            if step==1:
                masses=rigid.get_masses().detach().cpu().numpy().reshape(-1)
                inertias=rigid.get_inertias().detach().cpu().numpy().reshape(-1,3,3)
                report['native_mass_properties']=[{'path':str(path),'mass_kg':float(m),'inertia_body_kg_m2':I.tolist()} for path,m,I in zip(rigid.prim_paths,masses,inertias)]
                if staple:
                    from materials import SteelSpec
                    steel=SteelSpec();expected={path:7850*L*steel.wire_width_m*steel.wire_thickness_m for path,L in zip(staple['paths'],staple['lengths_m'])}
                    report['wire_mass_expected_kg']=expected
                    report['maximum_wire_mass_relative_error']=max(abs(float(m)-expected[str(path)])/expected[str(path)] for path,m in zip(rigid.prim_paths,masses) if str(path) in expected)
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
                if step==1 or step%frame_stride==0:frames[i].append(nodes)
            if step==1 or step%sample_stride==0:
                velocities=rigid.get_velocities().detach().cpu().numpy()
                wire_indices=[j for j,path in enumerate(rigid.prim_paths) if staple and path in staple['paths']]
                wire_speed=float(np.linalg.norm(velocities[wire_indices,:3],axis=1).max()) if wire_indices else 0.
                samples.append({'step':step,'time_s':step/a.physics_hz,'paper':measurements,
                    'maximum_wire_speed_m_s':wire_speed,'wire_segments':wire.tolist(),
                    'remover_pose':physics.frames[metadata['remover_path']].tolist()})
            invalid=any(not r['valid'] for r in measurements)
            if invalid and 'first_invalid_step' not in report:
                report.update(status='invalid_model_domain',first_invalid_step=step,first_invalid_measurements=measurements)
                save_nodes(a.out/'first-invalid-state.npz',step_nodes,wire)
            must_stop=invalid
            if a.observe_bending_diagnostic or a.observe_strain_diagnostic:
                limit=.01 if a.observe_strain_diagnostic else .003
                must_stop=any((r['maximum_tensile_strain']>limit or
                    not r['contact_audit']['valid']) for r,g in zip(measurements,guards))
            if must_stop:
                report['stop_measurements']=measurements
                save_nodes(a.out/'stop-state.npz',step_nodes,wire)
                break
        save_nodes(a.out/'state.npz',[np.asarray(f) for f in frames],wire)
        report.update(completed_steps=step,samples=samples,paper=[g.summary() for g in guards],
            contact_audit=[g.summary() for g in crossing],centroid_drop_m=[float(x[2]-y[2]) for x,y in zip(initial,final)])
        if report['status']=='running':report['status']='complete'
        elif (a.observe_bending_diagnostic or a.observe_strain_diagnostic) and step==round(a.seconds*a.physics_hz):
            report['status']='complete_outside_elastic_domain_diagnostic_only'
    except BaseException as error:
        report.update(status='failed',error=f'{type(error).__name__}: {error}',traceback=traceback.format_exc());raise
    finally:
        report['wall_seconds']=time.monotonic()-started
        (a.out/'full-probe.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        if attached:sim.detach_stage()
        if stage and cache:cache.Erase(stage)
        if app:app.close()


if __name__=='__main__':main()
