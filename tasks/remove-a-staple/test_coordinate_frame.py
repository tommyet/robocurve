"""Prevent a precision fix from changing camera geometry or robot reach."""
from types import SimpleNamespace as NS
import unittest
import numpy as np
import coordinate_frame as frame


class CoordinateFrameTests(unittest.TestCase):
    def tearDown(self):frame.configure(False)

    def test_roots_shift_once_without_moving_wrist_mounts_or_shared_defaults(self):
        frame.configure(True)
        shared=NS(pos=(.1,.2,.8))
        scene=NS(left_robot=NS(prim_path='/env/LeftArm',init_state=shared),
            right_robot=NS(prim_path='/env/RightArm',init_state=shared),
            table=NS(prim_path='/env/table',init_state=NS(pos=(.3,0.,.7275))),
            top_cam=NS(prim_path='/env/TopCam',offset=NS(pos=(.4,0.,1.2))),
            left_cam=NS(prim_path='/env/LeftArm/gripper/cam',offset=NS(pos=(.02,.01,0.))),
            right_cam=NS(prim_path='/env/RightArm/gripper/cam',offset=NS(pos=(.02,.01,0.))),
            hardware=NS(rigid_objects={}))
        cfg=frame.shift_scene_config(NS(scene=scene))
        frame.shift_scene_config(cfg)
        np.testing.assert_allclose(cfg.scene.left_robot.init_state.pos,(-.22,.2,.0325))
        np.testing.assert_allclose(cfg.scene.top_cam.offset.pos,(.08,0.,.4325))
        self.assertEqual(shared.pos,(.1,.2,.8))
        self.assertEqual(cfg.scene.left_cam.offset.pos,(.02,.01,0.))
        points=np.array(((.227,-.05,.76774),(.32,0.,.76755)))
        np.testing.assert_allclose(frame.to_station(frame.to_native(points)),points)
        np.testing.assert_allclose(np.diff(frame.to_native(points),axis=0),np.diff(points,axis=0))

    def test_missing_camera_or_base_fails_before_simulation(self):
        frame.configure(True)
        with self.assertRaisesRegex(ValueError,'Required world-root'):
            frame.shift_scene_config(NS(scene=NS()))


if __name__=='__main__':unittest.main()
