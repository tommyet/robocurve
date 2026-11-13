"""Isolate the D6 spoke spring in one dimension, with a known 700 N load.

A diagnostic gravity field supplies the constant axial load to a 13.125 g body.
This is a unit/constraint check, not a realistic task scene or robot evidence.
"""
import argparse,json,math,time,traceback
from pathlib import Path
import numpy as np
from mechanics import WheelSpec


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--axis',choices=('distance','transX'),default='distance')
    p.add_argument('--dt',type=float,default=.0001);p.add_argument('--seconds',type=float,default=1.)
    a=p.parse_args()
    if not .00001<=a.dt<=.001 or not .2<=a.seconds<=2:p.error('Bounded diagnostic only')
    a.out.mkdir(parents=True,exist_ok=False);start=time.monotonic()
    s=WheelSpec();mass=.42/32
    anchor=np.array((s.hub_flange_radius_m*math.cos(s.cross_angle_rad),s.hub_flange_radius_m*math.sin(s.cross_angle_rad),s.hub_half_width_m))
    L=float(np.linalg.norm(np.array((s.rim_radius_m,0.,0.))-anchor));k=s.spoke_modulus_pa*math.pi*(s.spoke_diameter_m/2)**2/L
    rest=L-s.baseline_tension_n/k;shortening=.25*s.nipple_pitch_m_per_turn
    r={'kind':'native_d6_spring_unit_check','complete':False,'axis':a.axis,'dt':a.dt,'seconds':a.seconds,'mass_kg':mass,'constant_load_n':s.baseline_tension_n,
       'stiffness_n_m':k,'damping_ns_m':100.,'initial_rest_m':rest,'expected_baseline_x_m':L,'expected_final_x_m':L-shortening,'samples':[],'phase':'launch'}
    from isaaclab.app import AppLauncher
    app=AppLauncher(headless=True,enable_cameras=False).app
    from pxr import Gf,Usd,UsdGeom,UsdPhysics,UsdUtils,PhysxSchema,Sdf
    from omni.physx import get_physx_interface,get_physx_simulation_interface
    cache=UsdUtils.StageCache.Get();stage=Usd.Stage.CreateInMemory();cache.Insert(stage);sim=get_physx_simulation_interface();physics=get_physx_interface();attached=False
    try:
        r['phase']='build';UsdGeom.SetStageMetersPerUnit(stage,1.)
        scene=UsdPhysics.Scene.Define(stage,'/physicsScene');scene.CreateGravityDirectionAttr(Gf.Vec3f(1.,0.,0.));scene.CreateGravityMagnitudeAttr(s.baseline_tension_n/mass)
        ps=PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim());ps.CreateEnableGPUDynamicsAttr(False);ps.CreateBroadphaseTypeAttr('MBP');ps.CreateSolverTypeAttr('TGS')
        b=UsdGeom.Cube.Define(stage,'/Body');b.CreateSizeAttr(.01);b.AddTranslateOp().Set(Gf.Vec3d(L,0.,0.))
        UsdPhysics.RigidBodyAPI.Apply(b.GetPrim());UsdPhysics.MassAPI.Apply(b.GetPrim()).CreateMassAttr(mass);UsdPhysics.CollisionAPI.Apply(b.GetPrim())
        rb=PhysxSchema.PhysxRigidBodyAPI.Apply(b.GetPrim());rb.CreateSleepThresholdAttr(0.);rb.CreateSolverPositionIterationCountAttr(128);rb.CreateSolverVelocityIterationCountAttr(4)
        j=UsdPhysics.Joint.Define(stage,'/Spring');j.CreateBody1Rel().SetTargets([Sdf.Path('/Body')])
        for axis in ('transY','transZ','rotX','rotY','rotZ'):
            lim=UsdPhysics.LimitAPI.Apply(j.GetPrim(),axis);lim.CreateLowAttr(1.);lim.CreateHighAttr(-1.)
        lim=UsdPhysics.LimitAPI.Apply(j.GetPrim(),a.axis);lim.CreateHighAttr(rest)
        if a.axis=='transX':lim.CreateLowAttr(-1.)
        soft=PhysxSchema.PhysxLimitAPI.Apply(j.GetPrim(),a.axis);soft.CreateStiffnessAttr(k);soft.CreateDampingAttr(100.)
        stage.GetRootLayer().Export(str(a.out/'initial.usda'));r['phase']='attach';sim.attach_stage(cache.GetId(stage).ToLongInt());attached=True
        n=round(a.seconds/a.dt);r['phase']='simulate'
        for step in range(n):
            if step==n//2:lim.GetHighAttr().Set(rest-shortening)
            sim.simulate(a.dt,step*a.dt);sim.fetch_results()
            if step%max(1,round(.005/a.dt))==0 or step==n-1:
                t=physics.get_rigidbody_transformation('/Body')
                if not t.get('ret_val'):raise RuntimeError('No live body transform')
                pos=list(map(float,t['position']))
                r['samples'].append({'step':step+1,'position_m':pos,'rest_m':float(lim.GetHighAttr().Get())})
        before=[x for x in r['samples'] if x['step']<=n//2][-1]['position_m'][0]
        after=r['samples'][-1]['position_m'][0]
        r.update(complete=True,baseline_error_m=before-L,final_error_m=after-(L-shortening),observed_displacement_m=after-before,
                 constitutive_pass=bool(abs(before-L)<1e-5 and abs(after-(L-shortening))<1e-5))
    except BaseException as error:r.update(error=f'{type(error).__name__}: {error}',traceback=traceback.format_exc());raise
    finally:
        r['wall_seconds']=time.monotonic()-start;(a.out/'spring-probe.json').write_text(json.dumps(r,indent=2)+'\n')
        if attached:sim.detach_stage()
        cache.Erase(stage);app.close()

if __name__=='__main__':main()
