"""State-only CLI/observation contracts and camera-independent physics proofs."""
import ast
from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType,SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np

PATH=Path(__file__).with_name('run.py')
spec=importlib.util.spec_from_file_location('_spray_run_test',PATH)
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)


class Array:
    def __init__(self,value):self.value=np.array(value)
    def detach(self):return self
    def cpu(self):return self
    def numpy(self):return self.value


class StateOnlyTests(unittest.TestCase):
    def test_invalid_modes_fail_before_output_or_runtime_creation(self):
        for extra in (['--policy','dream'],['--policy','probe'],['--policy','demo','--render-sync']):
            with tempfile.TemporaryDirectory() as directory:
                out=Path(directory)/'must-not-exist'
                result=subprocess.run([sys.executable,str(PATH),'--no-video','--log-dir',str(out),*extra],capture_output=True,text=True)
                self.assertEqual(result.returncode,2);self.assertIn('--no-video',result.stderr)
                self.assertFalse(out.exists())

    def test_real_joint_state_observation_has_no_camera_reads_or_fake_images(self):
        try:from yam_arena.constants import FINGER_OPEN
        except ModuleNotFoundError:self.skipTest('pinned YAM source required')
        @dataclass
        class Info:observation_space:object=None
        class Base:
            def __init__(self):self.info=Info();self.cam_height=176;self.cam_width=320
        config=ModuleType('inspect_robots_yam.config');config.observation_space=lambda h,w,cameras:(h,w,cameras)
        types=ModuleType('inspect_robots.types');types.Observation=SimpleNamespace
        packing=ModuleType('inspect_robots_yam.packing');packing.STATE_KEY='joint_pos'
        modules={'inspect_robots':ModuleType('inspect_robots'),'inspect_robots.types':types,
                 'inspect_robots_yam':ModuleType('inspect_robots_yam'),'inspect_robots_yam.config':config,
                 'inspect_robots_yam.packing':packing}
        tree=ast.parse(PATH.read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        cls=next(n for n in main.body if isinstance(n,ast.ClassDef) and n.name=='SprayEmbodiment')
        namespace=dict(YamArenaEmbodiment=Base,args=SimpleNamespace(no_video=True),joint_observation_state=runner.joint_observation_state)
        with patch.dict(sys.modules,modules):
            exec(compile(ast.Module(body=[cls],type_ignores=[]),str(PATH),'exec'),namespace)
            instance=namespace['SprayEmbodiment']()
            instance._ids={name:([0,1,2,3,4,5],[6,7]) for name in ('left_robot','right_robot')}
            scene={'left_robot':SimpleNamespace(data=SimpleNamespace(joint_pos=SimpleNamespace(torch=Array([[1,2,3,4,5,6,FINGER_OPEN,FINGER_OPEN]])))),
                   'right_robot':SimpleNamespace(data=SimpleNamespace(joint_pos=Array([[6,5,4,3,2,1,FINGER_OPEN/2,FINGER_OPEN/2]])))}
            instance._base=SimpleNamespace(scene=scene);instance._instruction='state only';instance._t=1.25
            observation=instance._observation()
        self.assertEqual(instance.info.observation_space,(176,320,()))
        self.assertEqual(observation.images,{});self.assertEqual(observation.image_times,{})
        np.testing.assert_allclose(observation.state['joint_pos'],[1,2,3,4,5,6,1,6,5,4,3,2,1,.5])
        self.assertEqual(observation.state_time,1.25);self.assertEqual(observation.instruction,'state only')

    def test_cli_does_not_request_frames_and_marks_media_ineligible(self):
        try:import yam_arena
        except ModuleNotFoundError:self.skipTest('pinned YAM source required')
        called=[]
        modules={name:ModuleType(name) for name in ('inspect_robots','inspect_robots.cli','inspect_robots.registry','yam_arena.inspect_embodiment','demo_policy')}
        modules['inspect_robots.cli'].main=lambda args:called.append(args) or 0
        modules['inspect_robots.registry'].register=lambda *a:lambda value:value
        modules['yam_arena.inspect_embodiment'].YamArenaEmbodiment=object
        modules['demo_policy'].register_policy=lambda **kw:'scripted-test'
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'run'
            with patch.dict(sys.modules,modules),patch.object(sys,'argv',[str(PATH),'--policy','demo','--no-video','--max-steps','1','--log-dir',str(out)]):runner.main()
            mode=json.loads((out/'mode.json').read_text())
            self.assertTrue(mode['state_only']);self.assertTrue(mode['diagnostic']);self.assertFalse(mode['media_eligible'])
            self.assertNotIn('--store-frames',called[0]);self.assertFalse((out/'frames').exists())


class Prim:
    def __init__(self,path,kind,schemas=(),attributes=None):self.path=path;self.kind=kind;self.schemas=schemas;self.attributes=attributes or {}
    def GetPath(self):return self.path
    def GetTypeName(self):return self.kind
    def GetAppliedSchemas(self):return self.schemas
    def GetAttributes(self):return [SimpleNamespace(GetName=lambda k=k:k,Get=lambda v=v:v) for k,v in self.attributes.items()]
    def GetRelationships(self):return []


class PhysicsManifestTests(unittest.TestCase):
    def test_camera_changes_do_not_change_physics_but_materials_gains_and_dt_do(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);urdf=root/'robot.urdf';mesh=root/'mesh.stl';asset=root/'can.usda'
            mesh.write_bytes(b'pinned collision');asset.write_text('native physics')
            urdf.write_text('<robot><link><collision><geometry><mesh filename="mesh.stl"/></geometry></collision></link></robot>')
            body=Prim('/robot','Mesh',['PhysicsCollisionAPI','PhysicsRigidBodyAPI','PhysicsMassAPI'],{'physics:mass':.25})
            material=Prim('/material','Material',['PhysicsMaterialAPI'],{'physics:staticFriction':.8})
            joint=Prim('/joint','PhysicsRevoluteJoint',[],{'drive:angular:physics:damping':80.,'physxJoint:maxJointVelocity':2.})
            def manifest(extra=(),dt=1/240):return runner.physics_manifest(SimpleNamespace(Traverse=lambda:iter([body,material,joint,*extra])),{'can':asset},urdf,dt,.05)
            baseline=manifest();camera=manifest([Prim('/camera','Camera')])
            self.assertEqual(baseline['physical_input_sha256'],camera['physical_input_sha256'])
            self.assertEqual(baseline['body_joint_mass_sha256'],camera['body_joint_mass_sha256'])
            material.attributes['physics:staticFriction']=.9
            self.assertNotEqual(baseline['body_joint_mass_sha256'],manifest()['body_joint_mass_sha256'])
            material.attributes['physics:staticFriction']=.8;joint.attributes['physxJoint:maxJointVelocity']=3.
            self.assertNotEqual(baseline['body_joint_mass_sha256'],manifest()['body_joint_mass_sha256'])
            self.assertNotEqual(baseline['physical_input_sha256'],manifest(dt=1/120)['physical_input_sha256'])
            mesh.write_bytes(b'changed collision')
            self.assertNotEqual(baseline['physical_input_sha256'],manifest()['physical_input_sha256'])


if __name__=='__main__':unittest.main()
