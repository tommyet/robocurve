"""Unscored single-loop free-fall diagnostic, with no cloth or fixture.

This isolates closed-chain constraints, native mass properties and self-contact.
The optional contact exclusion is a diagnostic only, never a task setting.
Root owns native launches; no score or feasibility result is produced here.
"""
import argparse
import hashlib
import json
from pathlib import Path
import signal
import time
import traceback
import numpy as np


def array(value):
    return getattr(value,'torch',value).detach().cpu().numpy().copy()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--joint-kind',choices=('spherical','d6'),default='spherical')
    p.add_argument('--ccd',choices=('none','sweep','hybrid'),default='sweep')
    p.add_argument('--self-contact',choices=('normal','none'),default='normal')
    p.add_argument('--clear-thread-sampling',action='store_true',help='Same centreline and diameter with24links; no non-neighbour tangent capsules at reset')
    p.add_argument('--physics-hz',type=int,choices=(960,3840),default=960)
    p.add_argument('--velocity-iterations',type=int,choices=(1,4,32),default=1)
    p.add_argument('--solver',choices=('TGS','PGS'),default='TGS',help='Native CPU contact-solver comparison; geometry and material unchanged')
    p.add_argument('--passive-bending',action='store_true',help='Disclosed B=1.2e-9 N m2 passive straight-rest D6 swing springs; no task-aware force')
    p.add_argument('--loop-shape',choices=('rectangle','circle'),default='rectangle',help='Free-loop diagnostic only; circle preserves each segment length and mass')
    p.add_argument('--cut-after-s',type=float,help='Unscored cut-end energy diagnostic: disable joint0 at this time, with the existing collision-restoration behavior')
    p.add_argument('--defer-cut-contact',action='store_true',help='Retain only the former adjoining pair exclusion until actual finite capsules separate')
    p.add_argument('--seconds',type=float,default=.05)
    a=p.parse_args()
    if not .01<=a.seconds<=.2:p.error('Single-loop isolation is bounded to0.01–0.2s')
    if a.passive_bending and (a.joint_kind!='d6' or a.self_contact!='normal'):
        p.error('Passive bending control requires D6 joints and every ordinary self-contact')
    if a.loop_shape!='rectangle' and not a.passive_bending:p.error('Cyclic equilibrium control requires passive bending')
    if a.cut_after_s is not None and (not .01<=a.cut_after_s<=a.seconds-.01 or a.self_contact!='normal'):
        p.error('Cut diagnostic requires normal contacts and at least10ms before and after the event')
    if a.defer_cut_contact and a.cut_after_s is None:p.error('Deferred cut contact requires an explicit diagnostic cut')
    a.out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic();app=physics=stage=cache=None;attached=False
    report=dict(status='running',score=None,robot_demo=False,dream_requests=0,
                joint_kind=a.joint_kind,ccd=a.ccd,self_contact=a.self_contact,clear_thread_sampling=a.clear_thread_sampling,
                physics_hz=a.physics_hz,seconds=a.seconds,solver=a.solver,passive_bending=a.passive_bending,loop_shape=a.loop_shape,
                diagnostic_cut_after_s=a.cut_after_s,defer_cut_contact=a.defer_cut_contact,cut_contact_events=[],
                source_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest()
                               for f in Path(__file__).parent.glob('*.py')})
    frames=[];velocities=[];times=[];elastic_history=[]
    def save():
        report['wall_seconds']=time.monotonic()-started
        (a.out/'probe.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        if frames:np.savez_compressed(a.out/'state.npz',poses=frames,velocities=velocities,times_s=times)
    def terminated(signum,frame):raise TimeoutError('Single-loop probe stopped by external watchdog')
    signal.signal(signal.SIGTERM,terminated)
    save()
    try:
        from isaaclab.app import AppLauncher
        app=AppLauncher(headless=True,enable_cameras=False).app
        from pxr import Gf,Sdf,Usd,UsdGeom,UsdPhysics,UsdUtils,PhysxSchema
        from omni.physx import get_physx_simulation_interface
        import omni.physics.tensors as tensors
        from geometry import stitch_loop
        from clamp_layout import transform
        from native_cloth import ensure_gpu_scene
        from native_stitches import author_thread,set_joint_enabled,restore_separated_cut_contacts
        from contact_audit import capsule_endpoints
        from thread_integrity import ThreadIntegrity
        from thread_bending import ThreadBending,circular_loop,elastic_diagnostics
        stage=Usd.Stage.CreateInMemory();cache=UsdUtils.StageCache.Get();cache.Insert(stage)
        stage_id=cache.GetId(stage).ToLongInt()
        UsdGeom.SetStageMetersPerUnit(stage,1.);UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.z)
        scene=UsdPhysics.Scene.Define(stage,'/physicsScene')
        scene.CreateGravityDirectionAttr(Gf.Vec3f(0.,0.,-1.));scene.CreateGravityMagnitudeAttr(9.81)
        ensure_gpu_scene(stage);native=PhysxSchema.PhysxSceneAPI(scene.GetPrim())
        native.CreateEnableGPUDynamicsAttr(False);native.CreateBroadphaseTypeAttr('MBP')
        native.CreateSolverTypeAttr(a.solver)
        native.CreateEnableCCDAttr(a.ccd!='none');native.CreateEnableExternalForcesEveryIterationAttr(False)
        nodes=transform(stitch_loop(0.,clear_capsules=a.clear_thread_sampling),lower_edge_supported=True);nodes-=nodes.mean(0)
        if a.loop_shape=='circle':nodes=circular_loop(np.linalg.norm(np.roll(nodes,-1,axis=0)-nodes,axis=1))
        bending=ThreadBending() if a.passive_bending else None
        thread=author_thread(stage,'/World/Thread',nodes,radius=.0004,joint_kind=a.joint_kind,bending=bending)
        if bending is not None:
            report['bending']=thread['bending']
            report['native_bending_drives']=[dict(joint=j,axis=axis,
                type=str(UsdPhysics.DriveAPI(stage.GetPrimAtPath(j),axis).GetTypeAttr().Get()),
                stiffness_per_degree=float(UsdPhysics.DriveAPI(stage.GetPrimAtPath(j),axis).GetStiffnessAttr().Get()),
                damping_per_degree=float(UsdPhysics.DriveAPI(stage.GetPrimAtPath(j),axis).GetDampingAttr().Get()),
                target_degrees=float(UsdPhysics.DriveAPI(stage.GetPrimAtPath(j),axis).GetTargetPositionAttr().Get()))
                for j in thread['joints'] for axis in ('rotY','rotZ')]
        for path in thread['bodies']:
            prim=stage.GetPrimAtPath(path);body=PhysxSchema.PhysxRigidBodyAPI(prim)
            body.CreateSolverVelocityIterationCountAttr(a.velocity_iterations)
            body.CreateEnableCCDAttr(a.ccd!='none');body.CreateEnableSpeculativeCCDAttr(a.ccd=='hybrid')
            if a.self_contact=='none':
                UsdPhysics.FilteredPairsAPI(prim).GetFilteredPairsRel().SetTargets(
                    [Sdf.Path(other) for other in thread['bodies'] if other!=path])
        report['native_configuration']=dict(gpu_dynamics=bool(native.GetEnableGPUDynamicsAttr().Get()),
            broadphase=str(native.GetBroadphaseTypeAttr().Get()),solver=str(native.GetSolverTypeAttr().Get()),
            scene_ccd=bool(native.GetEnableCCDAttr().Get()),
            body_ccd=[dict(sweep=bool(PhysxSchema.PhysxRigidBodyAPI(stage.GetPrimAtPath(path)).GetEnableCCDAttr().Get()),
                           speculative=bool(PhysxSchema.PhysxRigidBodyAPI(stage.GetPrimAtPath(path)).GetEnableSpeculativeCCDAttr().Get()))
                      for path in thread['bodies']])
        if (report['native_configuration']['gpu_dynamics'] or
                report['native_configuration']['solver']!=a.solver or any(
                row!={'sweep':a.ccd!='none','speculative':a.ccd=='hybrid'}
                for row in report['native_configuration']['body_ccd'])):
            raise RuntimeError('Native diagnostic settings differ from requested settings')
        stage.GetRootLayer().Export(str(a.out/'initial.usda'))
        physics=get_physx_simulation_interface();physics.attach_stage(stage_id);attached=True
        sim=tensors.create_simulation_view('torch',stage_id);sim.set_subspace_roots('/')
        if str(sim.device)!='cpu':raise RuntimeError('Expected CPU native tensor device')
        view=sim.create_rigid_body_view('/World/Thread/link_*')
        order=np.asarray([list(view.prim_paths).index(path) for path in thread['bodies']])
        initial=array(view.get_transforms())[order];mass=array(view.get_masses())[order].reshape(-1)
        inertia=array(view.get_inertias())[order].reshape(-1,3,3)
        lengths=thread['lengths'];audit=ThreadIntegrity([len(lengths)],.0004)
        audit.update(capsule_endpoints(initial,lengths),set(),0.)
        report['initial_thread_integrity']=audit.summary()
        report['native_mass_kg']=mass.tolist();report['authored_mass_kg']=thread['mass_kg']
        report['native_inertia_eigenvalues_kg_m2']=np.linalg.eigvalsh(inertia).tolist()
        report['native_inertia_positive_definite']=bool(np.all(np.linalg.eigvalsh(inertia)>0))
        report['initial_position_error_m']=float(np.linalg.norm(initial[:,:3]-(nodes+np.roll(nodes,-1,axis=0))/2,axis=1).max())
        energy_enabled=bending is not None or a.cut_after_s is not None
        rigidity=bending.rigidity_nm2 if bending is not None else 0.
        if energy_enabled:
            report['initial_elastic_diagnostic']=elastic_diagnostics(initial,array(view.get_velocities())[order],mass,inertia,lengths,rigidity)
        np.savez_compressed(a.out/'initial-native.npz',poses=initial,velocities=array(view.get_velocities())[order],
                            mass=mass,inertia=inertia,lengths=lengths,nodes=nodes)
        save()
        com0=np.average(initial[:,:3],axis=0,weights=mass);peak_nontranslation=0.;peak_speed=0.
        severed=set()
        for step in range(1,round(a.seconds*a.physics_hz)+1):
            if a.cut_after_s is not None and not severed and (step-1)/a.physics_hz>=a.cut_after_s-1e-12:
                report['cut_event']=dict(time_s=(step-1)/a.physics_hz,joint=0,
                    reason='Unscored zero-tool cut-end collision-energy diagnostic, not a task cutting event',
                    before=elastic_diagnostics(array(view.get_transforms())[order],array(view.get_velocities())[order],mass,inertia,lengths,rigidity))
                set_joint_enabled(stage,thread,0,False,restore_contact=not a.defer_cut_contact);severed.add(0)
            physics.simulate(1/a.physics_hz,(step-1)/a.physics_hz);physics.fetch_results()
            poses=array(view.get_transforms())[order];velocity=array(view.get_velocities())[order]
            axes=capsule_endpoints(poses,lengths)
            for index in restore_separated_cut_contacts(stage,[thread],axes):
                report['cut_contact_events'].append(dict(joint=index,time_s=step/a.physics_hz))
            report['pending_cut_contacts']=sorted(thread.get('pending_cut_contacts',set()))
            audit.update(axes,severed,step/a.physics_hz)
            com=np.average(poses[:,:3],axis=0,weights=mass)
            peak_nontranslation=max(peak_nontranslation,float(np.linalg.norm(poses[:,:3]-initial[:,:3]-(com-com0),axis=1).max()))
            peak_speed=max(peak_speed,float(np.linalg.norm(velocity[:,:3],axis=1).max()))
            frames.append(poses);velocities.append(velocity);times.append(step/a.physics_hz)
            if energy_enabled:
                elastic_history.append(dict(time_s=step/a.physics_hz,**elastic_diagnostics(poses,velocity,mass,inertia,lengths,rigidity)))
                report['elastic_history']=elastic_history
            report.update(completed_steps=step,simulated_s=step/a.physics_hz,thread_integrity=audit.summary(),
                maximum_nontranslation_m=peak_nontranslation,maximum_body_speed_m_s=peak_speed,
                centre_of_mass_displacement_m=(com-com0).tolist())
            if audit.first_failure is not None:
                report['status']='invalid_closed_chain';break
        if report['status']=='running':report['status']='complete'
        report['note']='Unscored diagnostic. No cloth, fixture, tool or robot exists. Self-contact exclusions, when requested, are not a task setting.'
    except BaseException as exc:
        report.update(status='failed',error=f'{type(exc).__name__}: {exc}',traceback=traceback.format_exc())
        raise
    finally:
        save()
        if attached:physics.detach_stage()
        if stage and cache:cache.Erase(stage)
        if app:app.close()


if __name__=='__main__':main()
