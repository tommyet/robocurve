"""Prototype native mechanics runner. No successful robot demo exists yet."""
import argparse
import atexit
import hashlib
import json
import os
from pathlib import Path
from config import *
from scoring import SprayScorer


def joint_observation_state(scene,ids):
    """The real adapter 14D joint observation, without touching camera sensors."""
    import numpy as np
    from yam_arena.constants import FINGER_OPEN
    per_arm=[]
    for name in ('left_robot','right_robot'):
        arm_ids,finger_ids=ids[name]
        value=scene[name].data.joint_pos
        value=value.torch if hasattr(value,'torch') else value
        q=value.detach().cpu().numpy()[0]
        per_arm.append(np.r_[q[arm_ids],np.clip(q[finger_ids].mean()/FINGER_OPEN,0.,1.)])
    return np.concatenate(per_arm).astype(np.float64)


def physics_manifest(stage,assets,urdf,physics_dt,control_dt):
    """Camera-independent authored physics and collision-input comparison."""
    import xml.etree.ElementTree as ET
    urdf=Path(urdf)
    meshes={}
    for mesh in ET.parse(urdf).getroot().findall('.//collision/geometry/mesh'):
        name=mesh.get('filename');meshes[name]=hashlib.sha256((urdf.parent/name).read_bytes()).hexdigest()
    inputs={'urdf_sha256':hashlib.sha256(urdf.read_bytes()).hexdigest(),'collision_mesh_sha256':meshes,
            'native_asset_sha256':{name:hashlib.sha256(Path(path).read_bytes()).hexdigest() for name,path in sorted(assets.items())},
            'physics_source_sha256':{name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ('mechanics.py','config.py','task.py')},
            'physics_dt_s':float(physics_dt),'control_dt_s':float(control_dt)}
    physical=[];counts={'colliders':0,'bodies':0,'joints':0,'mass_prims':0,'material_prims':0}
    for prim in stage.Traverse():
        schemas=list(prim.GetAppliedSchemas());kind=str(prim.GetTypeName())
        collision=any('CollisionAPI' in s for s in schemas);body=any('RigidBodyAPI' in s for s in schemas)
        joint='Joint' in kind and kind.startswith(('Physics','Physx'));mass=any('MassAPI' in s for s in schemas)
        material=any('MaterialAPI' in s for s in schemas)
        if not (collision or body or joint or mass or material or kind=='PhysicsScene'):continue
        for key,value in (('colliders',collision),('bodies',body),('joints',joint),('mass_prims',mass),('material_prims',material)):counts[key]+=int(value)
        attributes={}
        for attr in prim.GetAttributes():
            name=attr.GetName()
            if name.startswith(('physics:','physx','drive:')) and name not in ('physics:velocity','physics:angularVelocity'):
                value=attr.Get()
                if value is not None:attributes[name]=str(value)
        relationships={rel.GetName():[str(p) for p in rel.GetTargets()] for rel in prim.GetRelationships() if rel.GetName().startswith(('physics:','physx'))}
        physical.append(dict(path=str(prim.GetPath()),type=kind,schemas=sorted(s for s in schemas if 'Physics' in s or 'Physx' in s),attributes=attributes,relationships=relationships))
    physical.sort(key=lambda item:item['path'])
    digest=lambda value:hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return dict(physical_input_sha256=digest(inputs),body_joint_mass_sha256=digest(physical),inputs=inputs,counts=counts,body_joint_mass=physical,
                scope='URDF/collision/native-asset bytes and authored collider/body/joint/mass/PhysicsScene properties. Sensor cameras and dynamic transforms excluded; trajectory identity is not asserted.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy',choices=['probe','capprobe','demo','dream'],default='probe')
    parser.add_argument('--stage',choices=['cap','press','full'],default='full')
    parser.add_argument('--max-steps',type=int,default=2400)
    parser.add_argument('--render-sync',action='store_true',help='Use real RGB cameras with FXAA and synchronous rendering for the device-loss mitigation trial')
    parser.add_argument('--no-video',action='store_true',help='State-only demo engineering run; no camera renderer, images or eligible final media')
    parser.add_argument('--log-dir',type=Path,required=True)
    args=parser.parse_args()
    if not 1 <= args.max_steps <= 2400:parser.error('max-steps must be 1..2400')
    if args.no_video and args.policy!='demo':parser.error('--no-video is allowed only with --policy demo; image-based policies require cameras')
    if args.no_video and args.render_sync:parser.error('--no-video cannot be combined with --render-sync')
    out=args.log_dir.expanduser().resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'source').mkdir()
    sources=list(Path(__file__).parent.glob('*.py'))
    sources.append(Path(__file__).with_name('press_face.json'))
    for source in sources:(out/'source'/source.name).write_bytes(source.read_bytes())
    (out/'source-sha256.json').write_text(json.dumps(
        {s.name:hashlib.sha256(s.read_bytes()).hexdigest() for s in sources},indent=2))
    import numpy as np
    from inspect_robots.cli import main as cli
    from inspect_robots.registry import register
    from yam_arena.inspect_embodiment import YamArenaEmbodiment
    from yam_arena.urdf import quat_xyzw_to_matrix
    from yam_arena import ik
    import telemetry

    class SprayEmbodiment(YamArenaEmbodiment):
        def __init__(self,*a,**kw):
            super().__init__(*a,**kw)
            if args.no_video:
                from dataclasses import replace
                from inspect_robots_yam.config import observation_space
                self.info=replace(self.info,observation_space=observation_space(self.cam_height,self.cam_width,()))

        def _observation(self):
            if not args.no_video:return super()._observation()
            from inspect_robots.types import Observation
            from inspect_robots_yam.packing import STATE_KEY
            return Observation(images={},state={STATE_KEY:joint_observation_state(self._base.scene,self._ids)},
                               instruction=self._instruction,image_times={},state_time=self._t)

        def _ensure_sim(self,goal):
            if self._env is not None and goal == self._goal:return
            from yam_arena import inspect_embodiment as adapter
            if adapter._APP is None:
                os.environ.setdefault('OMNI_KIT_ACCEPT_EULA','YES')
                from isaaclab.app import AppLauncher
                kit_args='--/rtx/post/aa/op=2 --/app/asyncRendering=false --/omni/replicator/asyncRendering=false --/exts/isaacsim.core.throttling/enable_async=false' if args.render_sync else ''
                adapter._APP=AppLauncher(headless=True,device=self.device,enable_cameras=not args.no_video,kit_args=kit_args).app
                atexit.register(adapter._close_app_at_exit)
            from yam_arena import scene as sc
            from yam_arena.embodiment import BimanualYamEmbodiment
            from yam_arena import embodiment as robot_module
            original_renderer=robot_module.RENDERER
            if args.render_sync:
                import copy
                robot_module.RENDERER=copy.deepcopy(original_renderer)
                settings=robot_module.RENDERER.global_settings
                settings.antialiasing_mode='FXAA'
                settings.carb_settings={**(settings.carb_settings or {}),
                    '/app/asyncRendering':False,'/omni/replicator/asyncRendering':False,
                    '/exts/isaacsim.core.throttling/enable_async':False}
            original_init=BimanualYamEmbodiment.__init__
            def sensor_init(instance,*a,**kw):
                kw['contact_sensors']=True
                kw['enable_cameras']=not args.no_video
                original_init(instance,*a,**kw)
                stem=instance.scene_config.left_contacts.prim_path.rsplit('/.*',1)[0]
                instance.scene_config.left_contacts.filter_prim_paths_expr=['{ENV_REGEX_NS}/spray_can']
                instance.scene_config.right_contacts.filter_prim_paths_expr=[
                    '{ENV_REGEX_NS}/spray_can','{ENV_REGEX_NS}/button',
                    *[stem+instance.link_paths[n] for n in ('gripper','tip_left','tip_right')]]
            BimanualYamEmbodiment.__init__=sensor_init
            import isaaclab.sim as sim
            from mechanics import asset,stand_asset
            assets={name:asset(out/(name+'.usda'),name) for name in ('spray_can','cap','button')}
            assets['stand']=stand_asset(out/'stand.usda')
            self.native_assets=assets
            original=sc.task_object
            def make(spec):
                if spec.name not in assets:return original(spec)
                cfg=sim.UsdFileCfg(usd_path=assets[spec.name])
                if spec.name=='button':
                    spawn_usd=cfg.func
                    def spawn(path,cfg,translation=None,orientation=None,**kwargs):
                        prim=spawn_usd(path,cfg,translation=translation,orientation=orientation,**kwargs)
                        from mechanics import joints
                        # Author before the environment initializes PhysX views,
                        # rather than adding constraints to an already-live scene.
                        parent=str(prim.GetPath()).rsplit('/',1)[0]
                        joints(prim.GetStage(),parent+'/spray_can',parent+'/cap',parent+'/button',cap_attached=args.stage!='press')
                        return prim
                    cfg.func=spawn
                position=spec.pos
                if spec.name=='cap' and args.stage=='press':position=(CAP_PAD[0],CAP_PAD[1],TOP+.019)
                return sc.Object(name=spec.name,object_type=sc.ObjectType.BASE if spec.name=='stand' else sc.ObjectType.RIGID,
                    spawner_cfg=cfg,
                    initial_pose=sc.Pose(position_xyz=tuple(position),rotation_xyzw=(0.,0.,0.,1.)))
            sc.task_object=make
            try:super()._ensure_sim(goal)
            finally:
                sc.task_object=original
                BimanualYamEmbodiment.__init__=original_init
                robot_module.RENDERER=original_renderer
            if args.no_video:
                # The pinned adapter renders four times explicitly after its
                # settle loop. Also suppress any render request from env.step.
                self._base.sim.render=lambda *a,**kw:None
                cameras=[name for name in adapter.DEFAULT_CAMERAS if name in self._base.scene.sensors]
                if cameras:raise RuntimeError('state-only mode unexpectedly created camera sensors: '+str(cameras))
                (out/'renderer-readback.json').write_text(json.dumps(dict(state_only=True,camera_sensors=cameras,
                    render_requests_suppressed=True,rtx_camera_capture_enabled=False),indent=2))
            if args.render_sync:
                import carb.settings
                settings=carb.settings.get_settings()
                expected={'/rtx/post/aa/op':2,'/app/asyncRendering':False,
                    '/omni/replicator/asyncRendering':False,'/exts/isaacsim.core.throttling/enable_async':False}
                actual={key:settings.get(key) for key in expected}
                (out/'renderer-readback.json').write_text(json.dumps(dict(requested=expected,actual=actual),indent=2))
                if actual!=expected:raise RuntimeError('renderer settings do not match the requested synchronous FXAA mode')

        def reset(self,scene,*,seed=None):
            if hasattr(self,'audit'):raise RuntimeError('one trial per process')
            # Install joints before super.reset advances physics. _ensure_sim
            # creates the world on the first reset in the pinned YAM adapter.
            return self._reset_with_joints(scene,seed)

        def _ensure_joints(self):
            if getattr(self,'joints_installed',False):return
            from mechanics import box
            self.stage=self._base.scene.stage
            self.paths={name:'/World/envs/env_0/'+name for name in ('spray_can','cap','button')}
            for path in self.paths.values():
                if not self.stage.GetPrimAtPath(path):raise RuntimeError('missing rigid body '+path)
            for suffix in ('cap_guide','button_slide'):
                if suffix=='cap_guide' and args.stage=='press':continue
                if not self.stage.GetPrimAtPath(self.paths['spray_can']+'/'+suffix):
                    raise RuntimeError('missing native joint '+suffix)
            self.joints_installed=True
            self.contact_acc={};self.contact_errors=[]
            from omni.physx import get_physx_simulation_interface
            from pxr import PhysicsSchemaTools
            def decode(value):
                try:return str(PhysicsSchemaTools.intToSdfPath(value))
                except TypeError:return str(PhysicsSchemaTools.decodeSdfPath(value))
            def contact_report(headers,data):
                try:
                    for h in headers:
                        a,b=decode(h.actor0),decode(h.actor1)
                        key='|'.join((a,b,decode(h.collider0),decode(h.collider1)))
                        for i in range(h.contact_data_offset,h.contact_data_offset+h.num_contact_data):
                            c=data[i];entry=self.contact_acc.setdefault(key,dict(impulse=0.,points=0))
                            entry['impulse']+=float(np.linalg.norm(c.impulse));entry['points']+=1
                            entry['position']=[float(v) for v in c.position]
                            entry['normal']=[float(v) for v in c.normal]
                            entry['separation']=float(c.separation)
                except Exception as error:
                    if not self.contact_errors:self.contact_errors.append(str(error))
            self.contact_subscription=get_physx_simulation_interface().subscribe_contact_report_events(contact_report)
            # Surface-only colour tiles. They have no colliders and cannot
            # help the robot manipulate either the cap or the can.
            self.tiles=[]
            self.coat_cache=[0.]*(GRID*GRID)
            from pxr import UsdGeom
            self.mist=UsdGeom.Points.Define(self.stage,'/World/spray_mist')
            self.mist.CreatePointsAttr([]);self.mist.CreateWidthsAttr([])
            self.mist.CreateDisplayColorAttr([(.45,.70,1.)])
            for i,p,target in SprayScorer.cells():
                obj=box(self.stage,f'/World/spray_surface/cell_{i}',
                        (.0001,CELL*.98,CELL*.98),(TARGET_X-.0001,p[1],p[2]),
                        (.95,.95,.95) if target else BACKING_COLOR,False)
                self.tiles.append((obj,target))

        def _reset_with_joints(self,scene,seed):
            # _ensure_sim spawns both native joints before reset settles.
            self._ensure_sim(None)
            self._ensure_joints()
            from yam_arena import YAM_URDF
            physical=physics_manifest(self.stage,self.native_assets,YAM_URDF,self._base.cfg.sim.dt,self._base.step_dt)
            (out/'physics-manifest.json').write_text(json.dumps(physical,indent=2)+'\n')
            self.detached=args.stage=='press'
            self.tracker=SprayScorer()
            observation=super().reset(scene,seed=seed)
            self.task.module._tracker=self.tracker
            self.task.module._diagnostic=args.stage=='press'
            self.contact_acc={}
            self.audit=(out/'trajectory.jsonl').open('x')
            self._task_step()
            return observation

        def _task_step(self):
            if not hasattr(self,'audit'):return super()._task_step()
            def array(value):
                value=value.torch if hasattr(value,'torch') else value
                return value.detach().cpu().numpy().astype(float)
            world=self._base.arena_world
            def state(name):
                pose=array(world.get_pose_w(name))[0]
                speed=float(np.linalg.norm(array(world.get_root_linear_velocity_w(name))[0]))
                return pose[:3],quat_xyzw_to_matrix(pose[3:]),speed
            can,rot,can_speed=state('spray_can')
            cap,_,cap_speed=state('cap');button,_,_=state('button')
            cap_local=rot.T@(cap-can);button_local=rot.T@(button-can)
            if not self.detached and cap_local[2]-.087 >= .004:
                self.stage.RemovePrim(self.paths['spray_can']+'/cap_guide')
                self.detached=True
            hands=[];hand_states=[]
            from yam_arena.constants import FINGER_OPEN
            for side in ('left','right'):
                name=side+'_robot';robot=self._base.scene[name];ids,fids=self._ids[name]
                q=array(robot.data.joint_pos)[0]
                tcp,rotation=ik.tcp_pose(q[ids],self.rig.bases[side]);hands.append(tcp)
                hand_states.append(dict(tcp=tcp.tolist(),rotation=rotation.tolist(),joints=q[ids].tolist(),
                                        finger_joints=q[fids].tolist(),
                                        opening=float(np.clip(q[fids].mean()/FINGER_OPEN,0,1))))
            sample=dict(time=float(self._t),can=can.tolist(),cap=cap.tolist(),
                        nozzle=(button+rot@np.array((.009,0.,0.))).tolist(),axis=rot[:,0].tolist(),
                        button_travel=float(.077-button_local[2]),cap_detached=self.detached,
                        upright=float(rot[2,2]),can_speed=can_speed,cap_speed=cap_speed,
                        hand_tcp=[t.tolist() for t in hands],
                        hands=hand_states,can_rotation=rot.tolist(),can_axis=rot[:,2].tolist(),button=button.tolist(),
                        hands_clear=all(min(np.linalg.norm(t-can),np.linalg.norm(t-cap))>.07 for t in hands))
            sample['metrics']=self.tracker.update(sample)
            from pxr import Gf
            # Appearance only: a sparse animated aerosol visualization, gated
            # by measured piston travel and remaining spray supply. No forces,
            # particle contacts or scorer credit come from these points.
            visible=(sample['metrics']['cap_removed'] and sample['button_travel']>=PRESS_TRAVEL and
                     sample['metrics']['spray_seconds']<MAX_SPRAY_SECONDS)
            points=[]
            if visible:
                for i in range(72):
                    along=.015+.17*((i*.61803398875+self._t*2.5)%1.)
                    theta=i*2.3999632
                    radius=along*np.tan(np.radians(SPRAY_HALF_ANGLE))*.65
                    position=np.array(sample['nozzle'])+rot[:,0]*along+radius*(rot[:,1]*np.cos(theta)+rot[:,2]*np.sin(theta))
                    points.append(Gf.Vec3f(*position))
            self.mist.GetPointsAttr().Set(points)
            self.mist.GetWidthsAttr().Set([.0015]*len(points))
            for i,(tile,target) in enumerate(self.tiles):
                coat=min(1.,self.tracker.dose[i]/COAT_DOSE)
                if abs(coat-self.coat_cache[i])<1e-5:continue
                self.coat_cache[i]=coat
                base=(.95,.95,.95) if target else BACKING_COLOR
                tile.GetDisplayColorAttr().Set([Gf.Vec3f(*[(1-coat)*v+coat*b for v,b in zip(base,(.08,.3,.85))])])
            sample['controller']=telemetry.command
            sample['contacts']=self.contact_acc
            sample['contact_errors']=self.contact_errors
            sensor=self._base.scene['right_contacts']
            sample['right_contact_bodies']=sensor.body_names
            sample['right_contact_net']=array(sensor.data.net_forces_w)[0].tolist()
            if sensor.data.force_matrix_w is not None:
                sample['right_contact_matrix']=array(sensor.data.force_matrix_w)[0].tolist()
            left_sensor=self._base.scene['left_contacts']
            sample['left_contact_bodies']=left_sensor.body_names
            sample['left_contact_net']=array(left_sensor.data.net_forces_w)[0].tolist()
            if left_sensor.data.force_matrix_w is not None:
                sample['left_can_contact_matrix']=array(left_sensor.data.force_matrix_w)[0].tolist()
            self.contact_acc={}
            telemetry.latest=sample
            self.audit.write(json.dumps(sample,allow_nan=False)+'\n');self.audit.flush()
            return super()._task_step()

        def close(self):
            if hasattr(self,'audit'):
                self.audit.close()
                summary=self.tracker.result()
                if args.stage=='press':summary=dict(score=0.,diagnostic=True,milestones=summary)
                if args.no_video:summary.update(diagnostic=True,state_only=True,media_eligible=False)
                (out/'score-summary.json').write_text(json.dumps(summary,indent=2))
            super().close()

    register('embodiment','uncap_spray_prototype')(SprayEmbodiment)
    policy=args.policy
    if policy=='probe':
        from dataclasses import replace
        from yam_arena.scripted import YamScriptedPolicy
        from yam_arena.constants import READY
        from inspect_robots.types import Action,ActionChunk
        from inspect_robots_yam.packing import pack
        class HoldPolicy(YamScriptedPolicy):
            def __init__(self):
                super().__init__()
                self.info=replace(self.info,name='spray_geometry_probe')
            def reset(self,scene):pass
            def act(self,observation):
                arm=np.r_[READY,1.]
                return ActionChunk(actions=[Action(data=pack(arm,arm))],control_hz=20.)
        policy='spray_geometry_probe'
        register('policy',policy)(HoldPolicy)
    elif policy=='capprobe':policy='yam_scripted'
    elif policy=='demo':
        from demo_policy import register_policy
        policy=register_policy(cap_only=args.stage=='cap',press_only=args.stage=='press')
    diagnostic=args.no_video or args.policy in ('probe','capprobe') or (args.policy=='demo' and args.stage!='full')
    (out/'mode.json').write_text(json.dumps(dict(policy=args.policy,stage=args.stage,diagnostic=diagnostic,render_sync=args.render_sync,
                                               state_only=args.no_video,media_eligible=not diagnostic)))
    return cli(['run','--embodiment','uncap_spray_prototype','--policy',policy,
                '-E',f'task={Path(__file__).parent / "task.py"}','-E','object_jitter=0',
                '-E','control_hz=20','-E','cam_width=320','-E','cam_height=176',
                '--instruction',INSTRUCTION,'--scorer','task_score',
                '--max-steps',str(args.max_steps),*([] if args.no_video else ['--store-frames']),'--seed','0',
                '--no-prompt','--grader','none','--log-dir',str(out)])

if __name__=='__main__':main()
