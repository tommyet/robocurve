"""Three-second native flat-fabric drape check; not a knot demonstration."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time
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
    args=p.parse_args()
    if not 0 < args.seconds <= 10:
        p.error('diagnostics are limited to ten simulated seconds')
    args.output.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    from isaacsim import SimulationApp
    app=SimulationApp({'headless':args.headless=='true'})
    report={'status':'running','kind':'diagnostic_not_submission_evidence',
            'mode':args.mode,'material':asdict(TIE_FABRIC),'physics_hz':args.physics_hz,
            'seconds':args.seconds,'provenance':{}}
    for name in ('probe.py','cloth_mesh.py','native_cloth.py','layout.py'):
        report['provenance'][name]=hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
    try:
        from isaacsim.core.api import World
        from native_cloth import author_cloth,author_box,ensure_gpu_scene
        from layout import author_collar,TABLE
        import omni.physics.tensors as tensors
        world=World(physics_dt=1/args.physics_hz,rendering_dt=1/60,stage_units_in_meters=1.,backend='numpy')
        stage=world.stage
        ensure_gpu_scene(stage)
        world.scene.add_default_ground_plane(z_position=0.)
        author_box(stage,'/World/Table',(1.1,1.3,.06),(.36,0.,TABLE-.03),(.58,.39,.25))
        mesh=necktie()
        initial=initial_layout(mesh)
        if args.mode=='collar-drape':
            author_collar(stage)
        author_cloth(stage,'/World/Tie',mesh,TIE_FABRIC,points=initial,color=(.50,.08,.17),
                     vertex_colors=face_colors(mesh))
        stage.GetRootLayer().Export(str(args.output/'initial.usda'))
        world.reset()
        simview=tensors.create_simulation_view('numpy')
        simview.set_subspace_roots('/')
        view=simview.create_surface_deformable_body_view('/World/Tie')
        if view.count != 1:
            raise RuntimeError('Native cloth view did not register exactly one tie')
        frames=[]
        for step in range(int(args.seconds*args.physics_hz)+1):
            if step:
                world.step(render=step % max(1,args.physics_hz//60)==0)
            if step % max(1,args.physics_hz//20)==0:
                nodes=np.asarray(view.get_simulation_nodal_positions())[0,:len(mesh.rest)].copy()
                if nodes.shape != mesh.rest.shape or not np.isfinite(nodes).all():
                    raise RuntimeError('Invalid native tie telemetry')
                frames.append(nodes)
        frames=np.asarray(frames)
        np.savez_compressed(args.output/'nodes.npz',positions=frames,faces=mesh.faces,
                            rest=mesh.rest,initial=initial)
        final=frames[-1]
        report.update(status='complete',mesh=mesh.audit(),frames=len(frames),
                      max_initial_abs_edge_strain=float(np.max(np.abs(edge_strain(mesh.rest,initial,mesh.faces)))),
                      max_final_abs_edge_strain=float(np.max(np.abs(edge_strain(mesh.rest,final,mesh.faces)))),
                      final_z_min_m=float(final[:,2].min()),final_z_max_m=float(final[:,2].max()),
                      max_displacement_m=float(np.linalg.norm(final-initial,axis=1).max()),
                      validation='Only dynamics and collar contact can be assessed here. No knot/fit score.')
    except BaseException as exc:
        report.update(status='failed',error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        report['wall_seconds']=time.monotonic()-started
        (args.output/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
        app.close()


if __name__=='__main__':
    main()
