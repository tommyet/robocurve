import unittest
from dataclasses import dataclass
from types import SimpleNamespace as N
import numpy as np
import coordinate_frame as frame


@dataclass(frozen=True)
class Pose:
    position_xyz:tuple
    rotation_xyzw:tuple=(0.,0.,0.,1.)


class CoordinateTests(unittest.TestCase):
    def tearDown(self):frame.configure(False)

    def test_world_roots_and_fixed_view_shift_together_once(self):
        frame.configure(True)
        root=lambda p:N(prim_path='/World/object',init_state=N(pos=p))
        cam=lambda p:N(prim_path='/World/camera',offset=N(pos=p))
        pose=Pose((.303,0.,.8737));params={'pose':pose,'asset_cfg':N(name='jaw'),'velocity':None}
        cfg=N(scene=N(left_robot=root((0.,.3,.75)),right_robot=root((0.,-.3,.75)),
            table=root((.36,0.,.7175)),top_cam=cam((.3,0.,1.5)),
            jaw=root(pose.position_xyz),
            left_cam=cam((.01,.02,.03)),right_cam=cam((.01,.02,.03)),
            cloth=N(rigid_objects={'panel':root((.3,0.,.81))})),
            events=N(jaw=N(mode='reset',params=params),
                     cloth=N(mode='reset',params={'shell_name':'cloth'})))
        frame.shift_scene_config(cfg);frame.shift_scene_config(cfg)
        np.testing.assert_allclose(cfg.scene.right_robot.init_state.pos,(-.3,-.3,-.0627),atol=1e-14)
        np.testing.assert_allclose(cfg.scene.top_cam.offset.pos,(0.,0.,.6873),atol=1e-14)
        np.testing.assert_array_equal(cfg.scene.left_cam.offset.pos,(.01,.02,.03))
        # Collections have their own translated authored/reset poses.
        np.testing.assert_array_equal(cfg.scene.cloth.rigid_objects['panel'].init_state.pos,(.3,0.,.81))
        np.testing.assert_allclose(cfg.events.jaw.params['pose'].position_xyz,
                                   cfg.scene.jaw.init_state.pos,rtol=0,atol=1e-15)
        self.assertEqual(pose.position_xyz,(.303,0.,.8737))
        self.assertIs(params['pose'],pose)
        self.assertEqual(cfg.events.jaw.params['pose'].rotation_xyzw,pose.rotation_xyzw)
        self.assertEqual(sum(row['kind']=='world_reset_pose' for row in frame.CONFIG_AUDIT),1)
        p=np.array((.29558279,.027,.8127))
        np.testing.assert_allclose(frame.to_station(frame.to_native(p)),p,atol=1e-15)


if __name__=='__main__':unittest.main()
