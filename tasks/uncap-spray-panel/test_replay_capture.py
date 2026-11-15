"""Output-only replay captures actual native poses, optical rig and composed USD."""
from dataclasses import asdict
import hashlib
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import numpy as np

spec=importlib.util.spec_from_file_location('_spray_replay_runner',Path(__file__).with_name('run.py'))
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)


class Array:
    def __init__(self,value):self.value=np.asarray(value)
    def detach(self):return self
    def cpu(self):return self
    def numpy(self):return self.value


class NativeReplayTests(unittest.TestCase):
    def fixture(self):
        names=['base','link1','link2','link3','link4','link5','gripper','tip_left','tip_right']
        paths={name:'/links/'+name for name in names}
        paths['tip_left']='/links/gripper/tip_left';paths['tip_right']='/links/gripper/tip_right'
        scene={}
        for index,side in enumerate(('left','right')):
            poses=np.zeros((1,9,7),dtype=np.float32);poses[0,:,:3]=np.arange(27).reshape(9,3)+index*100
            poses[0,:,6]=1.
            scene[side+'_robot']=SimpleNamespace(body_names=names.copy(),data=SimpleNamespace(body_link_pose_w=SimpleNamespace(torch=Array(poses))))
        q=np.array([0,0,np.sin(.4),np.cos(.4)])
        objects={name:np.r_[[.2,.1,.8+i*.04],q] for i,name in enumerate(('spray_can','cap','button'))}
        world=SimpleNamespace(get_pose_w=lambda name:Array([objects[name]]))
        return scene,world,paths,objects

    def test_all21_poses_use_native_actor_frames_and_real_cap_button_orientation(self):
        scene,world,paths,objects=self.fixture();owners=runner.native_body_owners(scene,paths)
        result=runner.native_body_world_poses(scene,world,owners)
        self.assertEqual(len(result),21)
        path='/World/envs/env_0/LeftArm/links/link3'
        np.testing.assert_array_equal(result[path],scene['left_robot'].data.body_link_pose_w.torch.value[0,3])
        for name in ('cap','button'):
            np.testing.assert_array_equal(result['/World/envs/env_0/'+name],objects[name])
            self.assertNotEqual(result['/World/envs/env_0/'+name][5],0.)
        self.assertEqual(owners['/World/envs/env_0/LeftArm/links/gripper/tip_left']['parent_body_owner'],
                         '/World/envs/env_0/LeftArm/links/gripper')

    def test_invalid_or_reordered_native_state_fails_instead_of_using_fk(self):
        for invalid in ('nan','quaternion','shape','order'):
            scene,world,paths,objects=self.fixture();owners=runner.native_body_owners(scene,paths)
            array=scene['left_robot'].data.body_link_pose_w.torch.value
            if invalid=='nan':array[0,0,0]=np.nan
            if invalid=='quaternion':array[0,0,6]=0.
            if invalid=='shape':scene['left_robot'].data.body_link_pose_w.torch.value=array[:,:8]
            if invalid=='order':scene['left_robot'].body_names.reverse()
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):runner.native_body_world_poses(scene,world,owners)

    def test_body_owner_names_follow_installed_asset_paths_and_native_indices(self):
        scene,world,paths,objects=self.fixture()
        scene['left_robot'].body_names.reverse()
        owners=runner.native_body_owners(scene,paths)
        self.assertEqual(owners['/World/envs/env_0/LeftArm'+paths['tip_right']]['body_index'],0)
        scene['right_robot'].body_names.pop()
        with self.assertRaises(ValueError):runner.native_body_owners(scene,paths)

    def test_camera_calibration_is_the_pinned_rig_with_actual_gripper_parents(self):
        try:from yam_arena.station import rig
        except ModuleNotFoundError:self.skipTest('pinned YAM source required')
        scene,world,paths,objects=self.fixture();owners=runner.native_body_owners(scene,paths);actual=rig('calibrated')
        metadata=runner.replay_camera_metadata(actual,owners,320,176)
        self.assertEqual(metadata['quaternion_order'],'xyzw')
        self.assertEqual(metadata['native_render_width'],640);self.assertEqual(metadata['native_render_height'],360)
        top=metadata['cameras']['top_cam'];self.assertIsNone(top['parent_body_owner'])
        for key,value in asdict(actual.top_cam).items():self.assertEqual(top[key],value)
        for side in ('left','right'):
            camera=metadata['cameras'][side+'_cam']
            self.assertEqual(camera['parent_body_owner'],f'/World/envs/env_0/{side.capitalize()}Arm'+paths['gripper'])
            for key,value in asdict(actual.wrist_cams[side]).items():self.assertEqual(camera[key],value)

    def test_scene_export_is_output_only_and_reports_external_assets(self):
        calls=[]
        class Layer:
            def Export(self,path):calls.append(('export',path));Path(path).write_bytes(b'composed test layer');return True
            def GetExternalAssetDependencies(self):return ['texture.png','material.mdl']
        class Stage:
            def Flatten(self):calls.append(('flatten',));return Layer()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'replay-scene.usdc';result=runner.export_replay_scene(Stage(),path)
            self.assertEqual(result['scene_sha256'],hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(result['scene_file'],'replay-scene.usdc')
            self.assertEqual(result['external_asset_dependencies'],['material.mdl','texture.png'])
        self.assertEqual([call[0] for call in calls],['flatten','export'])


if __name__=='__main__':unittest.main()
