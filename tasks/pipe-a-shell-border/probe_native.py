"""First GPU probe: squeeze a real passive slider with a diagnostic force.

The barrel is clamped ONLY for this constitutive/contact test. This is not a
robot demonstration and cannot be submitted. No Dream API is used.
"""
import argparse
import json
import hashlib
from pathlib import Path
import time
import numpy as np


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--seconds',type=float,default=3.)
    parser.add_argument('--force-n',type=float,default=8.)
    args=parser.parse_args()
    if not 0<args.seconds<=10 or not 0<=args.force_n<=20:parser.error('Probe limits: 10 s, 20 N')
    args.out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    report={'status':'running','robot_demo':False,'diagnostic_force_n':args.force_n,
            'source_sha256':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                             for name in ('probe_native.py','native.py','material.py')}}
    from isaacsim import SimulationApp
    app=SimulationApp({'headless':True})
    try:
        from isaacsim.core.api import World
        from pxr import Gf,UsdGeom,UsdPhysics
        import omni.physics.tensors as tensors
        from native import author_dispenser,Coupling,rotation
        world=World(physics_dt=1/480,rendering_dt=1/60,stage_units_in_meters=1.,backend='numpy')
        stage=world.stage
        def body(path,position,size,mass=None,quat=(0.,0.,0.,1.)):
            x=UsdGeom.Xform.Define(stage,path);x.AddTranslateOp().Set(Gf.Vec3d(*position))
            x.AddOrientOp().Set(Gf.Quatd(quat[3],*quat[:3]))
            if mass:
                UsdPhysics.RigidBodyAPI.Apply(x.GetPrim())
                UsdPhysics.MassAPI.Apply(x.GetPrim()).CreateMassAttr(mass)
            c=UsdGeom.Cube.Define(stage,path+'/Shape');c.CreateSizeAttr(1.)
            c.AddScaleOp().Set(Gf.Vec3d(*size));UsdPhysics.CollisionAPI.Apply(c.GetPrim())
        body('/World/Table',(.30,0.,.7375),(.6,.5,.02))
        body('/World/Board',(.30,0.,.749),(.20,.16,.003))
        body('/World/Cake',(.30,0.,.7755),(.18,.14,.05))
        # Tilt the nozzle 45 degrees down. The large barrel and nozzle shoulder
        # remain clear of the cake; the lip starts about 0.1 mm above it.
        q=np.array((np.sin(-np.pi/8),0.,0.,np.cos(-np.pi/8)))
        pos=np.array((.235,-.09,.86));axis=rotation(q)[:,1]
        body('/World/Barrel',pos,(.03,.08,.03),.080,q)
        body('/World/Plunger',pos-axis*.060,(.035,.005,.035),.025,q)
        author_dispenser(stage,'/World/Barrel','/World/Plunger',diagnostic_fixture=True)
        coupling=Coupling();coupling.author_surface(stage)
        stage.GetRootLayer().Export(str(args.out/'initial.usda'))
        world.reset()
        sim=tensors.create_simulation_view('numpy');sim.set_subspace_roots('/')
        barrel=sim.create_rigid_body_view('/World/Barrel')
        plunger=sim.create_rigid_body_view('/World/Plunger')
        trace=[]
        for i in range(int(args.seconds*480)):
            bp=np.asarray(barrel.get_transforms())[0]
            pp=np.asarray(plunger.get_transforms())[0]
            bv=np.asarray(barrel.get_velocities())[0]
            fb,fp=coupling.advance(bp,bv,pp,1/480)
            # Force acts on the ordinary dynamic plunger; no state writes.
            fp+=rotation(bp[3:])[:,1]*(args.force_n if i<args.seconds*240 else 0.)
            for view,force in ((barrel,fb),(plunger,fp)):
                view.apply_forces_and_torques_at_position(force_data=np.asarray(force,dtype=np.float32).reshape(1,3),
                    torque_data=(np.asarray(coupling.last_contact_torque,dtype=np.float32).reshape(1,3)
                                 if view is barrel else None),position_data=None,
                    indices=np.array([0],dtype=np.uint32),is_global=True)
            world.step(render=i%8==0)
            if i%24==0:
                coupling.update_surface()
                trace.append({'t':i/480,'q_m':coupling.last_piston_m,
                              'reaction_n':coupling.last_reaction_n,
                              'emitted_ml':coupling.material.emitted_m3*1e6})
        coupling.material.save(args.out/'material.npz')
        report.update(status='complete',balance=coupling.material.balance(),trace=trace,
                      note='Interpret contact stability and flow; this test never establishes task feasibility.')
    except BaseException as exc:
        report.update(status='failed',error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        report['wall_seconds']=time.monotonic()-started
        (args.out/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
        app.close()


if __name__=='__main__':main()
