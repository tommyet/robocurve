"""Unscored native articulated-shell mechanism probe; no robot or task score.

The retained/open seam preserves the physical clamp, thread and backing.
The separate bend coupon must establish free deflection of the same finite
shell before it can be described as flexible fabric. Root owns paid launches.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import signal
import time
import traceback
import numpy as np

HERE=Path(__file__).resolve().parent


def array(value):
    return getattr(value,'torch',value).detach().cpu().numpy().copy()


def native_snapshot(step,physics_hz,facet_poses,thread_poses=None,thread_lengths=None):
    """Copy raw native poses without sharing panel and thread storage.

    Separate arrays retain the actual collider geometry when averaged surface
    vertices flag a near-edge event. The body-count assertion catches accidental
    substitution of panel poses for thread poses before evidence is written.
    """
    result={'time_s':np.asarray(step/physics_hz)}
    for i,poses in enumerate(facet_poses):
        result[f'facet_poses_{i}']=np.asarray(poses,float).copy()
    if thread_poses is not None:
        values=np.asarray(thread_poses,float)
        if values.shape!=(len(thread_lengths),7):
            raise ValueError('Native thread snapshot body count does not match thread lengths')
        result['thread']=values.copy()
        result['thread_lengths']=np.asarray(thread_lengths,float).copy()
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--mode',choices=('intact','open','bend','freefall'),required=True)
    p.add_argument('--physics-hz',type=int,choices=(240,960),default=960)
    p.add_argument('--velocity-iterations',type=int,choices=(1,32),default=None,
                   help='Optional native rigid-body solver comparison; default preserves authored settings')
    p.add_argument('--box-panels',action='store_true',help='Merge each triangle pair into one native rectangular box panel; no convex mesh cooking')
    p.add_argument('--cpu-ccd',action='store_true',help='Same rigid box/thread scene on CPU PhysX with native sweep and speculative CCD; DirectGPU supports neither CCD mode')
    p.add_argument('--ccd-mode',choices=('hybrid','sweep'),default='hybrid',help='CPU comparison only: sweep omits speculative contacts while preserving linear CCD')
    p.add_argument('--solver',choices=('TGS','PGS'),default='TGS',help='Native CPU contact-solver comparison; geometry and material unchanged')
    p.add_argument('--recenter-at-seam',action='store_true',help='Coordinate-only comparison: translate every authored object and world-fixed jaw anchor so the seam is near the origin')
    p.add_argument('--clear-thread-sampling',action='store_true',help='Same centreline and diameter with24links per loop; no non-neighbour tangent capsules at reset')
    p.add_argument('--seconds',type=float,default=.5)
    p.add_argument('--record-every-step',action='store_true',help='Save raw native body poses at every substep for geometry diagnosis')
    p.add_argument('--continue-after-audit-warning',action='store_true',help='Unscored forensic recording only: retain contact/hinge warnings through the bounded duration; physically disjoint closed thread ends still stop')
    a=p.parse_args()
    if not .05<=a.seconds<=2:p.error('Bounded shell coupon requires0.05–2seconds')
    if a.cpu_ccd and not a.box_panels:p.error('CPU CCD comparison requires native box panels')
    if a.ccd_mode!='hybrid' and not a.cpu_ccd:p.error('CCD mode requires the CPU CCD comparison')
    if a.solver!='TGS' and not a.cpu_ccd:p.error('PGS comparison requires CPU PhysX')
    if a.recenter_at_seam and (not a.box_panels or a.mode not in ('intact','open')):
        p.error('Seam recentering requires a box-panel intact/open comparison')
    a.out.mkdir(parents=True,exist_ok=False)
    report=dict(status='running',mode=a.mode,physics_hz=a.physics_hz,seconds=a.seconds,
                score=None,robot_demo=False,dream_requests=0,
                source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.py')})
    app=physics=stage=cache=None;attached=False;started=time.monotonic();phase='startup'
    def save():
        report['wall_seconds']=time.monotonic()-started
        report['phase']=phase
        temporary=a.out/'probe.tmp.json'
        temporary.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        temporary.replace(a.out/'probe.json')
    def terminated(signum,frame):raise TimeoutError('Probe stopped by external watchdog')
    signal.signal(signal.SIGTERM,terminated)
    save()
    try:
        from isaaclab.app import AppLauncher
        app=AppLauncher(headless=True,enable_cameras=False).app
        from pxr import Gf,Usd,UsdGeom,UsdPhysics,UsdUtils,PhysxSchema
        from omni.physx import get_physx_simulation_interface
        import omni.physics.tensors as tensors
        from facet_cloth import ShellMaterial,shell_mesh,author_shell,measured_surface,cooked_hull_geometry
        from native_cloth import author_box,ensure_gpu_scene
        from native_stitches import author_thread
        from geometry import TABLE_TOP,STITCH_Y,stitch_loop
        from clamp_layout import transform
        from passive_clamp import fixture_boxes,author_guide,PARAMETERS,MOVING_NAME
        from repair_backing import fixture_boxes as backing_boxes
        from contact_audit import ThreadClothAudit,capsule_endpoints,match_capsule_order
        from thread_integrity import ThreadIntegrity,ClosedJunctionCrossings
        phase='authoring'
        cache=UsdUtils.StageCache.Get();stage=Usd.Stage.CreateInMemory();cache.Insert(stage)
        stage_id=cache.GetId(stage).ToLongInt()
        UsdGeom.SetStageMetersPerUnit(stage,1.);UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.z)
        scene=UsdPhysics.Scene.Define(stage,'/physicsScene')
        scene.CreateGravityDirectionAttr(Gf.Vec3f(0.,0.,-1.));scene.CreateGravityMagnitudeAttr(9.81)
        ensure_gpu_scene(stage)
        native=PhysxSchema.PhysxSceneAPI(scene.GetPrim())
        native.CreateEnableExternalForcesEveryIterationAttr(False)
        if a.cpu_ccd:
            native.CreateEnableGPUDynamicsAttr(False)
            native.CreateBroadphaseTypeAttr('MBP')
            native.CreateEnableCCDAttr(True)
            native.CreateSolverTypeAttr(a.solver)
        report['effective_external_forces_every_iteration']=bool(native.GetEnableExternalForcesEveryIterationAttr().Get())
        material=ShellMaterial();report['shell_material']=asdict(material)
        report['shell_bending_rigidity_nm']=material.rigidity_nm
        report['membrane_model']='Approximately inextensible rigid facets; finite hinge bending, not FEM'
        report['box_panels']=a.box_panels
        report['ccd_mode']=a.ccd_mode if a.cpu_ccd else 'direct_gpu_unsupported'
        report['clear_thread_sampling']=a.clear_thread_sampling
        isolated=a.mode in ('bend','freefall')
        offset=np.array((-.300,0.,-.8127)) if a.recenter_at_seam else np.zeros(3)
        report['world_coordinate_offset_m']=offset.tolist()
        meshes=[shell_mesh(True)] if isolated else [shell_mesh(True),shell_mesh(False)]
        shells=[];threads=[]
        for i,mesh in enumerate(meshes):
            if not isolated:mesh.rest=transform(mesh.rest,lower_edge_supported=True)+offset
            shells.append(author_shell(stage,f'/World/Shell_{i}',mesh,material,
                                       (.76,.68,.47) if i==0 else (.25,.42,.66),primitive_boxes=a.box_panels))
        report['shell_geometry']=[m.audit() for m in meshes]
        report['shell_body_counts']=[len(s['bodies']) for s in shells]
        report['shell_hinge_counts']=[len(s['joints']) for s in shells]
        report['shell_mass_kg']=[float(s['model']['masses'].sum()) for s in shells]
        if not a.box_panels:
            report['convex_hull_min_thickness_m']=[sorted(set(float(
                PhysxSchema.PhysxConvexHullCollisionAPI(stage.GetPrimAtPath(body+'/Shape')).GetMinThicknessAttr().Get())
                for body in shell['bodies'])) for shell in shells]
        else:
            report['collision_geometry']='Native Cube primitives with rectangular panel width/height and0.4mm thickness; no mesh approximation/cooking'
        if a.mode=='bend':
            centre_z=TABLE_TOP+.004
            author_box(stage,'/World/LowerJaw',(.010,.090,.008),(.240,0.,centre_z-.004-.0002))
            author_box(stage,'/World/UpperJaw',(.010,.090,.008),(.240,0.,centre_z+.004+.0002))
            report['bend_fixture']='First10mm of horizontal upper patch held between ordinary fixed jaws,0.4mm gap; no vertex or facet attachment'
        elif a.mode!='freefall':
            author_box(stage,'/World/Table',(1.1,1.3,.06),np.array((.36,0.,.7175))+offset)
            for name,size,position in [*fixture_boxes(lower_edge_supported=True),*backing_boxes()]:
                path=f'/World/{name}'
                position=np.asarray(position)+offset
                author_box(stage,path,size,position,dynamic=name==MOVING_NAME,mass=PARAMETERS.mass_kg,friction=.8)
                if name==MOVING_NAME:author_guide(stage,path,position)
            threads=[author_thread(stage,f'/World/Stitch_{i}',transform(stitch_loop(y,clear_capsules=a.clear_thread_sampling),lower_edge_supported=True)+offset,
                                   radius=.0004,open_diagnostic=a.mode=='open') for i,y in enumerate(STITCH_Y)]
        if a.velocity_iterations is not None:
            for prim in stage.Traverse():
                if prim.HasAPI(UsdPhysics.RigidBodyAPI):
                    PhysxSchema.PhysxRigidBodyAPI.Apply(prim).CreateSolverVelocityIterationCountAttr(a.velocity_iterations)
        if a.cpu_ccd:
            for prim in stage.Traverse():
                if prim.HasAPI(UsdPhysics.RigidBodyAPI):
                    body=PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
                    body.CreateEnableCCDAttr(True)
                    body.CreateEnableSpeculativeCCDAttr(a.ccd_mode=='hybrid')
        report['effective_scene_physics']={
            'gpu_dynamics':bool(native.GetEnableGPUDynamicsAttr().Get()),
            'broadphase':str(native.GetBroadphaseTypeAttr().Get()),
            'sweep_ccd':bool(native.GetEnableCCDAttr().Get()),
            'solver':str(native.GetSolverTypeAttr().Get()),
        }
        report['effective_body_ccd']=[dict(path=str(prim.GetPath()),
            sweep=bool(PhysxSchema.PhysxRigidBodyAPI(prim).GetEnableCCDAttr().Get()),
            speculative=bool(PhysxSchema.PhysxRigidBodyAPI(prim).GetEnableSpeculativeCCDAttr().Get()))
            for prim in stage.Traverse() if prim.HasAPI(UsdPhysics.RigidBodyAPI)]
        if a.cpu_ccd and (report['effective_scene_physics']!={
                'gpu_dynamics':False,'broadphase':'MBP','sweep_ccd':True,'solver':a.solver} or
                not all(row['sweep'] and row['speculative']==(a.ccd_mode=='hybrid') for row in report['effective_body_ccd'])):
            raise RuntimeError('CPU CCD settings did not reach every native body and the scene')
        report['rigid_solver_velocity_iterations']=sorted(set(int(
            PhysxSchema.PhysxRigidBodyAPI(prim).GetSolverVelocityIterationCountAttr().Get())
            for prim in stage.Traverse() if prim.HasAPI(UsdPhysics.RigidBodyAPI)))
        if a.mode=='freefall':
            report['freefall_fixture']='None: one free shell in gravity with no jaws, backing, table or thread'
        stage.GetRootLayer().Export(str(a.out/'initial.usda'))
        phase='attach';save()
        physics=get_physx_simulation_interface();physics.attach_stage(stage_id);attached=True
        sim=tensors.create_simulation_view('torch',stage_id);sim.set_subspace_roots('/')
        report['native_tensor_device']=str(sim.device)
        if a.cpu_ccd and str(sim.device)!='cpu':
            raise RuntimeError('CPU CCD scene unexpectedly exposes a GPU simulation tensor device')
        views=[sim.create_rigid_body_view(f'/World/Shell_{i}/facet_*') for i in range(len(shells))]
        if any(view.count!=len(shell['bodies']) for view,shell in zip(views,shells)):
            raise RuntimeError('Missing native facet bodies')
        thread_view=sim.create_rigid_body_view('/World/Stitch_*/link_*') if threads else None
        if threads and thread_view.count!=sum(len(t['bodies']) for t in threads):raise RuntimeError('Missing native thread bodies')
        lengths=np.concatenate([t['lengths'] for t in threads]) if threads else None
        contact=[ThreadClothAudit(m.faces) for m in meshes]
        integrity=ThreadIntegrity([len(t['lengths']) for t in threads],.0004) if threads else None
        junctions=ClosedJunctionCrossings([m.faces for m in meshes],len(lengths)) if threads else None
        cut_indices={sum(len(t['lengths']) for t in threads[:i]) for i in range(len(threads))} if a.mode=='open' else set()
        orders=[np.asarray([list(view.prim_paths).index(path) for path in shell['bodies']]) for view,shell in zip(views,shells)]
        report['initial_facet_state']=[]
        for shell,view,order in zip(shells,views,orders):
            points,check=measured_surface(shell,array(view.get_transforms())[order])
            check['maximum_authored_vertex_error_m']=float(np.linalg.norm(points-shell['mesh'].rest,axis=1).max())
            check['maximum_body_speed_m_s']=float(np.linalg.norm(array(view.get_velocities())[:,:3],axis=1).max())
            report['initial_facet_state'].append(check)
        thread_order=(np.asarray([list(thread_view.prim_paths).index(path) for thread in threads for path in thread['bodies']]) if threads else None)
        frames=[[] for _ in shells];facet_frames=[[] for _ in shells];velocity_frames=[[] for _ in shells];times=[];thread_frames=[]
        previous_native=native_snapshot(0,a.physics_hz,
            [array(view.get_transforms())[order] for view,order in zip(views,orders)],
            array(thread_view.get_transforms())[thread_order] if threads else None,lengths)
        report['forensic_continue_after_warning']=a.continue_after_audit_warning
        gap_peak=0.;deformation_peak=0.;phase='stepping'
        def save_state():
            arrays={'sample_times_s':times}
            for i,(rows,mesh) in enumerate(zip(frames,meshes)):
                arrays.update({f'patch_{i}':rows,f'rest_{i}':mesh.rest,f'faces_{i}':mesh.faces,
                               f'facet_poses_{i}':facet_frames[i],f'facet_velocities_{i}':velocity_frames[i]})
            if threads:arrays.update(thread=thread_frames,thread_lengths=lengths)
            temporary=a.out/'state.tmp.npz';np.savez_compressed(temporary,**arrays)
            temporary.replace(a.out/'state.npz')
        last_checkpoint=time.monotonic();save()
        for step in range(1,round(a.seconds*a.physics_hz)+1):
            physics.simulate(1/a.physics_hz,(step-1)/a.physics_hz);physics.fetch_results()
            if step==1 and not a.box_panels:
                try:report['cooked_hulls']=[cooked_hull_geometry(shell,stage) for shell in shells]
                except BaseException as exc:
                    report['cooked_hull_query_error']=f'{type(exc).__name__}: {exc}'
            if threads:
                thread_poses=array(thread_view.get_transforms())[thread_order]
                segments=capsule_endpoints(thread_poses,lengths)
            measured=[];checks=[];ordered_poses=[]
            for i,(shell,view) in enumerate(zip(shells,views)):
                facet_poses=array(view.get_transforms())
                points,check=measured_surface(shell,facet_poses[orders[i]])
                ordered_poses.append(facet_poses[orders[i]])
                measured.append(points);checks.append(check)
                gap_peak=max(gap_peak,check['maximum_hinge_endpoint_gap_m'])
                centred=points-points.mean(0)
                singular=np.linalg.svd(centred,compute_uv=False)
                deformation_peak=max(deformation_peak,float(singular[-1]/np.sqrt(len(points))))
                if threads:contact[i].update(points,segments,step/a.physics_hz)
            invalid=any(not c['valid'] for c in checks)
            if threads:
                connectors=integrity.update(segments,cut_indices,step/a.physics_hz)
                invalid|=junctions.update(measured,connectors,cut_indices,step/a.physics_hz)
                invalid|=integrity.first_failure is not None or any(c.first_failure is not None for c in contact)
            current_native=native_snapshot(step,a.physics_hz,ordered_poses,
                                            thread_poses if threads else None,lengths)
            if invalid and 'first_invalid_step' not in report:
                report.update(status='invalid_model_domain',first_invalid_step=step)
                np.savez_compressed(a.out/'first-event-native.npz',
                    **{f'previous_{key}':value for key,value in previous_native.items()},
                    **{f'current_{key}':value for key,value in current_native.items()})
            if a.record_every_step or step==1 or step%max(1,a.physics_hz//20)==0 or invalid or step==round(a.seconds*a.physics_hz):
                for rows,points in zip(frames,measured):rows.append(points)
                for rows,panel_poses in zip(facet_frames,ordered_poses):rows.append(panel_poses)
                for rows,view,order in zip(velocity_frames,views,orders):
                    rows.append(array(view.get_velocities())[order])
                times.append(step/a.physics_hz)
                if threads:thread_frames.append(current_native['thread'])
            report.update(completed_steps=step,maximum_hinge_endpoint_gap_m=gap_peak,
                          maximum_rms_nonplanarity_m=deformation_peak,
                          last_facet_checks=checks,contact_audit=[c.summary() for c in contact])
            if integrity:report['thread_joint_integrity']=integrity.summary()
            if junctions:report['closed_junction_contact_audit']=junctions.summary()
            previous_native=current_native
            if step==1 or time.monotonic()-last_checkpoint>=5.:
                save_state();save();last_checkpoint=time.monotonic()
                print(json.dumps({'step':step,'simulated_s':step/a.physics_hz,
                                  'wall_s':report['wall_seconds'],'status':report['status']}),flush=True)
            if integrity and integrity.first_failure is not None:
                report['stopped_on_disjoint_closed_thread']=True
                break
            if invalid and not a.continue_after_audit_warning:break
        save_state()
        if integrity:report['thread_joint_integrity']=integrity.summary()
        if junctions:report['closed_junction_contact_audit']=junctions.summary()
        if a.mode=='bend':
            tip=meshes[0].rest[:,0]>.300
            report['free_tip_mean_drop_m']=float((meshes[0].rest[tip,2]-measured[0][tip,2]).mean())
            held=meshes[0].rest[:,0]<=.245+1e-12
            report['clamped_region_maximum_displacement_m']=float(np.linalg.norm(measured[0][held]-meshes[0].rest[held],axis=1).max())
        report['final_maximum_body_speed_m_s']=[float(np.linalg.norm(rows[-1][:,:3],axis=1).max()) for rows in velocity_frames]
        if a.mode=='freefall':
            displacement=measured[0]-meshes[0].rest
            report['freefall_mean_displacement_m']=displacement.mean(0).tolist()
            report['freefall_maximum_nontranslation_m']=float(np.linalg.norm(displacement-displacement.mean(0),axis=1).max())
            report['freefall_analytic_drop_m']=.5*9.81*(step/a.physics_hz)**2
        if report['status']=='running':report['status']='complete'
        report['note']='Unscored mechanism evidence only; native bending and retention must be assessed before YAM integration.'
    except BaseException as exc:
        report.update(status='failed',error=f'{type(exc).__name__}: {exc}',error_phase=phase,traceback=traceback.format_exc())
        raise
    finally:
        if 'save_state' in locals():
            try:save_state()
            except Exception as exc:report['state_checkpoint_error']=f'{type(exc).__name__}: {exc}'
        save()
        if attached:physics.detach_stage()
        if stage and cache:cache.Erase(stage)
        if app:app.close()


if __name__=='__main__':main()
