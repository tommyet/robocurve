"""Native cloth/thread retention probe, not a robot demo or task score.

Compare intact versus deliberately pre-cut loops. Both swatches remain native
flexible meshes, supported only by contact with thread and a diagnostic clamp.
No Dream calls; no animation, body-position writes or cloth attachments.
"""
import argparse
import json
import hashlib
from pathlib import Path
import time
import traceback
import numpy as np
from geometry import audit_scene


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=('intact','open'),default='intact')
    p.add_argument('--seconds',type=float,default=3.)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--physics-hz',type=int,choices=(480,960,1920,3840),default=960)
    p.add_argument('--coarse-thread',action='store_true',help='Diagnostic 0.8 mm thread / 1.6 mm holes; does not change task reset')
    p.add_argument('--contact-refinement',choices=('baseline','iterations','speculative','combined'),
                   default='baseline',help='Diagnostic native deformable contact settings only; geometry/material/audit unchanged')
    p.add_argument('--hole-mesh-spacing',type=float,default=None,
                   help='Diagnostic local collision/simulation mesh refinement in metres; same holes, area and material')
    p.add_argument('--quality-mesh',action='store_true',help='Opt-in graded 0.4 mm hole-boundary triangulation; requires coarse thread and no hole-mesh-spacing')
    p.add_argument('--sewing-clamp',action='store_true',help='Use exactly the YAM candidate rigid transform, connected fixture and table, without the YAM loader/reset or robot')
    p.add_argument('--passive-clamp',action='store_true',help='Use the force-limited spring jaw with --sewing-clamp')
    p.add_argument('--maximum-stretch',type=float,choices=(1.02,1.05),default=1.02,
                   help='Same explicit engineering domain as preview_yam; 2%% warnings remain visible')
    p.add_argument('--continue-after-invalid',action='store_true',help='Bounded failure investigation only; invalid evidence never passes')
    p.add_argument('--record-contact-history',action='store_true',
                   help='Per-substep contact occupancy/depth for failure analysis; requires --continue-after-invalid and never restores validity')
    p.add_argument('--continue-after-strain',action='store_true',
                   help='Diagnostic only: latch the 2%% material-domain excursion but continue to the first geometric crossing; never valid task evidence')
    a=p.parse_args()
    if not 0<a.seconds<=10:p.error('Diagnostic limited to ten simulated seconds')
    if a.quality_mesh and (not a.coarse_thread or a.hole_mesh_spacing is not None):
        p.error('Quality mesh requires --coarse-thread and omitting --hole-mesh-spacing')
    if a.sewing_clamp and (not a.coarse_thread or (not a.quality_mesh and a.hole_mesh_spacing!=.0004)):
        p.error('Sewing clamp requires --coarse-thread and either --hole-mesh-spacing .0004 or --quality-mesh')
    if a.passive_clamp and not a.sewing_clamp:p.error('Passive clamp requires --sewing-clamp')
    if a.record_contact_history and not a.continue_after_invalid:
        p.error('Contact history requires --continue-after-invalid')
    a.out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic();report={'status':'running','robot_demo':False,'mode':a.mode,'geometry':audit_scene(),
                                   'physics_hz':a.physics_hz,'requested_seconds':a.seconds,
                                   'contact_refinement':a.contact_refinement,
                                   'hole_mesh_spacing_m':a.hole_mesh_spacing,
                                   'mesh_method':'graded_delaunay' if a.quality_mesh else 'rectilinear',
                                   'sewing_clamp':a.sewing_clamp,'maximum_stretch':a.maximum_stretch,
                                   'passive_clamp':a.passive_clamp,
                                   'continue_after_strain':a.continue_after_strain,
                                   'continue_after_invalid':a.continue_after_invalid,
                                   'record_contact_history':a.record_contact_history,
                                   'source_sha256':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                                                    for name in ('probe_native.py','native_stitches.py','native_cloth.py','geometry.py','quality_mesh.py','contact_audit.py','contact_history.py','inspection.py','clamp_layout.py','scene_snapshot.py','passive_clamp.py')}}
    app=None;attached=False;stage=None;cache=None;physics=None
    phase='launch'
    try:
        from isaaclab.app import AppLauncher
        app=AppLauncher(headless=True,enable_cameras=False).app
        phase='imports'
        from pxr import Gf,Usd,UsdGeom,UsdPhysics,UsdUtils
        from omni.physx import get_physx_simulation_interface
        import omni.physics.tensors as tensors
        from native_cloth import author_box,ensure_gpu_scene,ContactRefinement
        from native_stitches import author_pair
        from inspection import StrainAudit
        from contact_audit import ThreadClothAudit,capsule_endpoints,match_capsule_order
        phase='stage creation'
        cache=UsdUtils.StageCache.Get();stage=Usd.Stage.CreateInMemory();cache.Insert(stage)
        stage_id=cache.GetId(stage).ToLongInt()
        UsdGeom.SetStageMetersPerUnit(stage,1.);UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.z)
        scene=UsdPhysics.Scene.Define(stage,'/physicsScene')
        scene.CreateGravityDirectionAttr(Gf.Vec3f(0.,0.,-1.));scene.CreateGravityMagnitudeAttr(9.81 if a.sewing_clamp else 9.80665)
        author_box(stage,'/World/Ground',(2.,2.,.02),(0.,0.,-.01))
        ensure_gpu_scene(stage)
        rotation=np.array(((0.,0.,1.),(0.,1.,0.),(-1.,0.,0.)))
        def transform(points):
            return (np.asarray(points)-(.235,0.,.7511))@rotation.T+(0.,0.,.5)
        fixture_roots={}
        if a.sewing_clamp:
            from clamp_layout import transform,fixture_boxes
            if a.passive_clamp:
                from passive_clamp import fixture_boxes,author_guide,description,PARAMETERS,MOVING_NAME
                report['passive_clamp_description']=description()
            # Same physical table bounds as the YAM station. No cloth touches
            # it at reset; the lowest patch starts 20 mm above its top.
            author_box(stage,'/World/Table',(1.1,1.3,.06),(.36,0.,.7175))
        phase='scene authoring'
        radius,hole_half=(.0004,.0008) if a.coarse_thread else (.0002,.0006)
        refined=a.contact_refinement in ('iterations','combined')
        contact_settings=ContactRefinement(
            speculative_ccd=a.contact_refinement in ('speculative','combined'),
            collision_iterations=4 if refined else 1,
            pair_update_frequency=4 if refined else 1)
        cloth,threads=author_pair(stage,transform=transform,open_diagnostic=a.mode=='open',
                                 thread_radius=radius,hole_half=hole_half,contact_refinement=contact_settings,
                                 hole_mesh_spacing=a.hole_mesh_spacing,quality_mesh=a.quality_mesh)
        report.update(thread_radius_m=radius,hole_width_m=2*hole_half,
                      cloth_geometry=[mesh.audit() for mesh in cloth],
                      authored_contact_settings=[{name:stage.GetPrimAtPath(f'/World/Cloth_{i}').GetAttribute(name).Get()
                         for name in contact_settings.attributes(64)} for i in range(2)])
        # Clamp upper edge with physical surfaces. The gap is 0.30 mm for the
        # 0.40 mm cloth; all native vertices stay dynamic.
        if a.sewing_clamp:
            for name,size,position in fixture_boxes():
                fixture_roots[name]=f'/World/{name}'
                moving=a.passive_clamp and name==MOVING_NAME
                author_box(stage,fixture_roots[name],size,position,friction=.8,
                           dynamic=moving,mass=PARAMETERS.mass_kg if moving else .005)
                if moving:author_guide(stage,fixture_roots[name],position)
        else:
            for sign in (-1,1):
                fixture_roots[f'clamp_jaw_{sign+1}']=f'/World/Jaw{sign+1}'
                author_box(stage,f'/World/Jaw{sign+1}',(.006,.085,.008),
                           (.0004+sign*.00315,0.,.496),friction=.8)
        stage.GetRootLayer().Export(str(a.out/'initial.usda'))
        phase='stage attach'
        import carb
        carb.settings.get_settings().set_bool('/physics/suppressReadback',True)
        carb.settings.get_settings().set_int('/physics/cudaDevice',0)
        from scene_snapshot import authored_scene
        report['authored_scene']=authored_scene(stage,fixture_roots)
        # The native surface-deformable GPU pipeline does not support CCD.
        from pxr import PhysxSchema
        PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim()).CreateEnableCCDAttr(False)
        physics=get_physx_simulation_interface();physics.attach_stage(stage_id);attached=True
        phase='tensor views'
        sim=tensors.create_simulation_view('torch',stage_id);sim.set_subspace_roots('/')
        views=[sim.create_surface_deformable_body_view(f'/World/Cloth_{i}') for i in range(2)]
        if any(v.count!=1 for v in views):raise RuntimeError('Missing native cloth body')
        thread_view=sim.create_rigid_body_view('/World/Stitch_*/link_*')
        if thread_view.count!=sum(len(t['bodies']) for t in threads):raise RuntimeError('Missing native thread links')
        moving_jaw=None;jaw_frames=[];jaw_velocity_frames=[]
        if a.passive_clamp:
            moving_jaw=sim.create_rigid_body_view(fixture_roots[MOVING_NAME])
            if moving_jaw.count!=1:raise RuntimeError('Missing native passive jaw')
        order=None
        lengths=np.concatenate([t['lengths'] for t in threads])
        frames=[[],[]];thread_frames=[];sample_times=[]
        previous_measured=[m.rest.copy() for m in cloth]
        previous_segments=np.concatenate([np.stack((t['nodes'],np.roll(t['nodes'],-1,axis=0)),axis=1) for t in threads])
        maximum_node_step_m=0.;maximum_thread_endpoint_step_m=0.
        strain=[StrainAudit(m.rest,m.faces,maximum_stretch=a.maximum_stretch) for m in cloth]
        contact=[ThreadClothAudit(m.faces) for m in cloth]
        history=[]
        if a.record_contact_history:
            from contact_history import ContactHistory
            history=[ContactHistory(m.faces,radius,1/a.physics_hz) for m in cloth]
        phase='physics stepping'
        steps=round(a.seconds*a.physics_hz)
        for step in range(1,steps+1):
            # Native GPU tensors cannot fetch before the first simulation step.
            # This first step is included in duration; there is no hidden warmup.
            physics.simulate(1/a.physics_hz,(step-1)/a.physics_hz);physics.fetch_results()
            poses=thread_view.get_transforms().detach().cpu().numpy()
            if order is None:order=match_capsule_order(poses,threads,tolerance_m=.00025)
            poses=poses[order].copy()
            segments=capsule_endpoints(poses,lengths)
            sample=step==1 or step==steps or step%max(1,a.physics_hz//20)==0
            measured=[]
            for j,v in enumerate(views):
                points=v.get_simulation_nodal_positions().detach().cpu().numpy()[0,:len(cloth[j].rest)].copy()
                if not np.isfinite(points).all():raise RuntimeError('Nonfinite native cloth nodes')
                strain[j].update(points,step/a.physics_hz)
                contact[j].update(points,segments,step/a.physics_hz)
                if history:history[j].update(points,segments,step/a.physics_hz)
                measured.append(points)
            node_step=max(float(np.linalg.norm(now-before,axis=1).max())
                          for now,before in zip(measured,previous_measured))
            thread_step=float(np.linalg.norm(segments-previous_segments,axis=2).max())
            maximum_node_step_m=max(maximum_node_step_m,node_step)
            maximum_thread_endpoint_step_m=max(maximum_thread_endpoint_step_m,thread_step)
            strain_invalid=any(audit.first_excursion is not None for audit in strain)
            contact_invalid=any(audit.first_failure is not None for audit in contact)
            invalid=strain_invalid or contact_invalid
            def save_pair(filename):
                np.savez_compressed(a.out/filename,
                    previous_left=previous_measured[0],previous_right=previous_measured[1],
                    current_left=measured[0],current_right=measured[1],
                    previous_thread_segments=previous_segments,current_thread_segments=segments,
                    left_faces=cloth[0].faces,right_faces=cloth[1].faces,
                    time_s=step/a.physics_hz,dt=1/a.physics_hz)
            if invalid:
                report.update(status='invalid_model_domain')
                if 'first_invalid_step' not in report:
                    report.update(first_invalid_step=step,first_invalid_node_step_m=node_step,
                                  first_invalid_thread_endpoint_step_m=thread_step)
                    save_pair('first-invalid-pair.npz');sample=True
            if contact_invalid and 'first_contact_failure_step' not in report:
                report['first_contact_failure_step']=step
                save_pair('first-contact-pair.npz');sample=True
            stop=invalid and not a.continue_after_invalid and (contact_invalid or not a.continue_after_strain)
            if stop:sample=True
            if sample:
                for j,points in enumerate(measured):frames[j].append(points)
            if sample:thread_frames.append(poses);sample_times.append(step/a.physics_hz)
            if sample and moving_jaw is not None:
                jaw_frames.append(moving_jaw.get_transforms().detach().cpu().numpy()[0].copy())
                jaw_velocity_frames.append(moving_jaw.get_velocities().detach().cpu().numpy()[0].copy())
            previous_measured=[points.copy() for points in measured]
            previous_segments=segments.copy()
            if stop:break
        np.savez_compressed(a.out/'state.npz',left=frames[0],right=frames[1],
                            left_faces=cloth[0].faces,right_faces=cloth[1].faces,thread=thread_frames,
                            sample_times_s=sample_times,authored_left=cloth[0].rest,authored_right=cloth[1].rest,
                            moving_jaw=jaw_frames,moving_jaw_velocity=jaw_velocity_frames)
        if a.passive_clamp:
            from passive_clamp import FRONT_FACE,MOVING_SIZE,MOVING_POSITION
            position,velocity=jaw_frames[-1],jaw_velocity_frames[-1]
            displacement=float(position[0]-MOVING_POSITION[0])
            drive_force=float(np.clip(PARAMETERS.stiffness_n_m*(-PARAMETERS.initial_gap_m-displacement)
                                      -PARAMETERS.damping_n_s_m*velocity[0],
                                      -PARAMETERS.force_limit_n,PARAMETERS.force_limit_n))
            report['passive_jaw_final']={'pose_xyzw':position.tolist(),'velocity':velocity.tolist(),
                'gap_m':float(position[0]-MOVING_SIZE[0]/2-FRONT_FACE),
                'inferred_drive_force_x_n':drive_force,
                'force_note':'Computed from authored spring/damper law and measured state, not a native contact-force measurement'}
        report.update(thread_count=thread_view.count,completed_steps=step,
                      maximum_node_step_m=maximum_node_step_m,
                      maximum_thread_endpoint_step_m=maximum_thread_endpoint_step_m,
                      right_centroid_drop_m=float(np.mean(cloth[1].rest[:,2])-np.mean(frames[1][-1][:,2])),
                      left_centroid_drop_m=float(np.mean(cloth[0].rest[:,2])-np.mean(frames[0][-1][:,2])),
                      strain=[{'maximum_principal_stretch':s.maximum_observed,
                               'first_validity_excursion':s.first_excursion,
                               'first_2pct_warning':s.first_warning,
                               'maximum_stretch_limit':s.limit} for s in strain],
                      contact_audit=[audit.summary() for audit in contact],
                      note='Compare intact/open runs visually and numerically; no automatic feasibility pass.')
        if history:
            report['contact_history']=[h.summary() for h in history]
            (a.out/'contact-history.json').write_text(json.dumps(
                {'status':report['status'],'never_task_evidence':True,
                 'patches':[{'summary':h.summary(),'rows':h.rows} for h in history]},indent=2)+'\n')
        if report['status']=='running':report['status']='complete'
    except BaseException as exc:
        report.update(status='failed',error=f'{type(exc).__name__}: {exc}',error_phase=phase,
                      error_traceback=traceback.format_exc())
        raise
    finally:
        report['wall_seconds']=time.monotonic()-started
        (a.out/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
        if attached:physics.detach_stage()
        if stage and cache:cache.Erase(stage)
        if app:app.close()


if __name__=='__main__':main()
