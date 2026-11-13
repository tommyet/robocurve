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
    def test_feedforward_cancels_native_damping_for_constant_velocity(self):
        # A correctly tracking joint moving at0.4rad/s should need zero net
        # PD torque from the reference trajectory, rather than braking atD*v.
        ratio=np.tile([5/80]*3+[1.5/10]*3+[0.],2)
        t=JointTracker(np.zeros(14),-np.ones(14),np.ones(14),np.ones(14),gain=0,
                       damping_over_stiffness_s=ratio)
        velocity=np.full(14,.4);velocity[[6,13]]=0
        target=velocity*t.dt
        command=t.command(target,target)
        stiffness=np.tile([80]*3+[10]*3+[1],2)
        damping=ratio*stiffness
        self.assertTrue(np.allclose(stiffness*(command-target)-damping*velocity,0))
        self.assertTrue(np.all(command[[6,13]]==0))
    def test_feedforward_preserves_total_offset_rate_and_position_bounds(self):
        ratio=np.tile([.0625]*3+[.15]*3+[0.],2)
        t=JointTracker(np.zeros(14),-np.ones(14),np.ones(14),np.full(14,.025),
                       damping_over_stiffness_s=ratio)
        target=np.full(14,.99);command=t.command(target,np.zeros(14))
        self.assertTrue(np.all(np.abs(command)<=.025+1e-12))
        self.assertTrue(np.all(np.abs(t.last['total_correction_rad'])<=.12+1e-12))
        self.assertTrue(np.all(target+np.array(t.last['total_correction_rad'])<=1))
        self.assertTrue(np.all(np.array(t.last['velocity_feedforward_rad'])[[6,13]]==0))
    def test_feedforward_drops_to_zero_when_target_holds(self):
        ratio=np.tile([.0625]*3+[.15]*3+[0.],2)
        t=JointTracker(np.zeros(14),-np.ones(14),np.ones(14),np.ones(14),gain=0,
                       damping_over_stiffness_s=ratio)
        target=np.full(14,.02)
        t.command(target,target)
        self.assertTrue(np.allclose(t.command(target,target),target))


if __name__=='__main__':unittest.main()
