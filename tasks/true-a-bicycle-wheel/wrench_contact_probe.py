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
import signal
import time
import traceback
import numpy as np
from wheel_scene import build_scene,quat
from thread_coupling import NativeThreadCoupler,TensorNativeIO,rotation,body_paths


def rotation_x(angle):
    c,s=math.cos(angle),math.sin(angle)
    return np.array(((1.,0.,0.),(0.,c,-s),(0.,s,c)))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--dt',type=float,default=.000025)
    p.add_argument('--settle-seconds',type=float,default=.15)
    p.add_argument('--insert-seconds',type=float,default=.15)
    p.add_argument('--turn-seconds',type=float,default=.5)
    p.add_argument('--hold-seconds',type=float,default=.1)
    p.add_argument('--turn-deg',type=float,default=-90.,help='Negative is clockwise tightening viewed from rim')
    p.add_argument('--no-contact',action='store_true')
    a=p.parse_args()
    if not .00001<=a.dt<=.0001 or not 10<=abs(a.turn_deg)<=90:p.error('Use dt .00001–.0001 and |turn|10–90deg')
    durations=(a.settle_seconds,a.insert_seconds,a.turn_seconds,a.hold_seconds)
    if any(not .025<=v<=1. for v in durations):p.error('Each diagnostic phase must be .025–1s')
    a.out.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    report={'kind':'wrench_contact_fixture','complete':False,'robot_demo':False,'score':None,
            'negative_control':a.no_contact,'dt':a.dt,'commanded_wrench_turn_deg':a.turn_deg,'samples':[]}
    report.update(phase_seconds=dict(zip(('settle','insert','turn','hold'),durations)),completed_steps=0)
    def save():
        report['wall_seconds']=time.monotonic()-started
        temp=a.out/'wrench-probe.json.tmp';temp.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        temp.replace(a.out/'wrench-probe.json')
    def interrupted(signum,frame):raise RuntimeError('Interrupted by '+signal.Signals(signum).name)
    handlers={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    for sig in handlers:signal.signal(sig,interrupted)
    save()
    from isaaclab.app import AppLauncher
    app=AppLauncher(headless=True,enable_cameras=False).app
    from pxr import Gf,PhysxSchema,Usd,UsdGeom,UsdPhysics,UsdUtils
    from omni.physx import get_physx_interface,get_physx_simulation_interface
    import omni.physics.tensors as tensors
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
        sim.attach_stage(stage_id);attached=True
        sim.simulate(a.dt,0.);sim.fetch_results();report['completed_steps']=1
        view=tensors.create_simulation_view('torch',stage_id);view.set_subspace_roots('/')
        io=TensorNativeIO(view,body_paths(metadata));coupling=NativeThreadCoupler(stage_id,metadata,native_io=io)
        steps=round(sum(durations)/a.dt);start_turn=None;center=frame=None;checkpoint=time.monotonic()
        for step in range(1,steps):
            t=step*a.dt
            if center is None and t>=a.settle_seconds:
                io.begin_step();center,R=io.frame(target['nipple_path']);center=center.copy();frame=R[:,[1,2,0]]
                if a.no_contact:center=center+.040*R[:,0]
                start_turn=coupling.last[0]['turns']
            if center is not None:
                # A diagnostic fixture follows the settled measured nipple
                # frame, then inserts slowly and rotates. This tests contact
                # mechanics, not perception or robot task feasibility.
                insertion=np.clip((t-a.settle_seconds)/a.insert_seconds,0.,1.)
                turn=np.clip((t-a.settle_seconds-a.insert_seconds)/a.turn_seconds,0.,1.)
                angle=math.radians(a.turn_deg)*(3*turn*turn-2*turn**3)
                R=frame@np.array(((math.cos(angle),-math.sin(angle),0.),(math.sin(angle),math.cos(angle),0.),(0.,0.,1.)))
                pos=center-frame[:,1]*(.012*(1-insertion))
                position_op.Set(Gf.Vec3d(*map(float,pos)))
                x,y,z,w=map(float,quat(R));orientation_op.Set(Gf.Quatf(w,x,y,z))
            coupling.before_step();sim.simulate(a.dt,t);sim.fetch_results()
            report['completed_steps']=step+1
            if step%max(1,round(.02/a.dt))==0 or step==steps-1:
                report['samples'].append({'step':step+1,'t':t+a.dt,'thread0':dict(coupling.last[0])})
                if time.monotonic()-checkpoint>=5.:save();checkpoint=time.monotonic()
        measured=(coupling.last[0]['turns']-start_turn)*360
        report['measured_tightening_turn_deg']=measured
        report['measured_nipple_turn_deg']=measured*coupling.spec.tightening_sign
        report['contact_response_observed']=bool(abs(measured)>.1)
        report['expected_response_pass']=bool(abs(measured)<=.1 if a.no_contact else measured>=5.)
        report['complete']=True
        report['interpretation']='Inspect measured torque/angle and repeat convergence; complete means executed, not full task feasibility.'
        stage.GetRootLayer().Export(str(a.out/'final-authored-parameters.usda'))
    except BaseException as error:
        report.update(error=f'{type(error).__name__}: {error}',traceback=traceback.format_exc());raise
    finally:
        save()
        if attached:sim.detach_stage()
        cache.Erase(stage);app.close()
        for sig,handler in handlers.items():signal.signal(sig,handler)


if __name__=='__main__':main()
