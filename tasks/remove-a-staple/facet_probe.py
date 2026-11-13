"""Small flexible-facet paper/staple contact diagnostic; never task evidence.

Native finite-thickness prisms, free steel staple and a physical pocket support.
No pins, scripted release or dynamic pose writes. A native hinge break or25µm
endpoint gap invalidates this coupon before an intact-paper claim is possible.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import time
import traceback
import numpy as np
from facet_paper import coupon_mesh,box_coupon_mesh,box_task_mesh,author_shell,measured_surface,cooked_hull_geometry,ShellMaterial
from paper import PaperMesh
from contact_guard import PaperWireCrossingGuard


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seconds',type=float,default=.1)
    p.add_argument('--dt',type=float,default=.0001)
    p.add_argument('--full-size-candidate',action='store_true',help='Use both established210×148mm sheets and the real support/staple/remover scene')
    p.add_argument('--recenter-at-paper-diagnostic',action='store_true',help='Rigidly translate the entire full scene near zero to diagnose float32 position quantization')
    p.add_argument('--primitive-box-panels',action='store_true')
    p.add_argument('--no-staple',action='store_true')
    p.add_argument('--separated-free-fall-diagnostic',action='store_true',help='No support; separate sheets by20mm to isolate unloaded hinge behavior')
    p.add_argument('--external-forces-every-iteration',action='store_true')
    p.add_argument('--velocity-iterations',type=int,choices=(1,4,32),default=4)
    p.add_argument('--position-iterations',type=int,choices=(32,64,128),default=128)
    p.add_argument('--wire-velocity-iterations',type=int,choices=(1,4,32),default=4,
                   help='Separate explicit wire control; connected islands use the highest requested count')
    args=p.parse_args()
    if not .001<=args.seconds<=.2 or not .000025<=args.dt<=.001:p.error('Bounded contact coupon only')
    if args.full_size_candidate and (not args.primitive_box_panels or args.separated_free_fall_diagnostic):p.error('Full-size candidate requires box panels and the supported scene')
    if args.recenter_at_paper_diagnostic and not args.full_size_candidate:p.error('Recentering diagnostic requires the full-size scene')
    if args.separated_free_fall_diagnostic and not args.no_staple:p.error('Separated free fall requires --no-staple')
    args.out.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    record=dict(schema='paper-facet-coupon-v1',complete=False,robot_demo=False,task_score=None,
        no_staple=args.no_staple,dt=args.dt,seconds=args.seconds,samples=[],completed_steps=0,phase='launch',
        separated_free_fall_diagnostic=args.separated_free_fall_diagnostic,
        external_forces_every_iteration=args.external_forces_every_iteration,
        position_iterations=args.position_iterations,velocity_iterations=args.velocity_iterations,wire_velocity_iterations=args.wire_velocity_iterations,
        primitive_box_panels=args.primitive_box_panels,full_size_candidate=args.full_size_candidate,
        source_sha256={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                       for name in ('facet_probe.py','facet_paper.py','native_paper.py','contact_guard.py')})
    app=sim=cache=stage=None;attached=False
    try:
        from isaaclab.app import AppLauncher
        app=AppLauncher(headless=True,enable_cameras=False).app
        from pxr import Gf,Usd,UsdGeom,UsdPhysics,PhysxSchema,UsdUtils
        import omni.physics.tensors as tensors
        from omni.physx import get_physx_interface,get_physx_simulation_interface
        from native_paper import author_staple,update_staple,measured_wire_segments
        physics=get_physx_interface();sim=get_physx_simulation_interface()
        cache=UsdUtils.StageCache.Get();stage=Usd.Stage.CreateInMemory();cache.Insert(stage)
        sid=cache.GetId(stage).ToLongInt();record['phase']='build'
        UsdGeom.SetStageMetersPerUnit(stage,1.);UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.z)
        scene=UsdPhysics.Scene.Define(stage,'/physicsScene')
        scene.CreateGravityDirectionAttr(Gf.Vec3f(0.,0.,-1.));scene.CreateGravityMagnitudeAttr(9.80665)
        ps=PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim());ps.CreateSolverTypeAttr('TGS')
        ps.CreateEnableGPUDynamicsAttr(False);ps.CreateBroadphaseTypeAttr('MBP');ps.CreateEnableCCDAttr(True)
        ps.CreateEnableExternalForcesEveryIterationAttr(args.external_forces_every_iteration)
        material=ShellMaterial();record['paper_material']=asdict(material)
        if args.full_size_candidate:
            from full_scene import build_scene,SHEET_CENTRES
            metadata=build_scene(stage,include_papers=False,reset_profile='pocket-support-candidate',mesh_profile='clearance-candidate')
            origins=[(*xy,metadata['reset_layout']['paper_centres_z'][i]) for i,xy in enumerate(SHEET_CENTRES)]
            staple=metadata['staple']
            if args.no_staple:
                stage.RemovePrim(metadata['root']+'/staple');staple=None
            record['physical_layout']=metadata['reset_layout']
            record['paper_size_m']=[.210,.148]
        else:
            # Four flat plates leave the entire folded-leg region clear underneath.
            for name,centre,size in (
                ('front',(0.,-.0065,.005),(.024,.011,.010)),
                ('back',(0.,.0065,.005),(.024,.011,.010)),
                ('left',(-.010,0.,.005),(.004,.002,.010)),
                ('right',(.010,0.,.005),(.004,.002,.010))):
                if args.separated_free_fall_diagnostic:continue
                box=UsdGeom.Cube.Define(stage,'/Support/'+name);box.CreateSizeAttr(1.)
                box.AddTranslateOp().Set(Gf.Vec3d(*centre));box.AddScaleOp().Set(Gf.Vec3f(*size))
                UsdPhysics.CollisionAPI.Apply(box.GetPrim())
                contact=PhysxSchema.PhysxCollisionAPI.Apply(box.GetPrim())
                contact.CreateContactOffsetAttr(.000002);contact.CreateRestOffsetAttr(0.)
            heights=(.03,.05) if args.separated_free_fall_diagnostic else (.01005,.01017)
            origins=[(0.,0.,z) for z in heights]
            staple=None if args.no_staple else author_staple(stage,'/Staple',origin=(0.,0.,.01024))
        shells=[];guards=[]
        for index,origin in enumerate(origins):
            mesh=box_task_mesh(index) if args.full_size_candidate else (box_coupon_mesh() if args.primitive_box_panels else coupon_mesh())
            mesh=PaperMesh(mesh.rest+np.array(origin),mesh.faces,mesh.holes)
            shell=author_shell(stage,f'/Paper{index}',mesh,material,velocity_iterations=args.velocity_iterations,position_iterations=args.position_iterations,primitive_boxes=args.primitive_box_panels)
            shells.append(shell);guards.append(PaperWireCrossingGuard(mesh.faces))
        if staple:
            for path in staple['paths']:
                rb=PhysxSchema.PhysxRigidBodyAPI.Get(stage,path)
                rb.CreateSolverVelocityIterationCountAttr(args.wire_velocity_iterations);rb.CreateMaxDepenetrationVelocityAttr(.05)
                rb.CreateSolverPositionIterationCountAttr(args.position_iterations)
        record['authored_solver_velocity_counts']={path:int(PhysxSchema.PhysxRigidBodyAPI.Get(stage,path).GetSolverVelocityIterationCountAttr().Get())
            for path in ([path for shell in shells for path in shell['bodies']]+(staple['paths'] if staple else []))}
        record['authored_solver_position_counts']={path:int(PhysxSchema.PhysxRigidBodyAPI.Get(stage,path).GetSolverPositionIterationCountAttr().Get())
            for path in ([path for shell in shells for path in shell['bodies']]+(staple['paths'] if staple else []))}
        offset=np.array((-.32,0.,-.7675)) if args.recenter_at_paper_diagnostic else np.zeros(3)
        record['world_coordinate_offset_m']=offset.tolist()
        if args.recenter_at_paper_diagnostic:
            # Coordinate change before attachment, not a physical reset or a
            # constraint. Every paper, steel body, tool and support moves by
            # the same vector; all relative geometry and gravity are unchanged.
            for root in (metadata['root'],'/Paper0','/Paper1'):
                UsdGeom.Xform.Define(stage,root).AddTranslateOp().Set(Gf.Vec3d(*offset))
        record['meshes']=[s['mesh'].audit() for s in shells]
        record['native_break_force_range_n']=[min(h['break_force_n'] for h in shells[0]['model']['hinges']),max(h['break_force_n'] for h in shells[0]['model']['hinges'])]
        stage.GetRootLayer().Export(str(args.out/'initial.usda'))
        record['phase']='attach';sim.attach_stage(sid);attached=True
        view=tensors.create_simulation_view('torch',sid);view.set_subspace_roots('/')
        bodies=[path for shell in shells for path in shell['bodies']]
        rigid=view.create_rigid_body_view(bodies)
        indices=[[list(rigid.prim_paths).index(path) for path in shell['bodies']] for shell in shells]
        if rigid.count!=len(bodies):raise RuntimeError('Incomplete native facet collection')
        steps=round(args.seconds/args.dt);record['phase']='simulate'
        timing={'material_s':0.,'native_simulation_s':0.,'readback_s':0.,'guard_s':0.}
        record['timing']=timing
        for step in range(1,steps+1):
            tick=time.perf_counter()
            if step>1 and staple:update_staple(physics,staple)
            timing['material_s']+=time.perf_counter()-tick;tick=time.perf_counter()
            sim.simulate(args.dt,(step-1)*args.dt);sim.fetch_results();record['completed_steps']=step
            timing['native_simulation_s']+=time.perf_counter()-tick;tick=time.perf_counter()
            poses=rigid.get_transforms().detach().cpu().numpy()
            timing['readback_s']+=time.perf_counter()-tick
            if step==1:
                if args.primitive_box_panels:
                    # Native Cube colliders are analytic boxes, not cooked hulls.
                    # Label this authored shape assertion distinctly from a
                    # native cooked-vertex query.
                    record['analytic_box_shapes']=[dict(body=body,
                        type=stage.GetPrimAtPath(body+'/Shape').GetTypeName(),
                        scale=list(stage.GetPrimAtPath(body+'/Shape').GetAttribute('xformOp:scale').Get()))
                        for shell in shells for body in shell['bodies']]
                    if not all(row['type']=='Cube' and abs(row['scale'][2]-material.thickness_m)<1e-10
                               for row in record['analytic_box_shapes']):
                        raise RuntimeError('Authored analytic paper shape differs from declared thickness')
                else:
                    try:
                        record['cooked_hulls']=[cooked_hull_geometry(shell,stage) for shell in shells]
                        record['cooked_hulls_verified']=all(abs(row[key]-material.thickness_m)<=1e-6
                            for row in record['cooked_hulls'] for key in ('minimum_thickness_m','maximum_thickness_m'))
                    except Exception as error:
                        record['cooked_hulls_verified']=False
                        record['cooked_hull_query_error']=f'{type(error).__name__}: {error}'
                    if not record['cooked_hulls_verified']:
                        raise RuntimeError('Native paper collision thickness is unverified or differs from100micrometres')
                masses=rigid.get_masses().detach().cpu().numpy().reshape(-1)
                record['native_mass_relative_error']=max(float(np.max(np.abs(masses[ids]/shell['model']['masses']-1))) for shell,ids in zip(shells,indices))
                if record['native_mass_relative_error']>1e-4:raise RuntimeError('Native facet masses differ from paper mass')
            tick=time.perf_counter()
            segments=measured_wire_segments(physics,staple) if staple else None
            points=[];checks=[]
            for shell,ids,guard in zip(shells,indices,guards):
                nodes,continuity=measured_surface(shell,poses[ids]);points.append(nodes)
                crossing=guard.update(nodes,segments) if staple else {'valid':True}
                checks.append(dict(continuity=continuity,wire_crossing=crossing))
            timing['guard_s']+=time.perf_counter()-tick
            valid=all(x['continuity']['valid'] and x['wire_crossing']['valid'] for x in checks)
            if step==1 or step%max(1,round(.002/args.dt))==0 or step==steps or not valid:
                record['samples'].append(dict(step=step,time_s=step*args.dt,checks=checks,
                    paper_centroids_m=[x.mean(0).tolist() for x in points],
                    maximum_facet_speed_m_s=float(np.linalg.norm(rigid.get_velocities().detach().cpu().numpy()[:,:3],axis=1).max())))
            if not valid:
                record['first_failure']=record['samples'][-1]
                np.savez_compressed(args.out/'failure-geometry.npz',facet_poses=poses,
                    paper0=points[0],paper1=points[1],wire_segments=segments if staple else np.empty((0,2,3)))
                break
        else:record['complete']=True
        record['phase']='finished';record['interpretation']='Unscored material/contact diagnostic; robot extraction and task success remain unverified.'
        np.savez_compressed(args.out/'final-facet-poses.npz',poses=poses)
    except BaseException as error:
        record.update(error=f'{type(error).__name__}: {error}',traceback=traceback.format_exc());raise
    finally:
        record['wall_seconds']=time.monotonic()-started
        (args.out/'facet-probe.json').write_text(json.dumps(record,indent=2)+'\n')
        if attached:sim.detach_stage()
        if cache and stage:cache.Erase(stage)
        if app:app.close()


if __name__=='__main__':main()
