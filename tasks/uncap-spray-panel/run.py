"""Prototype native mechanics runner. No successful robot demo exists yet."""
import argparse
import atexit
import hashlib
import json
import os
from pathlib import Path
from config import *
from scoring import SprayScorer


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy',choices=['probe','capprobe','demo','dream'],default='probe')
    parser.add_argument('--stage',choices=['cap','press','full'],default='full')
    parser.add_argument('--max-steps',type=int,default=2400)
    parser.add_argument('--log-dir',type=Path,required=True)
    args=parser.parse_args()
    if not 1 <= args.max_steps <= 2400:parser.error('max-steps must be 1..2400')
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
        def _ensure_sim(self,goal):
            if self._env is not None and goal == self._goal:return
            from yam_arena import inspect_embodiment as adapter
            if adapter._APP is None:
                os.environ.setdefault('OMNI_KIT_ACCEPT_EULA','YES')
                from isaaclab.app import AppLauncher
                adapter._APP=AppLauncher(headless=True,device=self.device,enable_cameras=True).app
                atexit.register(adapter._close_app_at_exit)
            from yam_arena import scene as sc
            from yam_arena.embodiment import BimanualYamEmbodiment
            original_init=BimanualYamEmbodiment.__init__
            def sensor_init(instance,*a,**kw):
                kw['contact_sensors']=True
                original_init(instance,*a,**kw)
                stem=instance.scene_config.left_contacts.prim_path.rsplit('/.*',1)[0]
                instance.scene_config.right_contacts.filter_prim_paths_expr=[
                    '{ENV_REGEX_NS}/spray_can','{ENV_REGEX_NS}/button',
                    *[stem+instance.link_paths[n] for n in ('gripper','tip_left','tip_right')]]
            BimanualYamEmbodiment.__init__=sensor_init
            import isaaclab.sim as sim
            from mechanics import asset,stand_asset
            assets={name:asset(out/(name+'.usda'),name) for name in ('spray_can','cap','button')}
            assets['stand']=stand_asset(out/'stand.usda')
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
            self.contact_acc={}
            telemetry.latest=sample
            self.audit.write(json.dumps(sample,allow_nan=False)+'\n');self.audit.flush()
            return super()._task_step()

        def close(self):
            if hasattr(self,'audit'):
                self.audit.close()
                summary=self.tracker.result()
                if args.stage=='press':summary=dict(score=0.,diagnostic=True,milestones=summary)
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
    diagnostic=args.policy in ('probe','capprobe') or (args.policy=='demo' and args.stage!='full')
    (out/'mode.json').write_text(json.dumps(dict(policy=args.policy,stage=args.stage,diagnostic=diagnostic)))
    return cli(['run','--embodiment','uncap_spray_prototype','--policy',policy,
                '-E',f'task={Path(__file__).parent / "task.py"}','-E','object_jitter=0',
                '-E','control_hz=20','-E','cam_width=320','-E','cam_height=176',
                '--instruction',INSTRUCTION,'--scorer','task_score',
                '--max-steps',str(args.max_steps),'--store-frames','--seed','0',
                '--no-prompt','--grader','none','--log-dir',str(out)])

if __name__=='__main__':main()
