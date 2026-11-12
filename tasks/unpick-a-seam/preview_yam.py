"""Unscored YAM cloth/tool scene preview; normal ready pose, no Dream calls."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--steps',type=int,default=60)
    a=p.parse_args()
    if not 1<=a.steps<=200:p.error('Preview limited to 200 control steps')
    a.out.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    report={'status':'running','robot_demo':False,'source_sha256':{n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest()
            for n in ('preview_yam.py','scene.py','geometry.py','native_stitches.py','native_cloth.py','cutting.py','arena_cloth.py','arena_thread.py')}}
    from isaaclab.app import AppLauncher
    app=AppLauncher(headless=True,enable_cameras=True).app
    try:
        import omni.physics.tensors as tensors
        import omni.usd
        from yam_arena import inspect_embodiment as wrapper
        wrapper._APP=app
        emb=wrapper.YamArenaEmbodiment(task=str(Path(__file__).with_name('scene.py')),
            object_jitter=0.,control_hz=20,cam_width=224,cam_height=224)
        emb._ensure_sim(None)
        from yam_arena import scene as adapter
        namespace=adapter.task_object.__globals__;roots=namespace['ROOTS'];cloth=namespace['MESHES']
        from arena_thread import SPAWNED
        threads=[SPAWNED[f'stitch_{i}'] for i in range(6)]
        from cutting import ThreadCutter,DamageAudit
        from native_stitches import sever_contacted_joints
        sim=tensors.create_simulation_view('numpy');sim.set_subspace_roots('/')
        blade=sim.create_rigid_body_view(roots['ripper_blade'])
        paths=[p for thread in threads for p in thread['bodies']]
        contact=sim.create_rigid_contact_view([roots['ripper_blade']],filter_patterns=[paths],max_contact_data_count=4096)
        cutter=ThreadCutter([len(t['bodies']) for t in threads])
        envroot=roots['ripper_handle'].rsplit('/',1)[0]
        views=[sim.create_surface_deformable_body_view(envroot+'/'+name) for name in ('cloth_left','cloth_right')]
        damage=DamageAudit();previous_edge=[None]
        edge_local=np.column_stack((np.full(9,.0005),np.linspace(-.002,.002,9),np.zeros(9)))
        base=emb._base;write=base.scene.write_data_to_sim
        def cut_step(*args,**kwargs):
            f=np.asarray(contact.get_contact_force_matrix(dt=float(base.physics_dt))).reshape(-1,3)
            pose=np.asarray(blade.get_transforms())[0]
            q=pose[3:]
            x,y,z,w=q/np.linalg.norm(q)
            normal=np.array((1-2*(y*y+z*z),2*(x*y+w*z),2*(x*z-w*y)))
            rotation=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                               [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                               [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
            edge=edge_local@rotation.T+pose[:3]
            nodes=[np.asarray(view.get_simulation_nodal_positions())[0,:len(m.rest)] for view,m in zip(views,cloth)]
            damage.update(edge if previous_edge[0] is None else previous_edge[0],edge,nodes,[m.faces for m in cloth],cutter.t)
            previous_edge[0]=edge.copy()
            sever_contacted_joints(omni.usd.get_context().get_stage(),threads,cutter.update(f,normal,float(base.physics_dt)))
            return write(*args,**kwargs)
        base.scene.write_data_to_sim=cut_step
        emb._env.reset()
        for i in range(a.steps):emb._env.step(emb._ready)
        nodes=[np.asarray(view.get_simulation_nodal_positions())[0,:len(m.rest)] for view,m in zip(views,cloth)]
        np.savez_compressed(a.out/'cloth.npz',left=nodes[0],right=nodes[1])
        report.update(status='complete',score=None,cut_events=cutter.events,damage_events=damage.events,
                      note='Unscored integration preview; damage crossings are recorded; tensile damage and final stitch inspection remain unvalidated.')
    except BaseException as exc:
        report.update(status='failed',error=f'{type(exc).__name__}: {exc}');raise
    finally:
        report['wall_seconds']=time.monotonic()-started
        (a.out/'preview.json').write_text(json.dumps(report,indent=2)+'\n');app.close()


if __name__=='__main__':main()
