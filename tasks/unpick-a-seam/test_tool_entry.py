import unittest
import numpy as np
from scipy.spatial.transform import Rotation
from tool_entry import ToolEntryCompensation


class EntryTests(unittest.TestCase):
    def test_measured_grasp_maps_target_without_moving_object(self):
        rng=np.random.default_rng(31)
        for _ in range(100):
            hand_r=Rotation.random(random_state=rng);hand_p=rng.uniform(-1,1,3)
            tcp_offset=np.array([0.,0.,.134])
            grip_r=Rotation.random(random_state=rng);grip_p=tcp_offset+rng.uniform(-.02,.02,3)
            measured_hand=np.r_[hand_p,hand_r.as_quat()]
            measured_tool=np.r_[hand_p+hand_r.apply(grip_p),(hand_r*grip_r).as_quat()]
            target_r=Rotation.random(random_state=rng).as_matrix();target_p=rng.uniform(-1,1,3)
            controller=ToolEntryCompensation(tcp_offset)
            tcp,r=controller.target(target_p,target_r,measured_hand,measured_tool)
            reconstructed_hand_p=tcp-r@tcp_offset
            np.testing.assert_allclose(reconstructed_hand_p+r@grip_p,target_p,atol=1e-12)
            np.testing.assert_allclose(r@grip_r.as_matrix(),target_r,atol=1e-12)

    def test_noise_is_filtered_and_dropped_tool_is_rejected(self):
        controller=ToolEntryCompensation([0,0,.134]);hand=np.array([0,0,0,0,0,0,1.]);tool=hand.copy();tool[2]=.144
        controller.target([0,0,0],np.eye(3),hand,tool)
        tool[0]=.001;controller.target([0,0,0],np.eye(3),hand,tool)
        self.assertAlmostEqual(controller.translation[0],.0001)
        tool[0]=.02
        with self.assertRaises(RuntimeError):controller.target([0,0,0],np.eye(3),hand,tool)


if __name__=='__main__':unittest.main()
