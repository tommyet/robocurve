"""Short native contact-resolution diagnostic, never a task episode or demo.

Start once from measured geometry with disclosed estimated velocities. Preserve
all physical cloth/thread geometry, material, contacts and cutting rules. Only
the diagnostic held-tool motion is prescribed with native kinematic targets.
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
    p.add_argument('--stage',type=Path,required=True);p.add_argument('--state',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--physics-hz',type=int,choices=(960,1920,3840),default=960)
    p.add_argument('--speed',type=float,choices=(0.,.25,1.),default=1.,
        help='Zero holds the initial handle target; measured dynamic-body velocities remain unchanged')
    p.add_argument('--effective-contact-diagnostic',action='store_true')
    p.add_argument('--convex-capsules-diagnostic',choices=('guards','all'),help='Equivalent convex surface candidate, before native physics only; never demo evidence')
    p.add_argument('--solver',choices=('TGS','PGS'),help='Explicit contact-constraint diagnostic; defaults to the archived native solver')
    p.add_argument('--thread-angular-ccd',action='store_true',help='Short diagnostic only: native speculative CCD for thread rotation, preserving sweep CCD and all physical parameters')
    p.add_argument('--position-iterations',type=int,choices=(128,255),default=128,
        help='Native constraint-resolution comparison only; no geometry, mass, material or validity changes')
    p.add_argument('--seconds',type=float,default=.1);a=p.parse_args()
    if not .05<=a.seconds<=.4:p.error('Short contact diagnostic requires0.05–0.4seconds')
    with np.load(a.state) as archive:data={key:archive[key] for key in archive.files}
    provenance=json.loads(a.state.with_suffix('.json').read_text())
    if provenance['data_sha256']!=hashlib.sha256(a.state.read_bytes()).hexdigest():
        raise ValueError('Diagnostic state hash mismatch')
    if provenance['source_sha256']['initial.usda']!=hashlib.sha256(a.stage.read_bytes()).hexdigest():
        raise ValueError('Original physical stage hash mismatch')
    a.out.mkdir(parents=True,exist_ok=False)
    report=dict(status='running',score=None,robot_demo=False,physics_hz=a.physics_hz,
        motion_speed=a.speed,requested_seconds=a.seconds,provenance=provenance,
        source_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in Path(__file__).parent.glob('*.py')})
    started=time.monotonic();app=stage=cache=physics=None;attached=False;history=[]
    def save():
        report['wall_seconds']=time.monotonic()-started
        (a.out/'probe.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        if history:np.savez_compressed(a.out/'states.npz',**{key:np.stack([row[key] for row in history]) for key in history[0]})
    def terminated(signum,frame):raise TimeoutError('External diagnostic watchdog')
    signal.signal(signal.SIGTERM,terminated);save()
    try:
        report['phase']='application launch';save()
        from isaaclab.app import AppLauncher
        app=AppLauncher(headless=True,enable_cameras=False,device='cpu').app
        # Kit's startup telemetry can fork. Trial116 crashed inside SciPy's
        # OpenBLAS at-fork thread shutdown, before any physics existed.
        from scipy.spatial.transform import Rotation,Slerp
        report['phase']='native stage construction';save()
        import torch,carb
        from pxr import Gf,Usd,UsdGeom,UsdPhysics,UsdUtils,PhysxSchema
        from omni.physx import get_physx_simulation_interface
        import omni.physics.tensors as tensors
        from geometry import Mesh
        from facet_cloth import mechanics,measured_surface
        from panel_diagnostics import solid_contacts
        from contact_audit import capsule_endpoints,ThreadClothAudit
        from thread_integrity import ThreadIntegrity,ClosedJunctionCrossings
        from cutting import ThreadCutter,CutParameters,DamageAudit
        from inspection import StrainAudit
        from native_stitches import sever_contacted_joints,restore_separated_cut_contacts
        from tool_geometry import blade_edge_samples
        # A new anonymous copy avoids modifying the archived original stage.
        original=Usd.Stage.Open(str(a.stage));stage=Usd.Stage.CreateInMemory()
        stage.GetRootLayer().TransferContent(original.Flatten())
        root='/World/envs/env_0'
        for name in ('LeftArm','RightArm'):
            if not stage.GetPrimAtPath(root+'/'+name):raise RuntimeError('Expected original robot root missing')
            stage.RemovePrim(root+'/'+name)
        for path in [str(prim.GetPath()) for prim in stage.Traverse() if prim.IsA(UsdGeom.Camera)]:stage.RemovePrim(path)
        cache=UsdUtils.StageCache.Get();cache.Insert(stage);stage_id=cache.GetId(stage).ToLongInt()
        transform_cache=UsdGeom.XformCache()
        def initial_body(path,pose,velocity):
            prim=stage.GetPrimAtPath(path)
            if not prim or not prim.HasAPI(UsdPhysics.RigidBodyAPI):raise RuntimeError('Missing native body '+path)
            q=pose[3:];tr=Gf.Transform();tr.SetTranslation(Gf.Vec3d(*map(float,pose[:3])))
            tr.SetRotation(Gf.Rotation(Gf.Quatd(float(q[3]),Gf.Vec3d(*map(float,q[:3])))))
            parent=transform_cache.GetLocalToWorldTransform(prim.GetParent())
            x=UsdGeom.Xformable(prim);x.ClearXformOpOrder();x.AddTransformOp().Set(tr.GetMatrix()*parent.GetInverse())
            body=UsdPhysics.RigidBodyAPI(prim)
            body.CreateVelocityAttr(Gf.Vec3f(*map(float,velocity[:3])))
            body.CreateAngularVelocityAttr(Gf.Vec3f(*map(float,np.rad2deg(velocity[3:]))))
        shells=[];paths=[]
        for side,name in enumerate(('cloth_left','cloth_right')):
            mesh=Mesh(data['left_rest' if side==0 else 'right_rest'],data['left_faces' if side==0 else 'right_faces'])
            model=mechanics(mesh,primitive_boxes=True)
            bodies=[f'{root}/{name}/facet_{i:03d}' for i in range(len(model['points']))]
            for path,pose,velocity in zip(bodies,data[f'facet_poses{side}'],data[f'facet_velocity{side}'],strict=True):initial_body(path,pose,velocity)
            shells.append(dict(mesh=mesh,model=model,bodies=bodies));paths.append(bodies)
        threads=[];thread_paths=[]
        for i in range(6):
            bodies=[f'{root}/stitch_{i}/link_{k:03d}' for k in range(24)]
            joints=[f'{root}/stitch_{i}/joint_{k:03d}' for k in range(24)]
            for k,path in enumerate(bodies):initial_body(path,data['thread'][24*i+k],data['thread_velocity'][24*i+k])
            threads.append(dict(bodies=bodies,joints=joints,lengths=data['thread_lengths'][24*i:24*(i+1)],radius_m=.0004))
            thread_paths.extend(bodies)
        for name in ('handle','blade'):initial_body(root+'/ripper_'+name,data[name],data[name+'_velocity'])
        if a.thread_angular_ccd:
            # PhysX sweep CCD handles translation; speculative contacts also
            # cover rotating capsule ends. This changes collision detection,
            # not geometry, forces, constraints or the physical cutting law.
            report['thread_angular_ccd']=[]
            for path in thread_paths:
                api=PhysxSchema.PhysxRigidBodyAPI.Apply(stage.GetPrimAtPath(path))
                api.CreateEnableSpeculativeCCDAttr(True)
                row=dict(path=path,sweep=bool(api.GetEnableCCDAttr().Get()),
                    speculative=bool(api.GetEnableSpeculativeCCDAttr().Get()))
                if not row['sweep'] or not row['speculative']:raise RuntimeError('Native thread CCD settings not applied')
                report['thread_angular_ccd'].append(row)
        if a.convex_capsules_diagnostic:
            from convex_capsule import replace_capsules
            paths_to_replace=[root+'/ripper_handle/Guard0',root+'/ripper_handle/Guard1']
            if a.convex_capsules_diagnostic=='all':paths_to_replace += [path+'/Shape' for path in thread_paths]
            report['convex_capsule_candidate']=replace_capsules(stage,paths_to_replace)
        initial_body(root+'/clamp_moving_jaw',data['jaw'],data['jaw_velocity'])
        UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath(root+'/ripper_handle')).CreateKinematicEnabledAttr(True)
        if a.effective_contact_diagnostic:
            PhysxSchema.PhysxContactReportAPI.Apply(stage.GetPrimAtPath(root+'/ripper_handle')).CreateThresholdAttr(0.)
        for prim in stage.Traverse():
            if prim.HasAPI(UsdPhysics.RigidBodyAPI):
                api=PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
                api.CreateSolverPositionIterationCountAttr(a.position_iterations)
                api.CreateSolverVelocityIterationCountAttr(1)
        report['position_iterations']=a.position_iterations
        for prim in stage.Traverse():
            if prim.IsA(UsdPhysics.Scene):
                api=PhysxSchema.PhysxSceneAPI.Apply(prim)
                api.CreateTimeStepsPerSecondAttr(a.physics_hz)
                if a.solver is not None:api.CreateSolverTypeAttr(a.solver)
                report['native_scene']=dict(solver=api.GetSolverTypeAttr().Get(),gpu=api.GetEnableGPUDynamicsAttr().Get(),
                    ccd=api.GetEnableCCDAttr().Get(),force_each_iteration=api.GetEnableExternalForcesEveryIterationAttr().Get())
        carb.settings.get_settings().set_bool('/physics/disableContactProcessing',False)
        stage.GetRootLayer().Export(str(a.out/'diagnostic-initial.usda'))
        physics=get_physx_simulation_interface();physics.attach_stage(stage_id);attached=True
        sim=tensors.create_simulation_view('torch',stage_id);sim.set_subspace_roots('/')
        if str(sim.device)!='cpu':raise RuntimeError('Expected CPU native scene')
        views=[sim.create_rigid_body_view(body_paths) for body_paths in paths]
        orders=[np.array([list(view.prim_paths).index(path) for path in body_paths]) for view,body_paths in zip(views,paths)]
        tv=sim.create_rigid_body_view(thread_paths);order=np.array([list(tv.prim_paths).index(path) for path in thread_paths])
        handle=sim.create_rigid_body_view(root+'/ripper_handle');blade=sim.create_rigid_body_view(root+'/ripper_blade')
        contact=sim.create_rigid_contact_view([root+'/ripper_blade'],filter_patterns=[thread_paths],max_contact_data_count=4096)
        filter_paths=list(contact.filter_paths)
        if filter_paths and isinstance(filter_paths[0],(list,tuple)):filter_paths=filter_paths[0]
        force_order=np.array([filter_paths.index(path) for path in thread_paths])
        handle_contact=None
        if a.effective_contact_diagnostic:
            handle_contact=sim.create_rigid_contact_view([root+'/ripper_handle'],filter_patterns=[thread_paths],max_contact_data_count=4096)
            hp=list(handle_contact.filter_paths)
            if hp and isinstance(hp[0],(list,tuple)):hp=hp[0]
            handle_order=np.array([hp.index(path) for path in thread_paths])
            report['effective_shape_counts']={'handle':int(handle.max_shapes),'blade':int(blade.max_shapes),'thread':int(tv.max_shapes)}
        cutter=ThreadCutter([24]*6,CutParameters(thread_radius_m=.0004));integrity=ThreadIntegrity([24]*6,.0004)
        crossing=[ThreadClothAudit(shell['mesh'].faces) for shell in shells]
        junctions=ClosedJunctionCrossings([s['mesh'].faces for s in shells],144)
        strains=[StrainAudit(s['mesh'].rest,s['mesh'].faces,maximum_stretch=1.05) for s in shells]
        damage=DamageAudit();previous_edge=None;peak_force=0.;dt=1/a.physics_hz
        times=data['tool_target_times'];targets=data['tool_targets'];rotation_path=Slerp(times,Rotation.from_quat(targets[:,3:]))
        indices=torch.tensor([0],dtype=torch.int32)
        for step in range(round(a.seconds*a.physics_hz)+1):
            t=step*dt
            if step:
                path_t=min(t*a.speed,float(times[-1]))
                target=np.r_[[np.interp(path_t,times,targets[:,axis]) for axis in range(3)],rotation_path(path_t).as_quat()]
                handle.set_kinematic_targets(torch.tensor(target[None],dtype=torch.float32),indices)
                physics.simulate(dt,t-dt);physics.fetch_results()
            thread=array(tv.get_transforms())[order];segments=capsule_endpoints(thread,data['thread_lengths'])
            blade_pose=array(blade.get_transforms())[0];br=Rotation.from_quat(blade_pose[3:]).as_matrix()
            edge=blade_edge_samples()@br.T+blade_pose[:3]
            poses=[array(view.get_transforms())[mapping] for view,mapping in zip(views,orders)]
            nodes=[];checks=[];solids=[]
            for side,(shell,pose) in enumerate(zip(shells,poses)):
                points,check=measured_surface(shell,pose,geometry_aperture_m=.0004)
                nodes.append(points);checks.append(check)
                solids.append(solid_contacts(shell['model'],pose,segments))
                crossing[side].update(points,segments,t);strains[side].update(points,t)
            connectors=integrity.update(segments,cutter.severed,t)
            junctions.update(nodes,connectors,cutter.severed,t)
            damage.update(edge if previous_edge is None else previous_edge,edge,nodes,[s['mesh'].faces for s in shells],t);previous_edge=edge
            invalid=bool(integrity.first_failure or any(c.first_failure for c in crossing) or any(s.first_excursion for s in strains) or
                any(not c['valid'] for c in checks) or any(s['native_midplane_intersections'] for s in solids) or damage.crossed_faces or
                any(not c['valid'] for c in junctions.summary()))
            if handle_contact is not None:
                if step==1:
                    from effective_tool_contact import query_guards
                    report['effective_guard_rays']=query_guards(array(handle.get_transforms())[0],root+'/ripper_handle')
                    from effective_tool_contact import query_native_bounds
                    report['effective_tool_bounds']=query_native_bounds(stage_id,root+'/ripper_handle',app)
                    if a.convex_capsules_diagnostic=='all':
                        report['effective_thread_bounds']=query_native_bounds(stage_id,thread_paths[0],app)
                hf=np.zeros((144,3)) if not step else array(handle_contact.get_contact_force_matrix(dt=dt))[0,handle_order]
                report.setdefault('handle_contact_history',[]).append(dict(time_s=t,maximum_force_n=float(np.linalg.norm(hf,axis=1).max()),force_by_thread_link=hf.tolist()))
                if step:
                    from effective_tool_contact import tool_contacts
                    report.setdefault('native_contact_points',[]).append(dict(time_s=t,pairs=tool_contacts(physics,root)))
            forces=np.zeros((144,3)) if not step else array(contact.get_contact_force_matrix(dt=dt))[0,force_order]
            edge_force=-forces@br[:,0];peak_force=max(peak_force,float(edge_force.max()))
            restore_separated_cut_contacts(stage,threads,segments)
            if step and not invalid:sever_contacted_joints(stage,threads,cutter.update(forces,br[:,0],dt))
            history.append(dict(time_s=np.array(t),thread=thread,thread_velocity=array(tv.get_velocities())[order],
                facet_poses0=poses[0],facet_poses1=poses[1],handle=array(handle.get_transforms())[0],blade=blade_pose,edge_force_n=edge_force))
            report.update(completed_steps=step,simulated_seconds=t,maximum_edge_force_n=peak_force,cut_events=cutter.events,
                thread_joint_integrity=integrity.summary(),facet_checks=checks,native_solid_checks=solids,
                contact_audit=[c.summary() for c in crossing],closed_junction_contact_audit=junctions.summary(),damage_events=damage.events,
                maximum_principal_stretch=[s.maximum_observed for s in strains])
            if step==0:
                report['initial_pose_error_m']=dict(thread=float(np.max(np.linalg.norm(thread[:,:3]-data['thread'][:,:3],axis=1))),
                    panels=[float(np.max(np.linalg.norm(pose[:,:3]-data[f'facet_poses{side}'][:,:3],axis=1))) for side,pose in enumerate(poses)])
                report['initial_velocity_error_m_s']=float(np.max(np.abs(array(tv.get_velocities())[order]-data['thread_velocity'])))
                if invalid:raise RuntimeError('Approximate diagnostic initial state fails unchanged guards')
            if invalid:
                report['status']='invalid_model_domain';report['first_invalid_step']=step;break
        if report['status']=='running':report['status']='complete'
    except BaseException as exc:
        report.update(status='failed',error=f'{type(exc).__name__}: {exc}',traceback=traceback.format_exc());raise
    finally:
        save()
        if attached:physics.detach_stage()
        if stage and cache:cache.Erase(stage)
        if app:app.close()


if __name__=='__main__':main()
