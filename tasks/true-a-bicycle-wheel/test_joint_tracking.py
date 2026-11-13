import unittest
import numpy as np
from joint_tracking import JointTracker


class JointTrackingTests(unittest.TestCase):
    def tracker(self):return JointTracker(np.zeros(14),-np.ones(14),np.ones(14),np.full(14,.025))
    def test_persistent_joint_error_has_bounded_compensation_and_no_gripper_offset(self):
        t=self.tracker();target=np.zeros(14);actual=np.full(14,-.2)
        last=np.zeros(14)
        for _ in range(200):
            q=t.command(target,actual)
            self.assertLessEqual(np.max(np.abs(q-last)),.025+1e-12);last=q
        self.assertTrue(np.allclose(q[np.arange(14)%7!=6],.12))
        self.assertTrue(np.all(q[[6,13]]==0.))
    def test_moving_target_does_not_integrate_normal_tracking_lag(self):
        t=self.tracker();q=t.command(np.full(14,.5),np.zeros(14))
        self.assertTrue(np.all(t.offset==0.));self.assertTrue(np.allclose(q,.025))
    def test_invalid_observation_cannot_produce_commands(self):
        t=self.tracker();bad=np.zeros(14);bad[0]=np.nan
        with self.assertRaises(ValueError):t.command(np.zeros(14),bad)
        self.assertTrue(np.all(t.previous==0.))


if __name__=='__main__':unittest.main()
