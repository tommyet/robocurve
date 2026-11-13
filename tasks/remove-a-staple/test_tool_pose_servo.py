import unittest
import numpy as np
from scipy.spatial.transform import Rotation
from tool_pose_servo import compensate_grasp


class RemoverPoseCompensationTests(unittest.TestCase):
    def test_changed_grasp_still_targets_same_world_tool_pose(self):
        desired_p=np.array((.25,-.05,.78))
        desired_R=Rotation.from_rotvec((.1,.2,-.3)).as_matrix()
        reference_p=np.array((0.,-.043,.016));reference_R=np.diag((-1.,1.,-1.))
        actual_tool_p=np.array((.24,-.06,.79))
        actual_tool_R=Rotation.from_rotvec((-.2,.1,.4)).as_matrix()
        grip_p=reference_p+(.001,-.002,.001)
        grip_R=Rotation.from_rotvec((.06,0.,0.)).as_matrix()@reference_R
        measured_tcp=actual_tool_p+actual_tool_R@grip_p
        measured_R=actual_tool_R@grip_R
        p,R,_=compensate_grasp(desired_p+desired_R@reference_p,desired_R@reference_R,
            measured_tcp,measured_R,np.r_[actual_tool_p,Rotation.from_matrix(actual_tool_R).as_quat()],
            reference_p,reference_R)
        recovered_R=R@grip_R.T
        np.testing.assert_allclose(recovered_R,desired_R,atol=1e-12)
        np.testing.assert_allclose(p-recovered_R@grip_p,desired_p,atol=1e-12)

    def test_nonfinite_object_pose_is_rejected(self):
        with self.assertRaises(ValueError):
            compensate_grasp(np.zeros(3),np.eye(3),np.zeros(3),np.eye(3),
                np.full(7,np.nan),np.zeros(3),np.eye(3))
