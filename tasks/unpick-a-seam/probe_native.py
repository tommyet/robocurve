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
    p.add_argument('--continue-after-invalid',action='store_true',help='Bounded failure investigation only; invalid evidence never passes')
    p.add_argument('--continue-after-strain',action='store_true',
                   help='Diagnostic only: latch the 2% material-domain excursion but continue to the first geometric crossing; never valid task evidence')
    a=p.parse_args()
    if not 0<a.seconds<=10:p.error('Diagnostic limited to ten simulated seconds')
    a.out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic();report={'status':'running','robot_demo':False,'mode':a.mode,'geometry':audit_scene(),
                                   'physics_hz':a.physics_hz,'requested_seconds':a.seconds,
                                   'contact_refinement':a.contact_refinement,
                                   'hole_mesh_spacing_m':a.hole_mesh_spacing,
                                   'continue_after_strain':a.continue_after_strain,
                                   'continue_after_invalid':a.continue_after_invalid,
                                   'source_sha256':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                                                    for name in ('probe_native.py','native_stitches.py','native_cloth.py','geometry.py','contact_audit.py','inspection.py')}}
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
        scene.CreateGravityDirectionAttr(Gf.Vec3f(0.,0.,-1.));scene.CreateGravityMagnitudeAttr(9.80665)
        author_box(stage,'/World/Ground',(2.,2.,.02),(0.,0.,-.01))
        ensure_gpu_scene(stage)
        rotation=np.array(((0.,0.,1.),(0.,1.,0.),(-1.,0.,0.)))
        def transform(points):
            return (np.asarray(points)-(.235,0.,.7511))@rotation.T+(0.,0.,.5)
        phase='scene authoring'
        radius,hole_half=(.0004,.0008) if a.coarse_thread else (.0002,.0006)
        refined=a.contact_refinement in ('iterations','combined')
        contact_settings=ContactRefinement(
            speculative_ccd=a.contact_refinement in ('speculative','combined'),
            collision_iterations=4 if refined else 1,
            pair_update_frequency=4 if refined else 1)
        cloth,threads=author_pair(stage,transform=transform,open_diagnostic=a.mode=='open',
                                 thread_radius=radius,hole_half=hole_half,contact_refinement=contact_settings,
                                 hole_mesh_spacing=a.hole_mesh_spacing)
        report.update(thread_radius_m=radius,hole_width_m=2*hole_half,
                      cloth_geometry=[mesh.audit() for mesh in cloth],
                      authored_contact_settings=[{name:stage.GetPrimAtPath(f'/World/Cloth_{i}').GetAttribute(name).Get()
                         for name in contact_settings.attributes(64)} for i in range(2)])
        # Clamp upper edge with physical surfaces. The gap is 0.30 mm for the
        # 0.40 mm cloth; all native vertices stay dynamic.
        for sign in (-1,1):
            author_box(stage,f'/World/Jaw{sign+1}',(.006,.085,.008),
                       (.0004+sign*.00315,0.,.496),friction=.8)
        stage.GetRootLayer().Export(str(a.out/'initial.usda'))
        phase='stage attach'
        import carb
        carb.settings.get_settings().set_bool('/physics/suppressReadback',True)
        carb.settings.get_settings().set_int('/physics/cudaDevice',0)
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
        order=None
        lengths=np.concatenate([t['lengths'] for t in threads])
        frames=[[],[]];thread_frames=[];sample_times=[]
        previous_measured=[m.rest.copy() for m in cloth]
        previous_segments=np.concatenate([np.stack((t['nodes'],np.roll(t['nodes'],-1,axis=0)),axis=1) for t in threads])
        maximum_node_step_m=0.;maximum_thread_endpoint_step_m=0.
        strain=[StrainAudit(m.rest,m.faces) for m in cloth]
        contact=[ThreadClothAudit(m.faces) for m in cloth]
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
            previous_measured=[points.copy() for points in measured]
            previous_segments=segments.copy()
            if stop:break
        np.savez_compressed(a.out/'state.npz',left=frames[0],right=frames[1],
                            left_faces=cloth[0].faces,right_faces=cloth[1].faces,thread=thread_frames,
                            sample_times_s=sample_times,authored_left=cloth[0].rest,authored_right=cloth[1].rest)
        report.update(thread_count=thread_view.count,completed_steps=step,
                      maximum_node_step_m=maximum_node_step_m,
                      maximum_thread_endpoint_step_m=maximum_thread_endpoint_step_m,
                      right_centroid_drop_m=float(np.mean(cloth[1].rest[:,2])-np.mean(frames[1][-1][:,2])),
                      left_centroid_drop_m=float(np.mean(cloth[0].rest[:,2])-np.mean(frames[0][-1][:,2])),
                      strain=[{'maximum_principal_stretch':s.maximum_observed,
                               'first_validity_excursion':s.first_excursion} for s in strain],
                      contact_audit=[audit.summary() for audit in contact],
                      note='Compare intact/open runs visually and numerically; no automatic feasibility pass.')
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
