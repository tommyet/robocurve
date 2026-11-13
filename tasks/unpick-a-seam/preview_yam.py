"""Unscored YAM seam diagnostic with every-substep material/contact audits.

Ordinary ready targets or a frozen joint plan drive the robot. Native state
feeds assessment and force-qualified cutting, never the action policy.
"""
import argparse
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import time
import traceback
import numpy as np

HERE=Path(__file__).resolve().parent


def array(value):
    return getattr(value,'torch',value).detach().cpu().numpy().copy()


def rotation(q):
    x,y,z,w=np.asarray(q,float)/np.linalg.norm(q)
    return np.array(((1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),
                     (2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)),
                     (2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y))))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--steps',type=int,default=20)
    p.add_argument('--plan',type=Path,help='Frozen action14 JSON produced by plan.py')
    p.add_argument('--physics-hz',type=int,choices=(960,1920,3840),default=960)
    p.add_argument('--coarse-thread',action='store_true')
    p.add_argument('--hole-mesh-spacing',type=float)
    p.add_argument('--contact-refinement',choices=('baseline','iterations','speculative','combined'),default='baseline')
    a=p.parse_args()
    if not 1<=a.steps<=2400:p.error('Use 1 to 2400 control steps')
    if a.plan is None and a.steps>200:p.error('Ready-hold preview limited to 200 steps')
    actions=None
    if a.plan is not None:
        plan=json.loads(a.plan.read_text())
        if plan.get('control_hz')!=20 or plan.get('no_object_feedback') is not True:
            raise ValueError('Expected a frozen 20 Hz joint plan without object feedback')
        actions=np.asarray([row['action14'] for row in plan['frames']],float)
        if actions.ndim!=2 or actions.shape[1]!=14 or not np.isfinite(actions).all() or len(actions)<a.steps:
            raise ValueError('Incomplete/invalid fixed action sequence')
    from native_cloth import ContactRefinement
    import runtime_config
    refined=a.contact_refinement in ('iterations','combined')
    settings=ContactRefinement(a.contact_refinement in ('speculative','combined'),4 if refined else 1,4 if refined else 1)
    runtime_config.CONFIG=runtime_config.SeamRuntime(
        .0004 if a.coarse_thread else .0002,.0008 if a.coarse_thread else .0006,
        a.hole_mesh_spacing,a.physics_hz,settings)
    a.out.mkdir(parents=True,exist_ok=False)
    frozen=a.out/'task-source';frozen.mkdir()
    hashes={}
    for source in HERE.glob('*.py'):
        compile(source.read_bytes(),str(source),'exec')
        hashes[source.name]=hashlib.sha256(source.read_bytes()).hexdigest()
        shutil.copyfile(source,frozen/source.name)
    if a.plan is not None:
        shutil.copyfile(a.plan,frozen/'fixed-plan.json')
        hashes['fixed-plan.json']=hashlib.sha256(a.plan.read_bytes()).hexdigest()
    started=time.monotonic()
    report={'status':'running','robot_demo':False,'score':None,'dream_requests':0,
            'requested_steps':a.steps,'completed_steps':0,'control_hz':20,
            'runtime':asdict(runtime_config.CONFIG),'source_sha256':hashes,
            'policy':'ordinary ready targets' if actions is None else 'frozen joint targets; no object feedback'}
    app=video=trace=emb=None
    def save():
        report['wall_seconds']=time.monotonic()-started
        (a.out/'preview.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    try:
        from isaaclab.app import AppLauncher
        app=AppLauncher(headless=True,enable_cameras=True).app
        import carb
        import torch
        import imageio.v2 as imageio
        from PIL import Image
        import omni.physics.tensors as tensors
        import omni.usd
        from pxr import UsdPhysics
        from yam_arena import inspect_embodiment as wrapper,scene as adapter
        wrapper._APP=app
        adapter.PHYSICS_DT=1/a.physics_hz
        carb.settings.get_settings().set_bool('/physics/disableContactProcessing',False)
        emb=wrapper.YamArenaEmbodiment(task=str(HERE/'scene.py'),object_jitter=0.,
                                      control_hz=20,cam_width=224,cam_height=224)
        emb._ensure_sim(None)
        base=emb._base;stage=omni.usd.get_context().get_stage()
        namespace=adapter.task_object.__globals__
        roots,cloth=namespace['ROOTS'],namespace['MESHES']
        from arena_thread import SPAWNED
        threads=[SPAWNED[f'stitch_{i}'] for i in range(6)]
        from cutting import ThreadCutter,CutParameters,DamageAudit
        from inspection import StrainAudit,inspect_removed_threads
        from contact_audit import ThreadClothAudit,capsule_endpoints
        from native_stitches import sever_contacted_joints
        all_paths=[path for thread in threads for path in thread['bodies']]
        for prim in stage.Traverse():
            if 'Attachment' in prim.GetTypeName():raise RuntimeError('Unexpected attachment in seam scene')
        for path in all_paths:
            if UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath(path)).GetKinematicEnabledAttr().Get():
                raise RuntimeError('Task thread must remain dynamic')
        envroot=roots['ripper_handle'].rsplit('/',1)[0]
        for name in ('cloth_left','cloth_right'):
            prim=stage.GetPrimAtPath(envroot+'/'+name)
            if not prim.HasAPI('OmniPhysicsSurfaceDeformableSimAPI') or prim.HasAPI(UsdPhysics.RigidBodyAPI):
                raise RuntimeError('Cloth is not native surface FEM')
        sim=tensors.create_simulation_view('torch');sim.set_subspace_roots('/')
        blade=sim.create_rigid_body_view(roots['ripper_blade'])
        handle=sim.create_rigid_body_view(roots['ripper_handle'])
        thread_view=sim.create_rigid_body_view(all_paths)
        native_paths=list(thread_view.prim_paths)
        order=np.asarray([native_paths.index(path) for path in all_paths])
        views=[sim.create_surface_deformable_body_view(envroot+'/'+name) for name in ('cloth_left','cloth_right')]
        if blade.count!=1 or handle.count!=1 or any(v.count!=1 for v in views):
            raise RuntimeError('Missing native seam body')
        contact=sim.create_rigid_contact_view([roots['ripper_blade']],filter_patterns=[all_paths],max_contact_data_count=4096)
        if contact.sensor_count!=1 or contact.filter_count!=len(all_paths):
            raise RuntimeError('Blade force matrix does not cover every thread link')
        filter_paths=list(contact.filter_paths)
        if filter_paths and isinstance(filter_paths[0],(list,tuple)):filter_paths=filter_paths[0]
        force_order=np.asarray([filter_paths.index(path) for path in all_paths])
        dt=float(base.physics_dt)
        if abs(dt-1/a.physics_hz)>1e-10:raise RuntimeError('Requested physics timestep was not applied')
        report.update(physics_dt_s=dt,contact_processing_disabled=carb.settings.get_settings().get('/physics/disableContactProcessing'))
        if report['contact_processing_disabled'] is True:raise RuntimeError('Native contact reporting is disabled')
        emb._env.reset()
        # Every following substep, including settling, is audited after reset.
        cutter=ThreadCutter([len(t['bodies']) for t in threads],CutParameters(thread_radius_m=runtime_config.CONFIG.thread_radius_m))
        damage=DamageAudit();strain=[StrainAudit(m.rest,m.faces) for m in cloth]
        crossing=[ThreadClothAudit(m.faces) for m in cloth]
        lengths=np.concatenate([t['lengths'] for t in threads])
        edge_local=np.column_stack((np.full(9,.0005),np.linspace(-.002,.002,9),np.zeros(9)))
        state={'steps':0,'invalid':False,'previous_edge':None,
               'last_physics_step':int(base.sim._physics_step_count),'max_edge_force_n':0.}
        def measured():
            poses=array(thread_view.get_transforms())[order]
            nodes=[array(view.get_simulation_nodal_positions())[0,:len(mesh.rest)] for view,mesh in zip(views,cloth)]
            pose=array(blade.get_transforms())[0];R=rotation(pose[3:])
            return poses,nodes,edge_local@R.T+pose[:3],R[:,0]
        def assess_step(apply_cut=True):
            poses,nodes,edge,normal=measured()
            segments=capsule_endpoints(poses,lengths);t=state['steps']*dt
            for j,points in enumerate(nodes):
                strain[j].update(points,t);crossing[j].update(points,segments,t)
            damage.update(edge if state['previous_edge'] is None else state['previous_edge'],edge,
                          nodes,[m.faces for m in cloth],t)
            state['previous_edge']=edge.copy()
            invalid=bool(damage.crossed_faces or any(s.first_excursion for s in strain) or any(s.first_failure for s in crossing))
            if invalid:
                state['invalid']=True
                if 'first_invalid_substep' not in report:
                    report['first_invalid_substep']=state['steps']
                    np.savez_compressed(a.out/'first-invalid.npz',left=nodes[0],right=nodes[1],
                        thread=poses,left_faces=cloth[0].faces,right_faces=cloth[1].faces,time_s=t)
            if apply_cut and not invalid:
                forces=array(contact.get_contact_force_matrix(dt=dt))[0,force_order]
                state['max_edge_force_n']=max(state['max_edge_force_n'],float(np.max(-forces@normal)))
                sever_contacted_joints(stage,threads,cutter.update(forces,normal,dt))
            state.update(poses=poses,nodes=nodes,segments=segments)
        assess_step(False)
        original_update=base.scene.update
        def after_physics(*args,**kwargs):
            result=original_update(*args,**kwargs)
            count=int(base.sim._physics_step_count)
            if count!=state['last_physics_step']:
                state['last_physics_step']=count;state['steps']+=1;assess_step()
                if state['invalid']:raise RuntimeError('Native seam material/contact validity boundary crossed')
            return result
        base.scene.update=after_physics
        ready=array(emb._ready)[0]
        if actions is not None:
            from yam_arena.constants import SHOULDER,WRIST,GRIPPER,FINGER_OPEN
            limits=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+
                                   [GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
            if np.any(actions<emb._low) or np.any(actions>emb._high) or np.any(np.abs(np.diff(np.vstack((ready,actions)),axis=0))>limits*1.001):
                raise ValueError('Fixed actions exceed ordinary joint/rate limits')
        video=imageio.get_writer(a.out/'preview.mp4',fps=20,codec='libx264',pixelformat='yuv420p',
                                ffmpeg_params=['-movflags','+faststart'],macro_block_size=1)
        trace=gzip.open(a.out/'trace.jsonl.gz','wt')
        def snapshot(step,action):
            rgb=array(base.scene['top_cam'].data.output['rgb'])[0,:,:,:3].astype(np.uint8)
            video.append_data(rgb)
            if step==0:Image.fromarray(rgb).save(a.out/'setup.png')
            row={'step':step,'time_s':step/20,'action14':action.tolist(),'physics_substeps':state['steps'],
                 'handle_pose_xyzw':array(handle.get_transforms())[0].tolist(),
                 'blade_pose_xyzw':array(blade.get_transforms())[0].tolist(),
                 'thread_poses_xyzw':state['poses'].tolist(),'cloth_nodes':[n.tolist() for n in state['nodes']],
                 'cut_events':cutter.events,'invalid':state['invalid']}
            trace.write(json.dumps(row,allow_nan=False)+'\n');trace.flush()
        snapshot(0,ready);save()
        if state['invalid']:raise RuntimeError('Authored seam reset fails material/contact audit')
        for step in range(1,a.steps+1):
            action=ready if actions is None else actions[step-1]
            emb._env.step(torch.as_tensor(action[None],device=base.device,dtype=torch.float32))
            snapshot(step,action);report['completed_steps']=step
            if step%20==0:save()
        if state['steps']!=round(a.steps*a.physics_hz/20):raise RuntimeError('Every-substep audit coverage mismatch')
        pieces=[];start=0
        for t in threads:
            end=start+len(t['lengths']);pieces.append(state['segments'][start:end]);start=end
        removed=inspect_removed_threads(pieces,state['nodes'],[m.faces for m in cloth],radius=runtime_config.CONFIG.thread_radius_m)
        for name in ('top_cam','left_cam','right_cam'):
            Image.fromarray(array(base.scene[name].data.output['rgb'])[0,:,:,:3].astype(np.uint8)).save(a.out/f'final-{name}.png')
        report.update(status='complete',thread_inspection=removed,
                      note='Unscored native robot diagnostic, not full task acceptance evidence.')
    except BaseException as exc:
        report.update(status='failed',error=f'{type(exc).__name__}: {exc}',traceback=traceback.format_exc())
        raise
    finally:
        if 'state' in locals():
            report.update(audited_physics_substeps=state['steps'],maximum_edge_force_n=state['max_edge_force_n'],
                material_invalid=state['invalid'],cut_events=cutter.events,damage_events=damage.events,
                contact_audit=[audit.summary() for audit in crossing],
                strain=[{'maximum_principal_stretch':s.maximum_observed,'first_validity_excursion':s.first_excursion} for s in strain])
        if trace:trace.close()
        if video:video.close()
        save()
        if app:app.close()


if __name__=='__main__':main()
