"""Prototype native mechanics runner. No successful robot demo exists yet."""
import argparse
import atexit
import hashlib
import json
import os
from contextlib import contextmanager
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


def native_body_owners(scene,link_paths):
    """Map native rigid-link indices to the actual USD owners, not FK markers."""
    owners={}
    for side,prim in (('left','LeftArm'),('right','RightArm')):
        entity=side+'_robot';names=list(scene[entity].body_names)
        if len(names)!=9:raise ValueError('expected nine native rigid links for '+entity)
        for index,name in enumerate(names):
            path='/World/envs/env_0/'+prim+link_paths[name]
            if path in owners:raise ValueError('duplicate native replay body owner '+path)
            owners[path]=dict(kind='robot',entity=entity,body_name=name,body_index=index,
                              source='ArticulationData.body_link_pose_w')
    for name in ('spray_can','cap','button'):
        owners['/World/envs/env_0/'+name]=dict(kind='object',entity=name,source='arena_world.get_pose_w')
    if len(owners)!=21:raise ValueError('native replay requires exactly 21 rigid body owners')
    for path,owner in owners.items():
        parents=[candidate for candidate in owners if path.startswith(candidate+'/')]
        owner['parent_body_owner']=max(parents,key=len) if parents else None
    return owners


def native_body_world_poses(scene,world,owners):
    """Read all 21 actual actor-frame poses in [x,y,z,qx,qy,qz,qw] order."""
    import numpy as np
    def array(value):
        value=value.torch if hasattr(value,'torch') else value
        return value.detach().cpu().numpy()
    robot_poses={};result={}
    for path,owner in owners.items():
        entity=owner['entity']
        if owner['kind']=='robot':
            if entity not in robot_poses:
                robot_poses[entity]=array(scene[entity].data.body_link_pose_w)
                if robot_poses[entity].shape!=(1,9,7):raise ValueError('invalid native body_link_pose_w shape for '+entity)
            if scene[entity].body_names[owner['body_index']]!=owner['body_name']:raise ValueError('native replay body ordering changed')
            pose=np.asarray(robot_poses[entity][0,owner['body_index']],dtype=float)
        else:pose=np.asarray(array(world.get_pose_w(entity))[0],dtype=float)
        if pose.shape!=(7,) or not np.isfinite(pose).all() or abs(np.linalg.norm(pose[3:])-1.)>.001:
            raise ValueError('invalid actual native replay pose for '+path)
        result[path]=pose.tolist()
    if len(result)!=21:raise ValueError('incomplete native replay pose row')
    return result


def replay_camera_metadata(rig,owners,observation_width,observation_height):
    """Pinned optical calibration; wrist parents use native gripper poses."""
    from dataclasses import asdict
    from yam_arena.constants import CAM_RENDER_WIDTH,CAM_RENDER_HEIGHT
    cameras={'top_cam':dict(parent_body_owner=None,pose_space='world',**asdict(rig.top_cam))}
    for side in ('left','right'):
        parent=next(path for path,owner in owners.items() if owner.get('entity')==side+'_robot' and owner.get('body_name')=='gripper')
        cameras[side+'_cam']=dict(parent_body_owner=parent,pose_space='parent_body_actor_frame',**asdict(rig.wrist_cams[side]))
    return dict(source='pinned yam_arena Rig optical calibration, not fabricated camera observations',quaternion_order='xyzw',
                native_render_width=CAM_RENDER_WIDTH,native_render_height=CAM_RENDER_HEIGHT,
                policy_observation_width=observation_width,policy_observation_height=observation_height,cameras=cameras)


def export_replay_scene(stage,path):
    """Flatten into an output layer without changing the live stage."""
    path=Path(path);layer=stage.Flatten()
    if not layer.Export(str(path)):raise RuntimeError('composed replay scene export failed')
    dependencies=getattr(layer,'GetExternalAssetDependencies',None)
    return dict(scene_file=path.name,scene_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                external_asset_dependencies=sorted(str(item) for item in dependencies()) if dependencies else None)


