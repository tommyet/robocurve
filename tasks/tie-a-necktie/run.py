"""Bounded YAM/Arena smoke recorder. No task demo, Dream call or scored success.

Smoke mode holds the ordinary ready joint targets. Motion-probe mode replays a
frozen ordinary joint trajectory. Explicit state-assisted mode reads reset
cloth geometry to choose ordinary joint targets; it cannot move material
directly. Dream retains normal camera and joint observations.
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
        if p.suffix in ('.py','.json','.md','.npz') or p.name=='LICENSE':
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
    result={'cloth':{},'pegs':{},'attachments':[],'physics_scenes':[]}
    for prim in stage.Traverse():
        path=str(prim.GetPath())
        schemas=prim.GetAppliedSchemas()
        if prim.IsA(UsdPhysics.Scene):
            result['physics_scenes'].append(dict(path=path,settings={name:prim.GetAttribute('physxScene:'+name).Get() for name in ('enableGPUDynamics','enableEnhancedDeterminism','enableExternalForcesEveryIteration')}))
        if 'Attachment' in prim.GetTypeName() or any('Attachment' in s for s in schemas):
            result['attachments'].append(path)
        for name in cloth_names:
            if path.endswith('/'+name) and 'OmniPhysicsDeformableBodyAPI' in schemas:
                result['cloth'][name]={'path':path,'schemas':list(schemas),
                     'rigid_body':prim.HasAPI(UsdPhysics.RigidBodyAPI),
                     'self_collision':prim.GetAttribute('physxDeformableBody:selfCollision').Get(),
                     'speculative_ccd':prim.GetAttribute('physxDeformableBody:enableSpeculativeCCD').Get(),
                     'collision_pair_update_frequency':prim.GetAttribute('physxDeformableBody:collisionPairUpdateFrequency').Get(),
                     'solver_position_iterations':prim.GetAttribute('physxDeformableBody:solverPositionIterationCount').Get()}
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
    p.add_argument('--mode',choices=('smoke','motion-probe','dream'),default='smoke')
    p.add_argument('--steps',type=int,default=None)
    p.add_argument('--plan',type=Path,help='Precomputed ordinary joint commands; required for motion-probe')
    p.add_argument('--seed',type=int,default=0)
    p.add_argument('--inside-out-reset',action='store_true',help='Explicit diagnostic reset for a simple (Oriental) knot; default remains front-face drape')
    p.add_argument('--adult-collar',action='store_true',help='Explicit diagnostic145cm tie and standalone folded-collar form')
    p.add_argument('--state-assisted-grasp',action='store_true',help='Disclosed scripted adult pickup: use measured reset cloth to select ordinary finger targets')
    p.add_argument('--state-assisted-handoff',action='store_true',help='Disclosed scripted adult tip transfer: measure the held free tip before ordinary receiving-finger actions')
    p.add_argument('--surface-contact-diagnostic',action='store_true',help='Native speculative cloth contact and eight within-step collision-pair updates; no material or rest-gap changes')
    p.add_argument('--judging-views',action='store_true',help='Record additional native960×720 front/rear assessor videos')
    p.add_argument('--out',type=Path)
    p.add_argument('--check-only',action='store_true',help='Compile source and check JSON without loading a simulator')
    args=p.parse_args()
    os.environ['ROBOCURVE_TIE_SURFACE_CONTACT_DIAGNOSTIC']='1' if args.surface_contact_diagnostic else '0'
    fixed_plan=fixed_actions=None
    if args.mode=='motion-probe':
        if args.plan is None:
            p.error('motion-probe requires a precomputed --plan')
        from fixed_motion import load
        fixed_plan,fixed_actions=load(args.plan)
        if bool(fixed_plan.get('requires_inside_out_reset')) != args.inside_out_reset:
            p.error('Motion and explicitly selected initial face do not match')
        if fixed_plan.get('do_not_run_reason'):
            p.error(fixed_plan['do_not_run_reason'])
        if bool(fixed_plan.get('requires_adult_collar')) != args.adult_collar:
            p.error('Motion and selected collar form do not match')
        if bool(fixed_plan.get('requires_state_assisted_handoff')) != args.state_assisted_handoff:
            p.error('Motion and selected tip-transfer controller do not match')
        expected=hashlib.sha256((HERE/('adult_layout.py' if args.adult_collar else 'layout.py')).read_bytes()).hexdigest()
        if fixed_plan.get('fixture_source_sha256')!=expected:
            p.error('Frozen motion does not match current collar geometry; recompile and audit first')
        args.steps=len(fixed_actions) if args.steps is None else args.steps
        if not 1<=args.steps<=len(fixed_actions):
            p.error('--steps exceeds the frozen action sequence')
    else:
        if args.plan is not None:
            p.error('smoke mode has no movement plan')
        maximum=3600 if args.mode=='dream' else MAX_SMOKE_STEPS
        args.steps=maximum if args.mode=='dream' and args.steps is None else 60 if args.steps is None else args.steps
        if not 1<=args.steps<=maximum:p.error(f'This mode permits1–{maximum} control steps')
    if args.mode=='dream' and (args.state_assisted_grasp or args.state_assisted_handoff):p.error('Dream receives ordinary observations and its own actions only')
    if args.mode=='dream' and not(args.adult_collar and args.inside_out_reset):p.error('Current Dream candidate requires the adult inside-out reset matching its demo')
    if not 0<=args.seed<2**32:
        p.error('Seed must be an unsigned 32-bit integer')
    if args.state_assisted_grasp and (args.mode!='motion-probe' or not args.adult_collar or args.steps not in ((280,580) if args.state_assisted_handoff else (220,))):
        p.error('Adult scripted pickup requires 220 actions; the transfer permits a 280-action held-pose diagnostic or 580 actions')
    if args.state_assisted_handoff and not args.state_assisted_grasp:p.error('Tip transfer requires the measured adult pickup prefix')
    if args.state_assisted_handoff and args.steps>280:
        from adult_handoff import RECEIVING_ROUTE_RELEASED
        if not RECEIVING_ROUTE_RELEASED:
            p.error('Receiving route is held until the forward-carried cloth is measured and its new approach is screened')
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
    if not args.adult_collar:
        draft['instruction']=('Tie a simple (Oriental) necktie knot' if args.inside_out_reset else 'Tie a four-in-hand necktie')+' on the child collar form and leave it ready to wear.'
    started=time.monotonic()
    report={'kind':'diagnostic_yam_'+args.mode+'_not_submission_evidence','status':'initializing',
            'score':None,'demo':False,'dream_requests':0,'started_utc':datetime.now(timezone.utc).isoformat(),
            'source_sha256':source_hashes,'versions':versions,'seed':args.seed,
            'initial_face':'inside-out for simple knot diagnostic' if args.inside_out_reset else 'front-face four-in-hand diagnostic',
            'adult_collar_candidate':args.adult_collar,
            'control_hz':CONTROL_HZ,'requested_steps':args.steps,'completed_steps':0,
            'policy':('constant adapter-ready joint targets' if fixed_plan is None else 'frozen fixed joint trajectory')+'; no object/assessor feedback',
            'instruction':draft['instruction']}
    if args.state_assisted_grasp:
        report['policy']='Explicit state-assisted scripted feasibility demonstration: measured reset cloth selects an ordinary pinch and lift. No physical state writes; Dream receives no material state.'
    if args.mode=='dream':report['policy']='Dream: ordinary camera/joint observations only, no material-state or scripted controller input'
    def save():
        report['wall_seconds']=time.monotonic()-started
        temporary=args.out/'run.json.tmp'
        temporary.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        temporary.replace(args.out/'run.json')
    save()
    app=video=trace=emb=dream=None
    request_audit=[];session_audit={'session_count':0}
    judging_videos={}
    def terminate(signum,frame):
        raise SystemExit('SIGTERM: bounded diagnostic interrupted')
    previous_sigterm=signal.signal(signal.SIGTERM,terminate)
    try:
        os.environ.setdefault('OMNI_KIT_ACCEPT_EULA','YES')
        os.environ['ROBOCURVE_TIE_INSIDE_OUT_RESET']='1' if args.inside_out_reset else '0'
        os.environ['ROBOCURVE_TIE_ADULT_COLLAR']='1' if args.adult_collar else '0'
        from isaaclab.app import AppLauncher
        app=AppLauncher(headless=True,enable_cameras=True).app
        import torch
        import imageio.v2 as imageio
        from PIL import Image
        import omni.usd
        import arena_cloth
        from arena_props import PEG_SPECS
        from yam_arena import inspect_embodiment as wrapper,scene
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
        if args.surface_contact_diagnostic:
            actual=report['native_scene_audit']['cloth']['tie']
            if actual['speculative_ccd'] is not True or actual['collision_pair_update_frequency']!=8:
                raise RuntimeError('Requested surface collision settings did not reach native cloth')
        report['physics_dt_s']=float(base.sim.get_physics_dt())
        if args.adult_collar:
            from adult_layout import fixture_geometry
            report['fixture_geometry']=fixture_geometry()
        if args.state_assisted_grasp:
            from adult_motion import compile_pickup
            from audit_adult_motion import audit
            nodes=arena_cloth.state(emb._env,'tie').nodes
            np.savez_compressed(args.out/'reset-cloth.npz',positions=nodes,
                rest=arena_cloth.SPECS['tie'].mesh.rest,faces=arena_cloth.SPECS['tie'].mesh.faces)
            fixed_plan=compile_pickup(arena_cloth.SPECS['tie'].mesh.rest,nodes)
            from audit_reset_approach import screen
            approach_hits=screen(fixed_plan,nodes,arena_cloth.SPECS['tie'].mesh.faces)
            (args.out/'reset-cloth-approach-audit.json').write_text(json.dumps(dict(samples=80,inflation_m=.001,violations=approach_hits),indent=2)+'\n')
            if approach_hits:raise RuntimeError('Measured reset cloth intersects the pre-grasp robot approach')
            clearance=audit(fixed_plan)
            (args.out/'reset-grasp-hull-audit.json').write_text(json.dumps(clearance,indent=2)+'\n')
            if not clearance['passed']:raise RuntimeError('Measured adult pickup fails commanded hull rejection check')
            if args.state_assisted_handoff:
                from adult_handoff import template
                fixed_plan=template(fixed_plan)
                raised_clearance=audit(dict(frames=fixed_plan['frames'][220:280]))
                if not raised_clearance['passed']:raise RuntimeError('Raised transfer pose fails commanded hull rejection check')
            fixed_plan.pop('do_not_run_reason',None)
            (frozen/'fixed-motion.json').rename(frozen/'requested-fixed-motion.json')
            (frozen/'fixed-motion.json').write_text(json.dumps(fixed_plan,indent=2)+'\n')
            report['executed_plan_sha256']=hashlib.sha256((frozen/'fixed-motion.json').read_bytes()).hexdigest()
            report['state_assisted_grasp']=fixed_plan['grasp']
            fixed_actions=np.asarray([f['action14'] for f in fixed_plan['frames']],float)
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
        from yam_arena.constants import SHOULDER,WRIST,GRIPPER,FINGER_OPEN
        delta_limit=np.tile(np.array([SHOULDER['velocity']/CONTROL_HZ]*3+
            [WRIST['velocity']/CONTROL_HZ]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/CONTROL_HZ]),2)
        if fixed_actions is not None:
            if np.any(np.abs(np.diff(np.vstack((ready,fixed_actions)),axis=0))>delta_limit*1.001):
                raise ValueError('Fixed trajectory exceeds normal joint/gripper speed limits')
        active_action=ready.copy()
        def arr(value):
            return getattr(value,'torch',value).detach().cpu().numpy()
        def snapshot(step):
            observation=emb._observation()
            state=scene.object_states(emb._env,names)
            record={'step':step,'time_s':step/CONTROL_HZ,'action14':active_action.tolist(),
                    'measured_joint_pos':encode(np.asarray(observation.state['joint_pos'])),
                    'objects':encode(state),'physics_step_count':int(base.sim._physics_step_count),
                    'robot_links':{name:{'names':list(base.scene[name].body_names),
                         'poses_xyzw':arr(base.scene[name].data.body_link_pose_w)[0].tolist()}
                         for name in ('left_robot','right_robot')}}
            trace.write(json.dumps(record,allow_nan=False)+'\n')
            trace.flush()
            report['last_recorded_native_step']=step
            image=np.asarray(observation.images['top_cam'],dtype=np.uint8)
            video.append_data(image)
            if args.judging_views:
                from review_views import images
                for camera,pixels in images(base,warnings=report.setdefault('judging_frame_warnings',[]),step=step).items():
                    judging_videos[camera].append_data(pixels)
                    if step in (0,args.steps):
                        label='start' if step==0 else 'final'
                        Image.fromarray(pixels).save(args.out/f'{camera.replace("_","-")}-{label}.png')

            if step in (0,args.steps):
                label='start' if step==0 else 'final'
                for camera,rgb in observation.images.items():
                    Image.fromarray(np.asarray(rgb,dtype=np.uint8)).save(args.out/f'diagnostic-{label}-{camera}.png')
        snapshot(0)
        if args.mode=='dream':
            from inspect_robots import Scene
            from dream_policy import make_policy
            dream=make_policy(request_audit,session_audit,rows_per_request=8)
            dream.bind(emb.info);dream.reset(Scene(id='tie-a-necktie',instruction=draft['instruction']))
            report['dream_model']=dream.info.checkpoint
        report['status']='running'
        # Kit may replace process handlers during startup. Re-arm after setup
        # so a bounded trial preserves its partial evidence on termination.
        signal.signal(signal.SIGTERM,terminate)
        save()
        command=torch.as_tensor(ready[None,:],device=base.device,dtype=torch.float32)
        receiving_check_steps=set()
        for step in range(1,args.steps+1):
            if args.state_assisted_handoff and step==281:
                from adult_handoff import select_receiving_plan
                native=arena_cloth.state(emb._env,'tie');mesh=arena_cloth.SPECS['tie'].mesh
                np.savez_compressed(args.out/'handoff-input-cloth.npz',positions=native.nodes,rest=mesh.rest,faces=mesh.faces)
                selected=select_receiving_plan(fixed_actions[279],mesh.rest,native.nodes,mesh.faces,
                    half_thickness=arena_cloth.SPECS['tie'].fabric.thickness/2)
                (args.out/'handoff-candidate-audit.json').write_text(json.dumps(selected['candidates'],indent=2)+'\n')
                if selected['plan'] is None:
                    raise RuntimeError('No ordinary receiving approach clears the measured cloth and fixtures')
                continuation=selected['plan']
                (args.out/'handoff-hull-audit.json').write_text(json.dumps(selected['rigid'],indent=2)+'\n')
                (args.out/'handoff-cloth-approach-audit.json').write_text(json.dumps(selected['approach'],indent=2)+'\n')
                report['handoff_route_selection']=selected['selection']
                fixed_plan['frames'][280:]=continuation['frames'];fixed_plan['handoff_calibration']=continuation['grasp']
                fixed_actions=np.asarray([f['action14'] for f in fixed_plan['frames']],float)
                if np.any(fixed_actions<emb._low) or np.any(fixed_actions>emb._high):raise ValueError('Receiving trajectory exceeds normal joint limits')
                if np.any(np.abs(np.diff(fixed_actions[279:],axis=0))>delta_limit*1.001):raise ValueError('Receiving trajectory exceeds normal action speeds')
                (frozen/'fixed-motion.json').write_text(json.dumps(fixed_plan,indent=2)+'\n')
                report['executed_plan_sha256']=hashlib.sha256((frozen/'fixed-motion.json').read_bytes()).hexdigest()
                receiving_check_steps={280+continuation['release_original_from'],281+continuation['release_original_through']}
                report['receiving_check_steps']=sorted(receiving_check_steps)
                report['state_assisted_handoff']=continuation['grasp'];save()
            if args.state_assisted_handoff and step in receiving_check_steps:
                from adult_handoff import receiving_material_present
                native=arena_cloth.state(emb._env,'tie');mesh=arena_cloth.SPECS['tie'].mesh
                robot=base.scene['left_robot'];index=list(robot.body_names).index('gripper')
                presence=receiving_material_present(mesh.rest,native.nodes,arr(robot.data.body_link_pose_w)[0,index])
                report.setdefault('receiving_material_checks',[]).append(dict(step_before_action=step,**presence))
                save()
                if presence['obvious_empty_pinch']:
                    raise RuntimeError('Wide tip is outside the receiving finger region; physical transfer is not established')
            if fixed_actions is not None:
                active_action=fixed_actions[step-1].copy()
                command=torch.as_tensor(active_action[None,:],device=base.device,dtype=torch.float32)
            elif dream is not None:
                chunk=dream.act(emb._observation())
                if len(chunk.actions)!=1:raise RuntimeError('Expected one ordinary Dream action')
                requested=np.asarray(chunk.actions[0].data,float)
                if requested.shape!=(14,) or not np.isfinite(requested).all():raise ValueError('Invalid Dream joint action')
                bounded=np.clip(requested,emb._low,emb._high)
                active_action=active_action+np.clip(bounded-active_action,-delta_limit,delta_limit)
                command=torch.as_tensor(active_action[None,:],device=base.device,dtype=torch.float32)
            emb._env.step(command)
            emb._t=step/CONTROL_HZ
            snapshot(step)
            report['completed_steps']=step
            if step%20==0:
                save()
        if args.judging_views:
            issues=report.get('judging_frame_warnings',[])
            report['judging_recording_quality']=dict(flagged_frames=len(issues),
                final_frame_flagged=any(x['step']==args.steps for x in issues),
                requires_visual_review=True,
                note='All returned native frames are retained. Optional camera occlusion does not alter physics or imply task success; final scoring still requires meaningful visible evidence.')
        report['status']='complete'
        report['meaning']='Bounded diagnostic execution completed; no task success or contact fidelity certified'
    except BaseException as exc:
        report.update(status='interrupted' if isinstance(exc,SystemExit) else 'failed',error_type=type(exc).__name__,error_message=str(exc))
        raise
    finally:
        # Preserve status even if an interrupted encoder cannot finish closing.
        save()
        if trace is not None:trace.close()
        if video is not None:video.close()
        for recorder in judging_videos.values():recorder.close()
        if dream is not None:
            from dream_policy import public_transcript
            (args.out/'dream-transcript.json').write_text(json.dumps(public_transcript(dream),indent=2)+'\n')
        report.update(dream_requests=len(request_audit),dream_session_audit=session_audit)
        if request_audit:(args.out/'dream-requests.json').write_text(json.dumps(request_audit,indent=2)+'\n')
        save()
        if app is not None:app.close()
        signal.signal(signal.SIGTERM,previous_sigterm)


if __name__=='__main__':main()
