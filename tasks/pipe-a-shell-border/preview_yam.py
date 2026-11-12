"""Unscored YAM integration preview. Robot stays at its ordinary ready pose.

Requires the pinned team simulator. No Dream call, privileged demo controller,
or object-state writes. This is an integration check, not task completion.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--steps',type=int,default=60)
    a=p.parse_args()
    if not 1<=a.steps<=200:p.error('Preview limited to 200 control steps')
    a.out.mkdir(parents=True,exist_ok=False);start=time.monotonic()
    report={'status':'running','robot_demo':False,'preview_steps':a.steps,
            'source_sha256':{n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest()
                             for n in ('scene.py','native.py','material.py','preview_yam.py')}}
    from isaaclab.app import AppLauncher
    app=AppLauncher(headless=True,enable_cameras=True).app
    try:
        import omni.physics.tensors as tensors
        from yam_arena import inspect_embodiment as wrapper
        wrapper._APP=app
        emb=wrapper.YamArenaEmbodiment(task=str(Path(__file__).with_name('scene.py')),
            object_jitter=0.,control_hz=20,cam_width=224,cam_height=224)
        emb._ensure_sim(None)
        import sys
        # The task loader may give scene.py a generated module name. Its hook
        # closure owns the exact runtime, avoiding a second scene import.
        from yam_arena import scene as adapter
        namespace=adapter.task_object.__globals__
        roots,coupling=namespace['ROOTS'],namespace['COUPLING']
        sim=tensors.create_simulation_view('numpy');sim.set_subspace_roots('/')
        barrel=sim.create_rigid_body_view(roots['barrel']);plunger=sim.create_rigid_body_view(roots['plunger'])
        base=emb._base;write=base.scene.write_data_to_sim
        def step_material(*args,**kwargs):
            out=write(*args,**kwargs)
            fb,fp=coupling.advance(np.asarray(barrel.get_transforms())[0],np.asarray(barrel.get_velocities())[0],
                                   np.asarray(plunger.get_transforms())[0],float(base.physics_dt))
            for view,force,torque in ((barrel,fb,coupling.last_contact_torque),(plunger,fp,np.zeros(3))):
                view.apply_forces_and_torques_at_position(force_data=np.asarray(force,np.float32).reshape(1,3),
                    torque_data=np.asarray(torque,np.float32).reshape(1,3),position_data=None,
                    indices=np.array([0],np.uint32),is_global=True)
            return out
        base.scene.write_data_to_sim=step_material
        emb._env.reset()
        coupling.material.reset()
        for i in range(a.steps):
            emb._env.step(emb._ready);coupling.update_surface()
        coupling.material.save(a.out/'material.npz')
        report.update(status='complete',balance=coupling.material.balance(),score=None,
                      note='Unscored integration preview; no manipulation, Dream trial or media evidence.')
    except BaseException as exc:
        report.update(status='failed',error=f'{type(exc).__name__}: {exc}');raise
    finally:
        report['wall_seconds']=time.monotonic()-start
        (a.out/'preview.json').write_text(json.dumps(report,indent=2)+'\n');app.close()


if __name__=='__main__':main()
