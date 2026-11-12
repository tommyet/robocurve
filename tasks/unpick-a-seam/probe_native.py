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
import numpy as np
from geometry import audit_scene


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=('intact','open'),default='intact')
    p.add_argument('--seconds',type=float,default=3.)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--physics-hz',type=int,choices=(480,960),default=960)
    a=p.parse_args()
    if not 0<a.seconds<=10:p.error('Diagnostic limited to ten simulated seconds')
    a.out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic();report={'status':'running','robot_demo':False,'mode':a.mode,'geometry':audit_scene(),
                                   'source_sha256':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                                                    for name in ('probe_native.py','native_stitches.py','native_cloth.py','geometry.py')}}
    from isaacsim import SimulationApp
    app=SimulationApp({'headless':True})
    try:
        from isaacsim.core.api import World
        import omni.physics.tensors as tensors
        from native_cloth import author_box,ensure_gpu_scene
        from native_stitches import author_pair
        world=World(physics_dt=1/a.physics_hz,rendering_dt=1/60,stage_units_in_meters=1.,backend='numpy')
        stage=world.stage;world.scene.add_default_ground_plane(z_position=0.)
        ensure_gpu_scene(stage)
        rotation=np.array(((0.,0.,1.),(0.,1.,0.),(-1.,0.,0.)))
        def transform(points):
            return (np.asarray(points)-(.235,0.,.7511))@rotation.T+(0.,0.,.5)
        cloth,threads=author_pair(stage,transform=transform,open_diagnostic=a.mode=='open')
        # Clamp upper edge with physical surfaces. The gap is 0.30 mm for the
        # 0.40 mm cloth; all native vertices stay dynamic.
        for sign in (-1,1):
            author_box(stage,f'/World/Jaw{sign+1}',(.006,.085,.008),
                       (.0004+sign*.00315,0.,.496),friction=.8)
        stage.GetRootLayer().Export(str(a.out/'initial.usda'))
        world.reset()
        sim=tensors.create_simulation_view('numpy');sim.set_subspace_roots('/')
        views=[sim.create_surface_deformable_body_view(f'/World/Cloth_{i}') for i in range(2)]
        if any(v.count!=1 for v in views):raise RuntimeError('Missing native cloth body')
        thread_view=sim.create_rigid_body_view('/World/Stitch_*/link_*')
        if thread_view.count!=sum(len(t['bodies']) for t in threads):raise RuntimeError('Missing native thread links')
        frames=[[],[]];thread_frames=[]
        for step in range(int(a.seconds*a.physics_hz)+1):
            if step:world.step(render=step%max(1,a.physics_hz//60)==0)
            if step%max(1,a.physics_hz//20)==0:
                for j,v in enumerate(views):
                    points=np.asarray(v.get_simulation_nodal_positions())[0,:len(cloth[j].rest)].copy()
                    if not np.isfinite(points).all():raise RuntimeError('Nonfinite native cloth nodes')
                    frames[j].append(points)
                thread_frames.append(np.asarray(thread_view.get_transforms()).copy())
        np.savez_compressed(a.out/'state.npz',left=frames[0],right=frames[1],
                            left_faces=cloth[0].faces,right_faces=cloth[1].faces,thread=thread_frames)
        report.update(status='complete',thread_count=thread_view.count,
                      right_centroid_drop_m=float(np.mean(cloth[1].rest[:,2])-np.mean(frames[1][-1][:,2])),
                      left_centroid_drop_m=float(np.mean(cloth[0].rest[:,2])-np.mean(frames[0][-1][:,2])),
                      note='Compare intact/open runs visually and numerically; no automatic feasibility pass.')
    except BaseException as exc:
        report.update(status='failed',error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        report['wall_seconds']=time.monotonic()-started
        (a.out/'probe.json').write_text(json.dumps(report,indent=2)+'\n');app.close()


if __name__=='__main__':main()
