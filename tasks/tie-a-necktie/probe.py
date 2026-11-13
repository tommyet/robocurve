"""Three-second native flat-fabric drape check; not a knot demonstration."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time
import traceback
import numpy as np
from cloth_mesh import necktie,edge_strain
from layout import initial_layout,face_colors
from native_cloth import Fabric


TIE_FABRIC=Fabric(thickness=.0012,density=500.,youngs_modulus=3e6,
                  dynamic_friction=.45,bend_modulus=2.5e5,
                  contact_offset=.001,rest_offset=.0006)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=('collar-drape','free-fall'),default='collar-drape')
    p.add_argument('--seconds',type=float,default=3.)
    p.add_argument('--physics-hz',type=int,choices=(240,480,960),default=240)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--headless',choices=('true','false'),default='true')
    p.add_argument('--no-render',action='store_true',help='Only for diagnosing renderer failures; no RGB evidence')
    args=p.parse_args()
    if not 0 < args.seconds <= 10:
        p.error('diagnostics are limited to ten simulated seconds')
    args.output.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    from isaaclab.app import AppLauncher
    app=AppLauncher(headless=args.headless=='true', enable_cameras=not args.no_render).app
    report={'status':'running','kind':'diagnostic_not_submission_evidence',
            'mode':args.mode,'material':asdict(TIE_FABRIC),'physics_hz':args.physics_hz,
            'seconds':args.seconds,'provenance':{},'phase':'build',
            'render_bridge':None if args.no_render else 'native PhysX Fabric'}
    for name in ('probe.py','cloth_mesh.py','native_cloth.py','layout.py','probe_capture.py','probe_runtime.py'):
        report['provenance'][name]=hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
    capture=None
    world=None
    try:
        from probe_runtime import ProbeRuntime
        from native_cloth import author_cloth,author_box,ensure_gpu_scene
        from layout import author_collar,TABLE
        import omni.physics.tensors as tensors
        world=ProbeRuntime(app, 1/args.physics_hz, render=not args.no_render)
        stage=world.stage
        ensure_gpu_scene(stage)
        author_box(stage,'/World/Ground',(10.,10.,.1),(0.,0.,-.05))
        author_box(stage,'/World/Table',(1.1,1.3,.06),(.36,0.,TABLE-.03),(.58,.39,.25))
        mesh=necktie()
        initial=initial_layout(mesh)
        if args.mode=='collar-drape':
            author_collar(stage)
        author_cloth(stage,'/World/Tie',mesh,TIE_FABRIC,points=initial,color=(.50,.08,.17),
                     vertex_colors=face_colors(mesh))
        if not args.no_render:
            from probe_capture import ProbeCapture
            eye,target=(-.40,-1.10,1.48),(.40,0.,.98)
            capture=ProbeCapture(stage,args.output,eye,target)
        stage.GetRootLayer().Export(str(args.output/'initial.usda'))
        report['phase']='attach'
        world.start()
        report['phase']='tensor_view'
        simview=tensors.create_simulation_view('torch',stage_id=world.stage_id)
        simview.set_subspace_roots('/')
        view=simview.create_surface_deformable_body_view('/World/Tie')
        if view.count != 1:
            raise RuntimeError('Native cloth view did not register exactly one tie')
        report['phase']='simulate'
        report['initial_native_sample_time_s']=1/args.physics_hz
        report['initial_sample_note']='GPU native getters require one step; this is counted within the requested duration, not an extra warmup'
        frames=[]
        times=[]
        velocity_max=0.
        for step in range(1,round(args.seconds*args.physics_hz)+1):
            world.step(render=(capture is not None and step % max(1,args.physics_hz//60)==0))
            if capture is not None and step==1:
                # Renderer-only warmup after the first counted physics step.
                for _ in range(6):
                    world.render()
                capture.capture('initial')
            if step==1 or step % max(1,args.physics_hz//20)==0:
                times.append(step/args.physics_hz)
                nodes=view.get_simulation_nodal_positions().detach().cpu().numpy()[0,:len(mesh.rest)].copy()
                if nodes.shape != mesh.rest.shape or not np.isfinite(nodes).all():
                    raise RuntimeError('Invalid native tie telemetry')
                frames.append(nodes)
                velocities=view.get_simulation_nodal_velocities().detach().cpu().numpy()[0,:len(mesh.rest)]
                velocity_max=max(velocity_max,float(np.linalg.norm(velocities,axis=1).max()))
            if capture is not None and step and step % max(1,args.physics_hz//capture.fps)==0:
                capture.capture('final' if step==int(args.seconds*args.physics_hz) else None)
        frames=np.asarray(frames)
        np.savez_compressed(args.output/'nodes.npz',positions=frames,faces=mesh.faces,
                            rest=mesh.rest,initial=initial,times_s=np.asarray(times))
        final=frames[-1]
        report.update(max_nodal_speed_m_s=velocity_max,
                      max_transient_abs_edge_strain=float(max(np.abs(edge_strain(mesh.rest,f,mesh.faces)).max() for f in frames)))
        report.update(status='complete',phase='complete',mesh=mesh.audit(),frames=len(frames),
                      max_initial_abs_edge_strain=float(np.max(np.abs(edge_strain(mesh.rest,initial,mesh.faces)))),
                      max_final_abs_edge_strain=float(np.max(np.abs(edge_strain(mesh.rest,final,mesh.faces)))),
                      final_z_min_m=float(final[:,2].min()),final_z_max_m=float(final[:,2].max()),
                      max_displacement_m=float(np.linalg.norm(final-initial,axis=1).max()),
                      validation='Only dynamics and collar contact can be assessed here. No knot/fit score.')
    except BaseException as exc:
        report.update(status='failed',error=f'{type(exc).__name__}: {exc}',traceback=traceback.format_exc())
        print(report['traceback'],flush=True)
    finally:
        if capture is not None:
            report['rendering']=capture.close()
        report['wall_seconds']=time.monotonic()-started
        (args.output/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
        if world is not None:
            world.close()
        app.close()


if __name__=='__main__':
    main()