def passive_rest_initial():
    """One-degree, already-supported initial layout, authored before spawn."""
    import math
    import numpy as np
    angle=math.radians(1.);c,s=math.cos(angle),math.sin(angle)
    rotation=np.array(((1.,0.,0.),(0.,c,-s),(0.,s,c)))
    center=np.array((CAN_START[0],CAN_START[1],TOP+RISER_HEIGHT+.070*c+.026*s))
    quat=(math.sin(angle/2),0.,0.,math.cos(angle/2))
    return {'spray_can':(tuple(map(float,center)),quat),'button':(tuple(map(float,center+rotation@np.array((0.,0.,.077)))),quat),
            'cap':((CAP_PAD[0],CAP_PAD[1],TOP+.019),(0.,0.,0.,1.))}


def passive_body_energy(mass,inertia,actor_rotation,com_pose,com_velocity,gravity):
    """Native inertia is at COM, column-major, expressed in actor axes."""
    import numpy as np
    tensor=np.asarray(inertia,dtype=float).reshape(3,3,order='F')
    velocity=np.asarray(com_velocity,dtype=float);omega=np.asarray(actor_rotation).T@velocity[3:]
    return {'linear_kinetic_J':float(.5*mass*(velocity[:3]@velocity[:3])),
            'rotational_kinetic_J':float(.5*omega@tensor@omega),
            'gravitational_J':float(-mass*np.asarray(gravity)@np.asarray(com_pose)[:3])}


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


@contextmanager
def physics_timestep(scene_module,physics_hz):
    """Temporarily select the pinned adapter's environment-construction step."""
    if physics_hz not in (240,960):raise ValueError('physics_hz must be 240 or 960')
    previous=scene_module.PHYSICS_DT
    scene_module.PHYSICS_DT=1./physics_hz
    try:yield
    finally:scene_module.PHYSICS_DT=previous


def physics_timing_readback(base,physics_hz):
    """Reject a requested integration rate unless the constructed env matches."""
    import math
    actual=float(base.cfg.sim.dt);control=float(base.step_dt);decimation=int(base.cfg.decimation)
    expected_decimation=round(physics_hz/20.)
    if not (math.isclose(actual,1./physics_hz,rel_tol=0.,abs_tol=1e-12) and
            math.isclose(control,.05,rel_tol=0.,abs_tol=1e-12) and decimation==expected_decimation):
        raise RuntimeError('physics/control timing readback does not match requested rate')
    return dict(requested_physics_hz=physics_hz,physics_dt_s=actual,control_dt_s=control,
                control_hz=20.,decimation=decimation,scope='constructed native environment cfg.sim.dt, cfg.decimation and step_dt')


