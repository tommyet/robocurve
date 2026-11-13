"""Bounded YAM/Arena smoke recorder. No task demo, Dream call or scored success.

Smoke mode holds the ordinary ready joint targets. Motion-probe mode replays a
frozen ordinary joint trajectory. Measured cloth/peg geometry is assessor
evidence only and never changes either policy's targets.
"""
import argparse
from dataclasses import fields,is_dataclass
from datetime import datetime,timezone
import gzip
import hashlib
from importlib.metadata import version,PackageNotFoundError
import json
import os
from pathlib import Path
import shutil
import signal
import time
import numpy as np

HERE=Path(__file__).resolve().parent
CONTROL_HZ=20
MAX_SMOKE_STEPS=200


def encode(value):
    if isinstance(value,np.ndarray):
        return value.tolist()
    if isinstance(value,np.generic):
        return value.item()
    if is_dataclass(value):
        return {f.name:encode(getattr(value,f.name)) for f in fields(value)}
    if isinstance(value,dict):
        return {k:encode(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):
        return [encode(v) for v in value]
    return value


def sources():
    result={}
    for p in sorted(HERE.iterdir()):
        if p.suffix in ('.py','.json','.md') or p.name=='LICENSE':
            if p.suffix=='.py':
                compile(p.read_bytes(),str(p),'exec')
            elif p.suffix=='.json':
                json.loads(p.read_text())
            result[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    return result


def package_versions():
    values={}
    for name in ('isaacsim','isaaclab','yam-arena','inspect-robots','inspect-robots-yam','numpy'):
        try:values[name]=version(name)
        except PackageNotFoundError:values[name]=None
    return values


def native_audit(stage,cloth_names,peg_names):
    """Fail closed if a custom asset silently becomes a rigid/proxy object."""
    from pxr import UsdPhysics
    result={'cloth':{},'pegs':{},'attachments':[]}
    for prim in stage.Traverse():
        path=str(prim.GetPath())
        schemas=prim.GetAppliedSchemas()
        if 'Attachment' in prim.GetTypeName() or any('Attachment' in s for s in schemas):
            result['attachments'].append(path)
        for name in cloth_names:
            if path.endswith('/'+name) and 'OmniPhysicsDeformableBodyAPI' in schemas:
                result['cloth'][name]={'path':path,'schemas':list(schemas),
                     'rigid_body':prim.HasAPI(UsdPhysics.RigidBodyAPI),
                     'self_collision':prim.GetAttribute('physxDeformableBody:selfCollision').Get()}
        for name in peg_names:
            if '/'+name+'/' in path:
                entry=result['pegs'].setdefault(name,{'bodies':[],'joints':[],'kinematic_bodies':[]})
                if prim.HasAPI(UsdPhysics.RigidBodyAPI):
                    entry['bodies'].append(path)
                    if UsdPhysics.RigidBodyAPI(prim).GetKinematicEnabledAttr().Get():
                        entry['kinematic_bodies'].append(path)
                if prim.IsA(UsdPhysics.Joint):
                    entry['joints'].append({'path':path,'type':prim.GetTypeName(),
                        'body0':[str(p) for p in prim.GetRelationship('physics:body0').GetTargets()],
                        'body1':[str(p) for p in prim.GetRelationship('physics:body1').GetTargets()]})
    if result['attachments']:
        raise RuntimeError('Unexpected attachment in this attachment-free scene')
    for name in cloth_names:
        item=result['cloth'].get(name)
        if not item or item['rigid_body'] or item['self_collision'] is not True:
            raise RuntimeError('Missing native self-contact cloth: '+name)
    for name in peg_names:
        item=result['pegs'].get(name,{})
        if len(item.get('bodies',[]))!=2 or len(item.get('joints',[]))!=1:
            raise RuntimeError('Peg must have exactly two free jaws and one hinge: '+name)
        if item.get('kinematic_bodies'):
            raise RuntimeError('Task peg jaw is kinematic: '+name)
        joint=item['joints'][0]
        if joint['type']!='PhysicsRevoluteJoint' or len(joint['body0'])!=1 or len(joint['body1'])!=1:
            raise RuntimeError('Peg has a world fixture or unexpected constraint: '+name)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=('smoke','motion-probe'),default='smoke')
    p.add_argument('--steps',type=int,default=None)
    p.add_argument('--plan',type=Path,help='Precomputed ordinary joint commands; required for motion-probe')
    p.add_argument('--seed',type=int,default=0)
    p.add_argument('--joint-feedback-from',type=int,help='Enable bounded right-arm PI tracking after this many actions, using ordinary joint observations only')
    p.add_argument('--judging-views',action='store_true',help='Record additional native960×720 front/rear assessor videos')
    p.add_argument('--out',type=Path)
    p.add_argument('--check-only',action='store_true',help='Compile source and check JSON without loading a simulator')
    args=p.parse_args()
    fixed_plan=fixed_actions=None
    if args.mode=='motion-probe':
        if args.plan is None:
            p.error('motion-probe requires a precomputed --plan')
        from fixed_motion import load
        fixed_plan,fixed_actions=load(args.plan)
        if fixed_plan.get('do_not_run_reason'):
            p.error('Blocked diagnostic plan: '+fixed_plan['do_not_run_reason'])
        if fixed_plan.get('line_pegs_required'):
            expected=hashlib.sha256(Path(__file__).with_name('line_pegs.py').read_bytes()).hexdigest()
            if fixed_plan.get('line_peg_source_sha256')!=expected or not 'LINE_PEGS_ENABLED=True' in Path(__file__).with_name('task.py').read_text():
                p.error('Motion requires the matching passive pegs-on-line reset')
        if fixed_plan.get('peg_rests_required') or fixed_plan.get('peg_rests_candidate'):
            expected=hashlib.sha256(Path(__file__).with_name('peg_rests.py').read_bytes()).hexdigest()
            if fixed_plan.get('peg_rest_source_sha256')!=expected:
                p.error('Peg motion does not match the current rest source; recompile and audit first')
            if not 'PEG_RESTS_ENABLED=True' in Path(__file__).with_name('task.py').read_text():
                p.error('Peg motion requires the declared raised-rest task reset')
        from scene import SUPPORT_BOARD_THICKNESS
        if fixed_plan.get('fixture_board_thickness_m')!=SUPPORT_BOARD_THICKNESS:
            p.error('Frozen motion was not compiled for the current support thickness; recompile and audit first')
        args.steps=len(fixed_actions) if args.steps is None else args.steps
        if not 1<=args.steps<=len(fixed_actions):
            p.error('--steps exceeds the frozen action sequence')
    else:
        if args.plan is not None:
            p.error('smoke mode has no movement plan')
        args.steps=60 if args.steps is None else args.steps
        if not 1<=args.steps<=MAX_SMOKE_STEPS:
            p.error('Smoke runs are limited to 1–200 control steps')
    if args.joint_feedback_from is not None and (args.mode!='motion-probe' or not 0<=args.joint_feedback_from<args.steps):
        p.error('Joint feedback requires a motion probe and a start before its last action')
    if fixed_plan is not None and fixed_plan.get('requires_joint_feedback_from')!=args.joint_feedback_from:
        p.error('Joint feedback option must exactly match the frozen plan')
    if not 0<=args.seed<2**32:
        p.error('Seed must be an unsigned 32-bit integer')
    source_hashes=sources()
    if args.check_only:
        print(json.dumps({'status':'local_syntax_and_json_passed','source_sha256':source_hashes,
                          'native_runtime':'not_tested','score':None},indent=2))
        return
    if args.out is None:
        p.error('--out is required for a native smoke run')
    versions=package_versions()
    if not (versions.get('isaacsim') or '').startswith('6.1.'):
        raise RuntimeError('Use the retained Isaac Sim 6.1 environment; this runner has no CPU fallback')
    args.out.mkdir(parents=True,exist_ok=False)
    frozen=args.out/'task-source'
    frozen.mkdir()
    for name in source_hashes:
        shutil.copyfile(HERE/name,frozen/name)
    if args.plan is not None:
        shutil.copyfile(args.plan,frozen/'fixed-motion.json')
        source_hashes['fixed-motion.json']=hashlib.sha256(args.plan.read_bytes()).hexdigest()
    draft=json.loads((HERE/'task.draft.json').read_text())
    started=time.monotonic()
    report={'kind':'diagnostic_yam_'+args.mode+'_not_submission_evidence','status':'initializing',
            'score':None,'demo':False,'dream_requests':0,'started_utc':datetime.now(timezone.utc).isoformat(),
            'source_sha256':source_hashes,'versions':versions,'seed':args.seed,
            'control_hz':CONTROL_HZ,'requested_steps':args.steps,'completed_steps':0,
            'policy':('constant adapter-ready joint targets' if fixed_plan is None else 'frozen fixed joint trajectory')+'; no object/assessor feedback',
            'instruction':draft['instruction'],'joint_feedback_from':args.joint_feedback_from}
    if args.joint_feedback_from is not None:
        report['policy']='frozen joint reference with bounded right-arm PI from ordinary joint observations; no object/assessor feedback'
    def save():
        report['wall_seconds']=time.monotonic()-started
        temporary=args.out/'run.json.tmp'
        temporary.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        temporary.replace(args.out/'run.json')
    save()
    app=video=trace=emb=None
    judging_videos={}
    def terminate(signum,frame):
        raise SystemExit('SIGTERM: bounded diagnostic interrupted')
    previous_sigterm=signal.signal(signal.SIGTERM,terminate)
    try:
        os.environ.setdefault('OMNI_KIT_ACCEPT_EULA','YES')
        from isaaclab.app import AppLauncher
        app=AppLauncher(headless=True,enable_cameras=True).app
        import torch
        import imageio.v2 as imageio
        from PIL import Image
        import omni.usd
        import arena_cloth
        from arena_props import PEG_SPECS
        from scene import PHYSICS_HZ
        from yam_arena import inspect_embodiment as wrapper,scene
        # The normal callback derives decimation from this timestep and20 Hz.
        scene.PHYSICS_DT=1/PHYSICS_HZ
        if args.judging_views:
            from review_views import configure,metadata
            original_make_env=scene.make_env
            def with_review_cameras(embodiment,**kwargs):
                configure(embodiment)
                return original_make_env(embodiment,**kwargs)
            scene.make_env=with_review_cameras
            report['judging_cameras']=metadata()
        np.random.seed(args.seed)
        torch.manual_seed(args.seed)
        wrapper._APP=app
        emb=wrapper.YamArenaEmbodiment(task=str(HERE/'task.py'),object_jitter=0.,
                                      control_hz=CONTROL_HZ,cam_width=224,cam_height=224)
        emb._ensure_sim(None)
        base=emb._base
        emb._instruction=draft['instruction']
        from reset_scene import reset_and_settle
        report['reset']={'method':'raw reset plus five seconds of fixed native settling','status':'requested'}
        save()
        report['reset']=reset_and_settle(emb)
        stage=omni.usd.get_context().get_stage()
        names=list(arena_cloth.SPECS)+list(PEG_SPECS)
        if not names:
            raise RuntimeError('Task custom assets were not registered')
        report['native_scene_audit']=native_audit(stage,list(arena_cloth.SPECS),list(PEG_SPECS))
        report['physics_dt_s']=float(base.sim.get_physics_dt())
        report['initial_physics_step_count']=int(base.sim._physics_step_count)
        report['initial_snapshot']='After one raw reset and the declared five-second native cloth/peg settling period'
        (args.out/'meshes.json').write_text(json.dumps({name:{'rest':spec.mesh.rest.tolist(),
            'faces':spec.mesh.faces.tolist(),'markers':spec.mesh.markers} for name,spec in arena_cloth.SPECS.items()})+'\n')
        video=imageio.get_writer(args.out/'diagnostic.mp4',fps=CONTROL_HZ,codec='libx264',pixelformat='yuv420p',
                                  ffmpeg_params=['-movflags','+faststart'],macro_block_size=1)
        if args.judging_views:
            for camera in report['judging_cameras']:
                judging_videos[camera['name']]=imageio.get_writer(
                    args.out/(camera['name'].replace('_','-')+'.mp4'),fps=CONTROL_HZ,
                    codec='libx264',pixelformat='yuv420p',ffmpeg_params=['-movflags','+faststart'],macro_block_size=1)
        trace=gzip.open(args.out/'trace.jsonl.gz','wt',compresslevel=1)
        ready=emb._ready.detach().cpu().numpy()[0].copy()
        if ready.shape!=(14,) or not np.isfinite(ready).all():
            raise RuntimeError('Invalid ready action')
        if np.any(ready<emb._low) or np.any(ready>emb._high):
            raise RuntimeError('Ready action exceeds normal adapter limits')
        report['initial_action14']=ready.tolist()
        if fixed_actions is not None and (np.any(fixed_actions<emb._low) or np.any(fixed_actions>emb._high)):
            raise ValueError('Fixed trajectory exceeds ordinary adapter action limits')
        if fixed_actions is not None:
            from yam_arena.constants import SHOULDER,WRIST,GRIPPER,FINGER_OPEN
            delta_limit=np.tile(np.array([SHOULDER['velocity']/CONTROL_HZ]*3+
                [WRIST['velocity']/CONTROL_HZ]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/CONTROL_HZ]),2)
            if np.any(np.abs(np.diff(np.vstack((ready,fixed_actions)),axis=0))>delta_limit*1.001):
                raise ValueError('Fixed trajectory exceeds normal joint/gripper speed limits')
        from joint_tracking import JointTracking
        tracking=JointTracking()
        report['joint_tracking_parameters']={k:getattr(tracking,k) for k in ('kp','ki','limit','slew')}
        active_action=ready.copy();reference_action=ready.copy();requested_action=ready.copy()
        def arr(value):
            return getattr(value,'torch',value).detach().cpu().numpy()
        def snapshot(step):
            observation=emb._observation()
            state=scene.object_states(emb._env,names)
            record={'step':step,'time_s':step/CONTROL_HZ,'action14':active_action.tolist(),
                    'measured_joint_pos':encode(np.asarray(observation.state['joint_pos'])),
                    'reference_action14':reference_action.tolist(),'requested_action14':requested_action.tolist(),
                    'right_tracking_bias6':tracking.bias.tolist(),
                    'objects':encode(state),'physics_step_count':int(base.sim._physics_step_count),
                    'robot_links':{name:{'names':list(base.scene[name].body_names),
                         'poses_xyzw':arr(base.scene[name].data.body_link_pose_w)[0].tolist()}
                         for name in ('left_robot','right_robot')}}
            trace.write(json.dumps(record,allow_nan=False)+'\n')
            trace.flush()
            image=np.asarray(observation.images['top_cam'],dtype=np.uint8)
            video.append_data(image)
            if args.judging_views:
                from review_views import images
                for camera,pixels in images(base).items():
                    judging_videos[camera].append_data(pixels)
                    if step in (0,args.steps):
                        label='start' if step==0 else 'final'
                        Image.fromarray(pixels).save(args.out/f'{camera.replace("_","-")}-{label}.png')

            if step in (0,args.steps):
                label='start' if step==0 else 'final'
                for camera,rgb in observation.images.items():
                    Image.fromarray(np.asarray(rgb,dtype=np.uint8)).save(args.out/f'diagnostic-{label}-{camera}.png')
        snapshot(0)
        report['status']='running'
        save()
        command=torch.as_tensor(ready[None,:],device=base.device,dtype=torch.float32)
        for step in range(1,args.steps+1):
            if fixed_actions is not None:
                reference_action=fixed_actions[step-1].copy()
                observed=np.asarray(emb._observation().state['joint_pos'],float)
                requested_action=tracking.action(reference_action,observed,enabled=args.joint_feedback_from is not None and step>args.joint_feedback_from)
                bounded=np.clip(requested_action,emb._low,emb._high)
                active_action=active_action+np.clip(bounded-active_action,-delta_limit,delta_limit)
                command=torch.as_tensor(active_action[None,:],device=base.device,dtype=torch.float32)
            emb._env.step(command)
            emb._t=step/CONTROL_HZ
            snapshot(step)
            report['completed_steps']=step
            if step%20==0:
                save()
        report['status']='complete'
        report['meaning']='Bounded diagnostic execution completed; no task success or contact fidelity certified'
    except BaseException as exc:
        report.update(status='interrupted' if isinstance(exc,SystemExit) else 'failed',error_type=type(exc).__name__,error_message=str(exc))
        raise
    finally:
        if trace is not None:trace.close()
        if video is not None:video.close()
        for recorder in judging_videos.values():recorder.close()
        save()
        if app is not None:app.close()
        signal.signal(signal.SIGTERM,previous_sigterm)


if __name__=='__main__':main()
