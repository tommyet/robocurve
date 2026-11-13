import unittest
import numpy as np
from tool_pose_servo import compensated_tcp,nipple_alignment
from wheel_scene import quat,spoke_phase


class ToolPoseServoTests(unittest.TestCase):
    def test_square_symmetry_does_not_accumulate_wrist_turns(self):
        p=np.array((.3,.1,.9));reference=spoke_phase(.2)
        for quarter in range(4):
            actual=reference@spoke_phase(quarter*np.pi/2+.03)
            correction,diagnostic=nipple_alignment(p,reference,np.r_[p,quat(actual)])
            np.testing.assert_allclose(correction,spoke_phase(.03),atol=1e-12)
            self.assertAlmostEqual(diagnostic['orientation_correction_rad'],.03)

    def test_changed_grasp_preserves_requested_world_tool_target(self):
        tool_p=np.array((.3,.1,.9));tool_R=spoke_phase(.4)
        reference_p=np.array((0.,-.195,.011));reference_R=np.diag((1.,-1.,-1.))
        actual_grip_p=reference_p+np.array((.001,0.,.001))
        actual_grip_R=spoke_phase(.15)@reference_R
        actual_tool_p=np.array((.29,.12,.88));actual_tool_R=spoke_phase(.2)
        actual_p=actual_tool_p+actual_tool_R@actual_grip_p
        actual_R=actual_tool_R@actual_grip_R
        p,R,d=compensated_tcp(tool_p+tool_R@reference_p,tool_R@reference_R,
            actual_p,actual_R,np.r_[actual_tool_p,quat(actual_tool_R)],reference_p,reference_R)
        recovered_R=R@actual_grip_R.T;recovered_p=p-recovered_R@actual_grip_p
        np.testing.assert_allclose(recovered_R,tool_R,atol=1e-12)
        np.testing.assert_allclose(recovered_p,tool_p,atol=1e-12)
        self.assertGreater(d['current_tool_position_error_m'],0.)

    def test_invalid_pose_rejected(self):
        with self.assertRaises(ValueError):
            compensated_tcp(np.zeros(3),np.eye(3),np.zeros(3),np.eye(3),np.full(7,np.nan),np.zeros(3),np.eye(3))
