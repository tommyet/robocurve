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
    parser.add_argument('--policy',choices=['probe','capprobe','dream'],default='probe')
    parser.add_argument('--max-steps',type=int,default=2400)
    parser.add_argument('--log-dir',type=Path,required=True)
    args=parser.parse_args()
    if not 1 <= args.max_steps <= 2400:parser.error('max-steps must be 1..2400')
    out=args.log_dir.expanduser().resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'source').mkdir()
    sources=list(Path(__file__).parent.glob('*.py'))
    for source in sources:(out/'source'/source.name).write_bytes(source.read_bytes())
    (out/'source-sha256.json').write_text(json.dumps(
        {s.name:hashlib.sha256(s.read_bytes()).hexdigest() for s in sources},indent=2))
    import numpy as np
    from inspect_robots.cli import main as cli
    from inspect_robots.registry import register
    from yam_arena.inspect_embodiment import YamArenaEmbodiment
    from yam_arena.urdf import quat_xyzw_to_matrix
    from yam_arena import ik

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
            import isaaclab.sim as sim
            from mechanics import asset
            assets={name:asset(out/(name+'.usda'),name) for name in ('spray_can','cap','button')}
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
                        joints(prim.GetStage(),parent+'/spray_can',parent+'/cap',parent+'/button')
                        return prim
                    cfg.func=spawn
                return sc.Object(name=spec.name,object_type=sc.ObjectType.RIGID,
                    spawner_cfg=cfg,
                    initial_pose=sc.Pose(position_xyz=tuple(spec.pos),rotation_xyzw=(0.,0.,0.,1.)))
            sc.task_object=make
            try:super()._ensure_sim(goal)
            finally:sc.task_object=original

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
                if not self.stage.GetPrimAtPath(self.paths['spray_can']+'/'+suffix):
                    raise RuntimeError('missing native joint '+suffix)
            self.joints_installed=True
            # Surface-only colour tiles. They have no colliders and cannot
            # help the robot manipulate either the cap or the can.
            self.tiles=[]
            for i,p,target in SprayScorer.cells():
                obj=box(self.stage,f'/World/spray_surface/cell_{i}',
                        (.0001,CELL*.98,CELL*.98),(TARGET_X-.0001,p[1],p[2]),
                        (.95,.95,.95) if target else (.55,.52,.48),False)
                self.tiles.append((obj,target))

        def _reset_with_joints(self,scene,seed):
            # _ensure_sim spawns both native joints before reset settles.
            self._ensure_sim(None)
            self._ensure_joints()
            self.detached=False
            self.tracker=SprayScorer()
            observation=super().reset(scene,seed=seed)
            self.task.module._tracker=self.tracker
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
            hands=[]
            for side in ('left','right'):
                name=side+'_robot';robot=self._base.scene[name];ids,_=self._ids[name]
                q=array(robot.data.joint_pos)[0]
                tcp,_=ik.tcp_pose(q[ids],self.rig.bases[side]);hands.append(tcp)
            sample=dict(time=float(self._t),can=can.tolist(),cap=cap.tolist(),
                        nozzle=(button+rot@np.array((.009,0.,0.))).tolist(),axis=rot[:,0].tolist(),
                        button_travel=float(.077-button_local[2]),cap_detached=self.detached,
                        upright=float(rot[2,2]),can_speed=can_speed,cap_speed=cap_speed,
                        hand_tcp=[t.tolist() for t in hands],
                        hands_clear=all(min(np.linalg.norm(t-can),np.linalg.norm(t-cap))>.07 for t in hands))
            sample['metrics']=self.tracker.update(sample)
            from pxr import Gf
            for i,(tile,target) in enumerate(self.tiles):
                coat=min(1.,self.tracker.dose[i]/COAT_DOSE)
                base=(.95,.95,.95) if target else (.55,.52,.48)
                tile.GetDisplayColorAttr().Set([Gf.Vec3f(*[(1-coat)*v+coat*b for v,b in zip(base,(.08,.3,.85))])])
            self.audit.write(json.dumps(sample,allow_nan=False)+'\n');self.audit.flush()
            return super()._task_step()

        def close(self):
            if hasattr(self,'audit'):
                self.audit.close()
                (out/'score-summary.json').write_text(json.dumps(self.tracker.result(),indent=2))
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
    (out/'mode.json').write_text(json.dumps(dict(policy=args.policy,diagnostic=args.policy!='dream')))
    return cli(['run','--embodiment','uncap_spray_prototype','--policy',policy,
                '-E',f'task={Path(__file__).parent / "task.py"}','-E','object_jitter=0',
                '-E','control_hz=20','-E','cam_width=320','-E','cam_height=176',
                '--instruction',INSTRUCTION,'--scorer','task_score',
                '--max-steps',str(args.max_steps),'--store-frames','--seed','0',
                '--no-prompt','--grader','none','--log-dir',str(out)])

if __name__=='__main__':main()
