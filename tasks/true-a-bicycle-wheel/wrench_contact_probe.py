"""Diagnostic wrench/nipple contact test. Kinematic test fixture, NOT a robot demo.

After settling, the fixture inserts the actual open-slot wrench onto nipple0 and
rotates it. Only native collisions can rotate the nipple; the thread coupler
reads measured nipple angle. A no-contact control moves the wrench 40mm beyond
the nipple along its axis. No wheel, spoke or nipple pose is commanded.
"""
import argparse
import json
import math
from pathlib import Path
import time
import numpy as np
from wheel_scene import build_scene,quat
from thread_coupling import NativeThreadCoupler,rotation


def rotation_x(angle):
    c,s=math.cos(angle),math.sin(angle)
    return np.array(((1.,0.,0.),(0.,c,-s),(0.,s,c)))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--dt',type=float,default=.001)
    p.add_argument('--turn-deg',type=float,default=90.)
    p.add_argument('--no-contact',action='store_true')
    a=p.parse_args()
    if not .0001<=a.dt<=.001 or not 10<=abs(a.turn_deg)<=90:p.error('Use dt .0001–.001 and |turn|10–90deg')
    a.out.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    report={'kind':'wrench_contact_fixture','complete':False,'robot_demo':False,'score':None,
            'negative_control':a.no_contact,'dt':a.dt,'commanded_wrench_turn_deg':a.turn_deg,'samples':[]}
    from isaaclab.app import AppLauncher
    app=AppLauncher(headless=True,enable_cameras=False).app
    from pxr import Gf,PhysxSchema,Usd,UsdGeom,UsdPhysics,UsdUtils
    from omni.physx import get_physx_interface,get_physx_simulation_interface
    sim,physics=get_physx_simulation_interface(),get_physx_interface()
    cache=UsdUtils.StageCache.Get();stage=Usd.Stage.CreateInMemory();cache.Insert(stage)
    stage_id=cache.GetId(stage).ToLongInt();attached=False
    try:
        scene=UsdPhysics.Scene.Define(stage,'/physicsScene');scene.CreateGravityDirectionAttr(Gf.Vec3f(0.,0.,-1.));scene.CreateGravityMagnitudeAttr(9.80665)
        ps=PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim());ps.CreateSolverTypeAttr('TGS');ps.CreateEnableGPUDynamicsAttr(False);ps.CreateBroadphaseTypeAttr('MBP');ps.CreateEnableCCDAttr(True)
        table=UsdGeom.Cube.Define(stage,'/Bench');table.CreateSizeAttr(1.);table.AddTranslateOp().Set(Gf.Vec3d(.3,0.,.7275));table.AddScaleOp().Set(Gf.Vec3f(1.,1.,.04));UsdPhysics.CollisionAPI.Apply(table.GetPrim())
        metadata=build_scene(stage);wrench_prim=stage.GetPrimAtPath(metadata['wrench_path'])
        UsdPhysics.RigidBodyAPI(wrench_prim).CreateKinematicEnabledAttr(True)
        ops=UsdGeom.Xform(wrench_prim).GetOrderedXformOps()
        position_op=next(op for op in ops if op.GetOpType()==UsdGeom.XformOp.TypeTranslate)
        orientation_op=next(op for op in ops if op.GetOpType()==UsdGeom.XformOp.TypeOrient)
        target=metadata['spokes'][0]
        authored=UsdGeom.XformCache().GetLocalToWorldTransform(stage.GetPrimAtPath(target['nipple_path']))
        q=authored.ExtractRotationQuat();v=q.GetImaginary()
        initial_R=rotation([*map(float,v),float(q.GetReal())]);initial_frame=initial_R[:,[1,2,0]]
        initial_center=np.asarray(authored.ExtractTranslation(),float)
        if a.no_contact:initial_center+=.040*initial_R[:,0]
        position_op.Set(Gf.Vec3d(*map(float,initial_center-initial_frame[:,1]*.012)))
        x,y,z,w=map(float,quat(initial_frame));orientation_op.Set(Gf.Quatf(w,x,y,z))
        sim.attach_stage(stage_id);attached=True;coupling=NativeThreadCoupler(stage_id,metadata)
        steps=round(5/a.dt);start_turn=None;center=frame=None
        for step in range(steps):
            t=step*a.dt
            if center is None and t>=1.:
                native=physics.get_rigidbody_transformation(target['nipple_path'])
                if not native.get('ret_val'):raise RuntimeError('Missing nipple transform')
                center=np.asarray(native['position'],float)
                R=rotation(native['rotation']);frame=R[:,[1,2,0]]
                if a.no_contact:center=center+.040*R[:,0]
                start_turn=coupling.last[0]['turns']
            if center is not None:
                # A diagnostic fixture follows the settled measured nipple
                # frame, then inserts slowly and rotates. This tests contact
                # mechanics, not perception or robot task feasibility.
                insertion=np.clip((t-1.)/1.,0.,1.)
                turn=np.clip((t-2.)/2.,0.,1.)
                angle=math.radians(a.turn_deg)*(3*turn*turn-2*turn**3)
                R=frame@np.array(((math.cos(angle),-math.sin(angle),0.),(math.sin(angle),math.cos(angle),0.),(0.,0.,1.)))
                pos=center-frame[:,1]*(.012*(1-insertion))
                position_op.Set(Gf.Vec3d(*map(float,pos)))
                x,y,z,w=map(float,quat(R));orientation_op.Set(Gf.Quatf(w,x,y,z))
            coupling.before_step();sim.simulate(a.dt,t);sim.fetch_results()
            if step%max(1,round(.02/a.dt))==0 or step==steps-1:
                report['samples'].append({'step':step+1,'t':t+a.dt,'thread0':dict(coupling.last[0])})
        measured=(coupling.last[0]['turns']-start_turn)*360
        report['measured_nipple_turn_deg']=measured
        report['contact_response_observed']=bool(abs(measured)>(5. if not a.no_contact else .1))
        report['complete']=True
        report['interpretation']='Inspect measured torque/angle and repeat convergence; complete means executed, not full task feasibility.'
        stage.GetRootLayer().Export(str(a.out/'final.usda'))
    except BaseException as error:
        report['error']=f'{type(error).__name__}: {error}';raise
    finally:
        report['wall_seconds']=time.monotonic()-started
        (a.out/'wrench-probe.json').write_text(json.dumps(report,indent=2)+'\n')
        if attached:sim.detach_stage()
        cache.Erase(stage);app.close()


if __name__=='__main__':main()
