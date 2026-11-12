"""Cheap native surface-cloth diagnostics, not a robot task demonstration.

Run under the retained Isaac Sim interpreter. No Dream calls are made. Start
with --mode drape --seconds 3, then clamp and open-clamp. All cloth and jaw
movement comes from native physics after the initial state is authored.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from cloth_mesh import Mesh,tshirt,edge_strain
from native_cloth import Fabric


def coupon():
    x,y=np.meshgrid(np.linspace(0,.18,37),np.linspace(-.025,.025,11))
    points=np.column_stack((x.ravel(),y.ravel(),np.zeros(x.size)))
    faces=[]
    for j in range(10):
        for i in range(36):
            a=j*37+i
            faces.extend(((a,a+1,a+38),(a,a+38,a+37)))
    return Mesh(points,np.asarray(faces),{})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=('drop','drape','clamp','open-clamp','task-layout'),default='drape')
    p.add_argument('--seconds',type=float,default=3.)
    p.add_argument('--physics-hz',type=int,choices=(240,480,960),default=240)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--headless',choices=('true','false'),default='true')
    args=p.parse_args()
    if not 0 < args.seconds <= 10:
        p.error('a diagnostic is limited to ten simulated seconds')
    args.output.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    # Application must precede all simulator imports.
    from isaacsim import SimulationApp
    app=SimulationApp({'headless':args.headless=='true'})
    report={'status':'running','kind':'diagnostic_not_submission_evidence',
            'mode':args.mode,'material':asdict(Fabric()),'physics_hz':args.physics_hz,
            'seconds':args.seconds,'provenance':{}}
    for name in ('probe.py','cloth_mesh.py','native_cloth.py','scene.py'):
        report['provenance'][name]=hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
    try:
        from isaacsim.core.api import World
        from pxr import Gf,UsdGeom,UsdPhysics
        import omni.physics.tensors as tensors
        from native_cloth import author_cloth,author_box,author_peg,ensure_gpu_scene
        world=World(physics_dt=1/args.physics_hz,rendering_dt=1/60,stage_units_in_meters=1.,backend='numpy')
        stage=world.stage
        world.scene.add_default_ground_plane(z_position=0.)
        ensure_gpu_scene(stage)
        cloth_path='/World/Cloth'
        if args.mode=='task-layout':
            from scene import author_props,initial_layout,TABLE
            author_box(stage,'/World/Table',(1.1,1.3,.06),(.36,0.,TABLE-.03),(.58,.39,.25))
            mesh=author_props(stage)
            initial=initial_layout(mesh)
            cloth_path='/World/Tshirt'
        elif args.mode in ('drop','drape'):
            mesh=tshirt()
            initial=mesh.rest.copy()
            initial[:,0]+=.05
            initial[:,1]-=.15
            initial[:,2]+=.40
            if args.mode=='drape':
                # A 10 mm round rail does not pin any vertices.
                rail=UsdGeom.Cylinder.Define(stage,'/World/Rail')
                rail.CreateRadiusAttr(.005)
                rail.CreateHeightAttr(.55)
                rail.CreateAxisAttr('X')
                rail.AddTranslateOp().Set(Gf.Vec3d(.05,0.,.32))
                UsdPhysics.CollisionAPI.Apply(rail.GetPrim())
        else:
            mesh=coupon()
            initial=mesh.rest.copy()
            initial[:,2]+=.5004
            author_peg(stage,'/World/Peg',pos=(0.,0.,.5),fixed_lower=True,
                       spring=args.mode=='clamp',open_angle=-.35)
            if args.mode=='open-clamp':
                # Negative diagnostic: the jaw is fixed in the declared open
                # pose. This fixture is never used in a task episode.
                UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath('/World/Peg/upper')).CreateKinematicEnabledAttr(True)
        if args.mode!='task-layout':
            author_cloth(stage,cloth_path,mesh,points=initial)
        stage.GetRootLayer().Export(str(args.output/'initial.usda'))
        world.reset()
        simview=tensors.create_simulation_view('numpy')
        simview.set_subspace_roots('/')
        cloth=simview.create_surface_deformable_body_view(cloth_path)
        if cloth.count != 1:
            raise RuntimeError('Native cloth view did not register exactly one body')
        frames=[]
        for step in range(int(args.seconds*args.physics_hz)+1):
            if step:
                world.step(render=(step % max(1,args.physics_hz//60)==0))
            if step % max(1,args.physics_hz//20)==0:
                points=np.asarray(cloth.get_simulation_nodal_positions())[0,:len(mesh.rest)].copy()
                if points.shape != mesh.rest.shape or not np.isfinite(points).all():
                    raise RuntimeError('Invalid native cloth telemetry')
                frames.append(points)
        frames=np.asarray(frames)
        np.savez_compressed(args.output/'nodes.npz',positions=frames,faces=mesh.faces,
                            rest=mesh.rest,initial=initial)
        final=frames[-1]
        strain=edge_strain(mesh.rest,final,mesh.faces)
        # Native dynamics diagnostics only: none is a task success score.
        report.update(status='complete',mesh=mesh.audit(),frames=len(frames),
                      max_displacement_m=float(np.linalg.norm(final-initial,axis=1).max()),
                      final_z_min_m=float(final[:,2].min()),
                      final_z_max_m=float(final[:,2].max()),
                      final_z_range_m=float(np.ptp(final[:,2])),
                      max_abs_edge_strain=float(np.max(np.abs(strain))),
                      nodes_above_45cm=int(np.sum(final[:,2]>.45)),
                      validation='Requires visual and differential interpretation; no auto-pass.')
    except BaseException as exc:
        report.update(status='failed',error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        report['wall_seconds']=time.monotonic()-started
        (args.output/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
        app.close()


if __name__=='__main__':
    main()
