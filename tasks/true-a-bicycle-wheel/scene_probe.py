"""Bounded full-wheel settling with live thread coupling; no robot or score.

All 130 dynamic bodies and native wheel joints remain physical. The first native
step initializes tensor readback; every following step applies measured thread
reaction and shortening. Checkpoints preserve evidence if the wall cap interrupts.
"""
import argparse
import hashlib
import json
from pathlib import Path
import signal
import time
import traceback
import numpy as np
from wheel_scene import build_scene
from mechanics import RESET_PROFILES, starting_turn_errors
from thread_coupling import NativeThreadCoupler,TensorNativeIO,rotation,body_paths


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--dt',type=float,default=.000025)
    p.add_argument('--seconds',type=float,default=.1)
    p.add_argument('--reset-profile',choices=RESET_PROFILES,default='four-defect-reference')
    p.add_argument('--nipple-flat-phase-deg',type=float,choices=(0.,45.),default=0.)
    p.add_argument('--wheel-clocking-deg',type=float,choices=(0.,10.,20.,50.),default=0.)
    p.add_argument('--solver-position-iterations',type=int,choices=(16,32,64,128),default=128)
    p.add_argument('--gpu-physics',action='store_true',help='Compare native GPU rigid physics with the CPU reference')
    p.add_argument('--external-forces-every-iteration',action='store_true',help='Match the YAM TGS external-force integration option; diagnostic only')
    p.add_argument('--freeze-thread-diagnostic',action='store_true',help='No runtime material writes/lead torque; isolates native assembly')
    args=p.parse_args()
    if not .00001<=args.dt<=.0001 or not .025<=args.seconds<=2.:
        p.error('Use 0.00001 <= dt <= 0.0001 and 0.025 <= seconds <= 2')
    args.out.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    record={'schema':'native-wheel-scene-diagnostic-v2','complete':False,'calibrated':False,
            'evidence_type':'Native full scene with live thread coupling; no robot or task score',
            'dt':args.dt,'seconds':args.seconds,'samples':[],'completed_steps':0,'phase':'launch',
            'solver_position_iterations':args.solver_position_iterations,
            'reset_profile':args.reset_profile,'nipple_flat_phase_deg':args.nipple_flat_phase_deg,'wheel_clocking_deg':args.wheel_clocking_deg,
            'initial_turn_offsets':starting_turn_errors(profile=args.reset_profile).tolist(),
            'frozen_material_diagnostic':args.freeze_thread_diagnostic,
            'gpu_physics':args.gpu_physics,
            'external_forces_every_iteration':args.external_forces_every_iteration,
            'first_step':'Initializes native tensor state; authored spring rest lengths/friction already present, lead torque begins on step2.',
            'source_sha256':{n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest()
                             for n in ('scene_probe.py','wheel_scene.py','native_probe.py','thread_coupling.py','mechanics.py','integrity.py','momentum.py')}}
    def save():
        record['wall_seconds']=time.monotonic()-started
        temporary=args.out/'scene-diagnostic.json.tmp'
        temporary.write_text(json.dumps(record,indent=2,allow_nan=False)+'\n')
        temporary.replace(args.out/'scene-diagnostic.json')
    def interrupted(signum,frame):raise RuntimeError('Interrupted by '+signal.Signals(signum).name)
    app=sim=stage=cache=None;attached=False;handlers={};save()
    try:
        for sig in (signal.SIGTERM,signal.SIGINT):
            handlers[sig]=signal.getsignal(sig);signal.signal(sig,interrupted)
        from isaaclab.app import AppLauncher
        app=AppLauncher(headless=True,enable_cameras=False).app
        from pxr import Gf,PhysxSchema,Usd,UsdGeom,UsdPhysics,UsdUtils
        from omni.physx import get_physx_simulation_interface
        import omni.physics.tensors as tensors
        sim=get_physx_simulation_interface();cache=UsdUtils.StageCache.Get()
        stage=Usd.Stage.CreateInMemory();cache.Insert(stage);stage_id=cache.GetId(stage).ToLongInt()
        record['phase']='build'
        scene=UsdPhysics.Scene.Define(stage,'/physicsScene')
        scene.CreateGravityDirectionAttr(Gf.Vec3f(0.,0.,-1.));scene.CreateGravityMagnitudeAttr(9.80665)
        phys=PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
        phys.CreateSolverTypeAttr('TGS');phys.CreateEnableGPUDynamicsAttr(args.gpu_physics)
        phys.CreateBroadphaseTypeAttr('GPU' if args.gpu_physics else 'MBP');phys.CreateEnableCCDAttr(not args.gpu_physics)
        phys.CreateEnableExternalForcesEveryIterationAttr(args.external_forces_every_iteration)
        if args.gpu_physics:
            import carb.settings
            carb.settings.get_settings().set_bool('/physics/suppressReadback',True)
            carb.settings.get_settings().set_int('/physics/cudaDevice',0)
        table=UsdGeom.Cube.Define(stage,'/Bench');table.CreateSizeAttr(1.)
        table.AddTranslateOp().Set(Gf.Vec3d(.3,0.,.7275));table.AddScaleOp().Set(Gf.Vec3f(1.,1.,.04))
        UsdPhysics.CollisionAPI.Apply(table.GetPrim())
        PhysxSchema.PhysxCollisionAPI.Apply(table.GetPrim()).CreateContactOffsetAttr(.000002)
        metadata=build_scene(stage,reset_profile=args.reset_profile,nipple_flat_phase_rad=np.deg2rad(args.nipple_flat_phase_deg),wheel_clocking_rad=np.deg2rad(args.wheel_clocking_deg))
        for path in body_paths(metadata):
            rb=PhysxSchema.PhysxRigidBodyAPI.Get(stage,path)
            rb.CreateSolverPositionIterationCountAttr(args.solver_position_iterations)
        stage.GetRootLayer().Export(str(args.out/'initial.usda'))
        cache_xf=UsdGeom.XformCache();authored={}
        for path in body_paths(metadata):
            matrix=cache_xf.GetLocalToWorldTransform(stage.GetPrimAtPath(path))
            q=matrix.ExtractRotationQuat()
            authored[path]=(np.asarray(matrix.ExtractTranslation(),float),rotation([*map(float,q.GetImaginary()),float(q.GetReal())]))
        hp,hR=authored[metadata['hub_path']];audit=[]
        for i,s in enumerate(metadata['spokes']):
            ip,iR=authored[s['inner_path']];op,oR=authored[s['outer_path']];rp,rR=authored[s['rim_path']]
            anchor=hp+hR@np.asarray(s['hub_anchor_local_m']);end=rp+rR@np.asarray(s['rim_anchor_local_m'])
            half=s['half_rod_length_m'];gap=(op-oR[:,0]*half/2)-(ip+iR[:,0]*half/2)
            axial=float(gap@iR[:,0]);rest=s['rest_target_attribute'].Get()+s['rest_target_origin_m']
            audit.append({'spoke':i,'hub_joint_gap_m':float(np.linalg.norm(ip-iR[:,0]*half/2-anchor)),
                'rim_joint_gap_m':float(np.linalg.norm(op+oR[:,0]*half/2-end)),
                'mid_joint_gap_m':gap.tolist(),'axial_extension_m':s['rest_target_origin_m']+axial-rest,
                'initial_tension_n':max(0.,s['rest_target_origin_m']+axial-rest)*s['stiffness_n_per_m'],
                'axis_alignment':float(iR[:,0]@oR[:,0])})
        record['authored_spoke_constraint_audit']=audit
        if any(max(x['hub_joint_gap_m'],x['rim_joint_gap_m'],np.linalg.norm(x['mid_joint_gap_m']))>1e-6 for x in audit):
            raise RuntimeError('Authored spoke endpoint or midpoint joint mismatch')
        record['phase']='attach';sim.attach_stage(stage_id);attached=True
        sim.simulate(args.dt,0.);sim.fetch_results();record['completed_steps']=1
        tensor=tensors.create_simulation_view('torch',stage_id);tensor.set_subspace_roots('/')
        io=TensorNativeIO(tensor,body_paths(metadata));record['native_body_count']=io.view.count
        record['native_body_paths']=io.paths
        from momentum import MomentumAudit
        momentum=MomentumAudit(io.view,metadata['wrench_path'])
        record['native_mass_properties']=momentum.properties()
        if io.view.count!=130:raise RuntimeError('Expected 130 native wheel/wrench bodies')
        coupling=NativeThreadCoupler(stage_id,metadata,native_io=io)
        timings={'material_s':0.,'native_simulation_s':0.,'observation_s':0.,'checkpoint_s':0.}
        record['timing']=timings
        steps=round(args.seconds/args.dt);record['phase']='simulate';last_checkpoint=time.monotonic()
        for step in range(1,steps+1):
            if step>1:
                tick=time.perf_counter()
                coupling.before_step(frozen_material_diagnostic=args.freeze_thread_diagnostic)
                timings['material_s']+=time.perf_counter()-tick;tick=time.perf_counter()
                sim.simulate(args.dt,(step-1)*args.dt);sim.fetch_results()
                timings['native_simulation_s']+=time.perf_counter()-tick
            record['completed_steps']=step
            if step==1 or step%max(1,round(.001/args.dt))==0 or step==steps:
                tick=time.perf_counter()
                io.begin_step();hp,hR=io.frame(metadata['hub_path']);wp,_=io.frame(metadata['wrench_path'])
                points=np.array([io.frame(s['rim_path'])[0] for s in metadata['spokes']]);local=(points-hp)@hR
                if not np.isfinite(local).all() or np.max(np.linalg.norm(local,axis=1))>.35:
                    raise RuntimeError('Native rim escaped wheel bounds')
                state=coupling.observation_for_assessor()
                record['samples'].append({'step':step,'time_s':step*args.dt,'hub_position_m':hp.tolist(),
                    'rim_positions_m':points.tolist(),'rim_positions_in_hub_m':local.tolist(),
                    'native_body_poses':io.transforms.tolist(),
                    'lateral_runout_m':float(np.ptp(local[:,2])),'wrench_position_m':wp.tolist(),
                    'thread_state':state,'momentum':momentum.measure(io.transforms,hp)})
                timings['observation_s']+=time.perf_counter()-tick
                if time.monotonic()-last_checkpoint>=5.:
                    tick=time.perf_counter();save();last_checkpoint=time.monotonic()
                    timings['checkpoint_s']+=time.perf_counter()-tick
        record['rim_integrity']=coupling.audit_integrity()
        record['complete']=True
        record['native_parameter_updates']={'attempted':coupling.parameters.attempts,'written':coupling.parameters.writes,
            'skipping_rule':'Only float32-identical values; no material tolerance or update decimation'}
        record['interpretation']='Execution only; assess geometry, tension and uncommanded thread drift before advancing.'
        stage.GetRootLayer().Export(str(args.out/'final-authored-parameters.usda'))
    except BaseException as error:
        record.update(error=f'{type(error).__name__}: {error}',traceback=traceback.format_exc());raise
    finally:
        save()
        if attached:sim.detach_stage()
        if cache and stage:cache.Erase(stage)
        if app:app.close()
        for sig,handler in handlers.items():signal.signal(sig,handler)


if __name__=='__main__':main()