def configure_contact_diagnostic(configs,enabled):
    """Set reporting-only sensor options before construction, explicitly opt-in."""
    if enabled:
        from native_contact_reader import SENSOR_CONSTRUCTION_REQUIREMENTS
        for cfg in configs:
            for name,value in SENSOR_CONSTRUCTION_REQUIREMENTS.items():setattr(cfg,name,value)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy',choices=['probe','capprobe','demo','recorded-demo','dream','rest-probe'],default='probe')
    parser.add_argument('--contact-diagnostic',action='store_true',help='Unscored stages only: raw native contact points/friction; no forces applied')
    parser.add_argument('--physics-hz',type=int,choices=[240,960],default=240,help='Physics integration frequency; controller remains20Hz')
    parser.add_argument('--body-solver-32-8',action='store_true',help='Explicit can/button PhysX solver precision; all other physics unchanged')
    parser.add_argument('--rest-solver',choices=['baseline','32-8'],default='baseline',help='Unscored passive-rest coupon only')
    parser.add_argument('--stage',choices=['cap','press','full'],default='full')
    parser.add_argument('--max-steps',type=int,default=2400)
    parser.add_argument('--render-sync',action='store_true',help='Use real RGB cameras with FXAA and synchronous rendering for the device-loss mitigation trial')
    parser.add_argument('--no-video',action='store_true',help='State-only demo engineering run; no camera renderer, images or eligible final media')
    parser.add_argument('--log-dir',type=Path,required=True)
    args=parser.parse_args()
    if not 1 <= args.max_steps <= 2400:parser.error('max-steps must be 1..2400')
    if args.policy=='rest-probe':args.stage='press';args.no_video=True
    elif args.rest_solver!='baseline':parser.error('--rest-solver is allowed only with --policy rest-probe')
    if args.contact_diagnostic and not (args.policy=='rest-probe' or (args.policy=='demo' and args.stage!='full')):parser.error('--contact-diagnostic requires an explicitly unscored demo stage or rest-probe')
    if args.no_video and args.policy not in ('demo','recorded-demo','rest-probe'):parser.error('--no-video is allowed only with --policy demo/recorded-demo/rest-probe; image-based policies require cameras')
    if args.no_video and args.render_sync:parser.error('--no-video cannot be combined with --render-sync')
    if args.policy=='recorded-demo' and (args.stage!='full' or args.physics_hz!=960 or args.body_solver_32_8):parser.error('recorded-demo requires full stage,960Hz and baseline body solver')
    out=args.log_dir.expanduser().resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'source').mkdir()
    sources=list(Path(__file__).parent.glob('*.py'))
    sources.append(Path(__file__).with_name('press_face.json'))
    if args.policy=='recorded-demo':sources.extend(Path(__file__).with_name(name)for name in ('recorded_demo_actions.jsonl','recorded_demo_metadata.json'))
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
                configure_contact_diagnostic((instance.scene_config.left_contacts,instance.scene_config.right_contacts),args.contact_diagnostic)
                stem=instance.scene_config.left_contacts.prim_path.rsplit('/.*',1)[0]
                instance.scene_config.left_contacts.filter_prim_paths_expr=['{ENV_REGEX_NS}/spray_can']
                instance.scene_config.right_contacts.filter_prim_paths_expr=[
                    '{ENV_REGEX_NS}/spray_can','{ENV_REGEX_NS}/button',
                    *[stem+instance.link_paths[n] for n in ('gripper','tip_left','tip_right')]]
            BimanualYamEmbodiment.__init__=sensor_init
            import isaaclab.sim as sim
            from mechanics import asset,stand_asset,panel_asset
            assets={name:asset(out/(name+'.usda'),name) for name in ('spray_can','cap','button')}
            assets['stand']=stand_asset(out/'stand.usda')
            assets['panel']=panel_asset(out/'panel.usda')
            if args.body_solver_32_8 or (args.policy=='rest-probe' and args.rest_solver=='32-8'):
                from pxr import Usd,PhysxSchema
                for name in ('spray_can','button'):
                    stage=Usd.Stage.Open(str(assets[name]));api=PhysxSchema.PhysxRigidBodyAPI.Apply(stage.GetDefaultPrim())
                    api.CreateSolverPositionIterationCountAttr(32);api.CreateSolverVelocityIterationCountAttr(8);stage.GetRootLayer().Save()
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
                orientation=(0.,0.,0.,1.)
                if args.policy=='rest-probe' and spec.name in passive_rest_initial():position,orientation=passive_rest_initial()[spec.name]
                return sc.Object(name=spec.name,object_type=sc.ObjectType.BASE if spec.name in ('stand','panel') else sc.ObjectType.RIGID,
                    spawner_cfg=cfg,
                    initial_pose=sc.Pose(position_xyz=tuple(position),rotation_xyzw=orientation))
            sc.task_object=make
            try:
                with physics_timestep(sc,args.physics_hz):super()._ensure_sim(goal)
            finally:
                sc.task_object=original
                BimanualYamEmbodiment.__init__=original_init
                robot_module.RENDERER=original_renderer
            timing=physics_timing_readback(self._base,args.physics_hz)
            (out/'physics-timing-readback.json').write_text(json.dumps(timing,indent=2)+'\n')
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
            from pxr import UsdGeom,Gf
            self.mist=UsdGeom.Points.Define(self.stage,'/World/spray_mist')
            self.mist.CreatePointsAttr([]);self.mist.CreateWidthsAttr([])
            self.mist.CreateDisplayColorAttr([(.45,.70,1.)])
            from surface_geometry import circle_cell_parts
            for i,p,target in SprayScorer.cells():
                parts=circle_cell_parts(p[1],p[2],CELL*.49,TARGET_CENTER,TARGET_RADIUS)
                obj=UsdGeom.Mesh.Define(self.stage,f'/World/spray_surface/cell_{i}')
                points=[];counts=[];indices=[];bases=[]
                for polygon,white in parts:
                    counts.append(len(polygon));indices.extend(range(len(points),len(points)+len(polygon)))
                    points.extend(Gf.Vec3f(TARGET_X-.0001,y,z) for y,z in polygon)
                    bases.append((.95,.95,.95) if white else BACKING_COLOR)
                obj.CreatePointsAttr(points);obj.CreateFaceVertexCountsAttr(counts);obj.CreateFaceVertexIndicesAttr(indices)
                obj.CreateSubdivisionSchemeAttr('none');obj.CreateDoubleSidedAttr(True)
                obj.CreateDisplayColorAttr([Gf.Vec3f(*base) for base in bases]);obj.GetDisplayColorPrimvar().SetInterpolation('uniform')
                self.tiles.append((obj,target,bases))

        def _reset_with_joints(self,scene,seed):
            # _ensure_sim spawns both native joints before reset settles.
            self._ensure_sim(None)
            self._ensure_joints()
            from pxr import PhysxSchema,UsdPhysics
            readback={'readback_scope':'live composed USD PhysxRigidBodyAPI and DriveAPI attributes; not native engine solver getter'}
            for name in ('spray_can','button'):
                prim=self.stage.GetPrimAtPath(self.paths[name]);api=PhysxSchema.PhysxRigidBodyAPI(prim)
                readback[name]={'position_iterations':api.GetSolverPositionIterationCountAttr().Get(),
                                'velocity_iterations':api.GetSolverVelocityIterationCountAttr().Get()}
            drive=UsdPhysics.DriveAPI.Get(self.stage.GetPrimAtPath(self.paths['spray_can']+'/button_slide'),'linear')
            readback['button_drive']={'stiffness_N_m':drive.GetStiffnessAttr().Get(),'damping_N_s_m':drive.GetDampingAttr().Get()}
            self.rest_drive_stiffness=float(readback['button_drive']['stiffness_N_m'])
            if (args.body_solver_32_8 or args.rest_solver=='32-8') and any(readback[name]!={'position_iterations':32,'velocity_iterations':8} for name in ('spray_can','button')):
                raise RuntimeError('passive-rest solver readback mismatch')
            (out/'body-physics-readback.json').write_text(json.dumps(readback,indent=2)+'\n')
            self.rest_samples=[];self.rest_hold=0.;self.rest_last_t=None;self.rest_initial_energy=None
            from yam_arena import YAM_URDF
            physical=physics_manifest(self.stage,self.native_assets,YAM_URDF,self._base.cfg.sim.dt,self._base.step_dt)
            (out/'physics-manifest.json').write_text(json.dumps(physical,indent=2)+'\n')
            if args.contact_diagnostic:
                from native_contact_reader import SENSOR_CONSTRUCTION_REQUIREMENTS
                readback={}
                for side in ('left','right'):
                    sensor=self._base.scene.sensors[side+'_contacts'];view=sensor.contact_view
                    actual={key:getattr(sensor.cfg,key) for key in SENSOR_CONSTRUCTION_REQUIREMENTS}
                    if actual!=SENSOR_CONSTRUCTION_REQUIREMENTS:raise RuntimeError('diagnostic sensor config mismatch')
                    readback[side]=dict(config=actual,sensor_paths=view.sensor_paths,filter_paths=view.filter_paths,
                        sensor_count=view.sensor_count,filter_count=view.filter_count,max_contact_data_count=view.max_contact_data_count)
                (out/'contact-diagnostic-readback.json').write_text(json.dumps(dict(physics_dt_s=float(self._base.cfg.sim.dt),sensors=readback),indent=2)+'\n')
            self.detached=args.stage=='press'
            self.tracker=SprayScorer()
            observation=super().reset(scene,seed=seed)
            # Export composed appearance once after settling. This writes a
            # separate layer only; it never edits the live physics stage.
            from yam_arena.robot import asset_link_paths
            self.replay_owners=native_body_owners(self._base.scene,asset_link_paths())
            for path in self.replay_owners:
                if not self.stage.GetPrimAtPath(path):raise RuntimeError('missing native replay owner '+path)
            scene_export=export_replay_scene(self.stage,out/'replay-scene.usdc')
            cameras=replay_camera_metadata(self.rig,self.replay_owners,self.cam_width,self.cam_height)
            replay=dict(**scene_export,
                        pose_order=['x','y','z','qx','qy','qz','qw'],quaternion_order='xyzw',pose_space='simulation_world',
                        native_pose_source='ArticulationData.body_link_pose_w actor frames and arena_world.get_pose_w; no URDF FK reconstruction',
                        capture_hz=20.,frame_zero='post-reset-settle at simulation t=0',interpolated=False,
                        owners=self.replay_owners,cameras=cameras,
                        surface_cells=[dict(index=i,prim_path=str(obj.GetPrim().GetPath()),target=target,
                            display_color_interpolation='uniform',face_vertex_counts=list(obj.GetFaceVertexCountsAttr().Get()))
                            for i,(obj,target,bases) in enumerate(self.tiles)],
                        appearance_updates='Per-row exact native displayColor writes, scorer dose and mist point positions; replay only, not real camera capture',
                        source_sha256=json.loads((out/'source-sha256.json').read_text()),state_only=args.no_video,media_eligible=False)
            (out/'replay-manifest.json').write_text(json.dumps(replay,indent=2)+'\n')
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
            cap,cap_rotation,cap_speed=state('cap');button,button_rotation,_=state('button')
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
                        cap_rotation=cap_rotation.tolist(),button_rotation=button_rotation.tolist(),
                        native_pose_quaternion_order='xyzw',native_body_world_poses=native_body_world_poses(self._base.scene,world,self.replay_owners),
                        hands_clear=all(min(np.linalg.norm(t-can),np.linalg.norm(t-cap))>.07 for t in hands))
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
            sample['metrics']=self.tracker.update(sample)
            gravity=getattr(self._base.cfg.sim,'gravity',(0.,0.,-9.81));bodies={};energy=0.
            for name,rotation in (('spray_can',rot),('button',button_rotation)):
                data=self._base.scene[name].data
                mass=float(array(data.body_mass).reshape(-1)[0]);inertia=array(data.body_inertia).reshape(-1).tolist()
                com_pose=array(data.root_com_pose_w)[0];velocity=array(data.root_com_vel_w)[0]
                kinetic=passive_body_energy(mass,inertia,rotation,com_pose,velocity,gravity)
                energy+=sum(kinetic.values())
                bodies[name]=dict(mass_kg=mass,inertia_actor_frame_column_major=inertia,com_pose_xyzw=com_pose.tolist(),
                                  com_linear_velocity_w=velocity[:3].tolist(),angular_velocity_w=velocity[3:].tolist(),**kinetic)
            sample['native_body_dynamics']=bodies
            spring=.5*self.rest_drive_stiffness*sample['button_travel']**2;energy+=spring
            if self.rest_initial_energy is None:self.rest_initial_energy=energy
            dt=0. if self.rest_last_t is None else self._t-self.rest_last_t;self.rest_last_t=self._t
            self.rest_hold=self.rest_hold+dt if can_speed<.02 and sample['upright']>=np.cos(np.radians(10.)) else 0.
            bottom=can[2]-.005*rot[2,2]-.065*abs(rot[2,2])-.026*np.sqrt(max(0.,1-rot[2,2]**2))
            rest=dict(bodies=bodies,tilt_deg=float(np.degrees(np.arccos(np.clip(rot[2,2],-1.,1.)))),
                      can_body_support_gap_m=float(bottom-(TOP+RISER_HEIGHT)),existing_criterion_hold_s=float(self.rest_hold),
                      total_mechanical_energy_J=energy,energy_change_from_first_sample_J=energy-self.rest_initial_energy,button_spring_energy_J=spring)
            if args.policy=='rest-probe':
                self.rest_samples.append(dict(time=float(self._t),can_speed=can_speed,**rest));sample['passive_rest']=rest
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
            sample['spray_mist_points']=[[float(v) for v in point] for point in points]
            sample['spray_surface_dose']=[float(value) for value in self.tracker.dose]
            sample['spray_surface_updates']=[]
            for i,(tile,target,bases) in enumerate(self.tiles):
                coat=min(1.,self.tracker.dose[i]/COAT_DOSE)
                if abs(coat-self.coat_cache[i])<1e-5:continue
                self.coat_cache[i]=coat
                colors=[Gf.Vec3f(*[(1-coat)*v+coat*b for v,b in zip(base,(.08,.3,.85))]) for base in bases]
                tile.GetDisplayColorAttr().Set(colors)
                sample['spray_surface_updates'].append(dict(index=i,colors=[[float(v) for v in color] for color in colors]))
            sample['controller']=telemetry.command
            sample['contacts']=self.contact_acc
            sample['contact_errors']=self.contact_errors
            if args.contact_diagnostic:
                from native_contact_reader import read_sensor_native_contacts,ContactReadError
                sample['native_contacts']={}
                for side,contact_sensor in (('left',left_sensor),('right',sensor)):
                    try:raw=read_sensor_native_contacts(contact_sensor,physics_dt=float(self._base.cfg.sim.dt))
                    except ContactReadError as error:raw=error.as_dict()
                    sample['native_contacts'][side]=raw
            self.contact_acc={}
            telemetry.latest=sample
            self.audit.write(json.dumps(sample,allow_nan=False)+'\n');self.audit.flush()
            return super()._task_step()

        def close(self):
            if hasattr(self,'audit'):
                self.audit.close()
                summary=self.tracker.result()
                if args.stage=='press' or args.contact_diagnostic:summary=dict(score=0.,diagnostic=True,milestones=summary)
                if args.no_video:summary.update(diagnostic=True,state_only=True,media_eligible=False)
                (out/'score-summary.json').write_text(json.dumps(summary,indent=2))
                if args.policy=='rest-probe' and self.rest_samples:
                    samples=self.rest_samples;final=samples[-1]
                    result=dict(diagnostic=True,task_score=0.,solver=args.rest_solver,samples=len(samples),duration_s=final['time'],
                                final=final,max_tilt_deg=max(s['tilt_deg'] for s in samples),max_speed_m_s=max(s['can_speed'] for s in samples),
                                existing_rest_criterion_held_final_1s=final['existing_criterion_hold_s']>=1.,
                                scope='passive can/button native state and rigid-body energy; no forces or actor-pose writes after reset; contact energy not represented')
                    (out/'passive-rest-summary.json').write_text(json.dumps(result,indent=2)+'\n')
            super().close()

    register('embodiment','uncap_spray_prototype')(SprayEmbodiment)
    policy=args.policy
    if policy in ('probe','rest-probe'):
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
    elif policy=='recorded-demo':
        from recorded_demo import register_policy
        policy=register_policy()
    elif policy=='demo':
        from demo_policy import register_policy
        policy=register_policy(cap_only=args.stage=='cap',press_only=args.stage=='press')
    diagnostic=args.no_video or args.policy in ('probe','capprobe') or (args.policy=='demo' and args.stage!='full')
    (out/'mode.json').write_text(json.dumps(dict(policy=args.policy,stage=args.stage,diagnostic=diagnostic,render_sync=args.render_sync,
                                               state_only=args.no_video,media_eligible=not diagnostic,contact_diagnostic=args.contact_diagnostic,physics_hz=args.physics_hz,body_solver_32_8=args.body_solver_32_8,recorded_clock_only=args.policy=='recorded-demo',passive_rest=args.policy=='rest-probe',rest_solver=args.rest_solver if args.policy=='rest-probe' else None)))
    return cli(['run','--embodiment','uncap_spray_prototype','--policy',policy,
                '-E',f'task={Path(__file__).parent / "task.py"}','-E','object_jitter=0',
                '-E','control_hz=20','-E','cam_width=320','-E','cam_height=176',
                '--instruction',INSTRUCTION,'--scorer','task_score',
                '--max-steps',str(args.max_steps),*([] if args.no_video else ['--store-frames']),'--seed','0',
                '--no-prompt','--grader','none','--log-dir',str(out)])

if __name__=='__main__':main()
