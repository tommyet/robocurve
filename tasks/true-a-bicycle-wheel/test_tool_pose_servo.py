import unittest
import numpy as np
from tool_pose_servo import compensated_tcp,nipple_alignment,ik_acceptance,orientations_settled,engagement_key,nipple_mouth_clearance_m,blended_nipple_target
from wheel_scene import quat,spoke_phase


class ToolPoseServoTests(unittest.TestCase):
    def test_clear_transition_feedback_has_exact_endpoints(self):
        p=np.array((.2,.3,.9));c=np.array((.35,0.,1.));actual=c+(.01,-.02,0.)
        R=spoke_phase(.2);C=spoke_phase(.12)
        zero=blended_nipple_target(p,R,c,actual,C,0.)
        full=blended_nipple_target(p,R,c,actual,C,1.)
        np.testing.assert_array_equal(zero[0],p);np.testing.assert_array_equal(zero[1],R)
        np.testing.assert_array_equal(full[0],actual+C@(p-c));np.testing.assert_array_equal(full[1],C@R)

    def test_clear_transition_blends_rotation_and_translation(self):
        c=np.array((.35,0.,1.));actual=c+(.01,-.02,0.);p=c+(0.,.1,0.)
        result=blended_nipple_target(p,np.eye(3),c,actual,spoke_phase(.2),.5)
        np.testing.assert_allclose(result[0],c+.5*(actual-c)+spoke_phase(.1)@(p-c),atol=1e-12)
        np.testing.assert_allclose(result[1],spoke_phase(.1),atol=1e-12)

    def test_clear_transition_rejects_unbounded_feedback_weights(self):
        for weight in (-.01,1.01,float('nan')):
            with self.assertRaises(ValueError):
                blended_nipple_target(np.zeros(3),np.eye(3),np.zeros(3),np.ones(3),np.eye(3),weight)

    def test_whole_square_must_clear_mouth_not_only_its_centre(self):
        tool=np.r_[np.zeros(3),quat(np.eye(3))]
        nipple=np.r_[np.array((0.,.009,0.)),quat(np.eye(3))]
        self.assertLess(nipple_mouth_clearance_m(tool,nipple),0.)
        nipple[1]=.016
        self.assertAlmostEqual(nipple_mouth_clearance_m(tool,nipple),.006385)
        # Simultaneous world translation/rotation cannot change engagement.
        R=spoke_phase(.7);shift=np.array((.3,.2,1.))
        shifted_tool=np.r_[shift,quat(R)]
        shifted_nipple=np.r_[shift+R@nipple[:3],quat(R)]
        self.assertAlmostEqual(nipple_mouth_clearance_m(shifted_tool,shifted_nipple),.006385)

    def test_clear_approach_and_contact_keep_one_latched_orientation(self):
        stages=('Clear approach nipple 0','Approach nipple 0','Approach nipple 0 settle',
                'Nipple 0 quarter 1 insert','Nipple 0 quarter 1 tighten','Nipple 0 quarter 1 disengage')
        self.assertEqual({engagement_key(0,stage) for stage in stages},{(0,1)})
        self.assertEqual(engagement_key(0,'Nipple 0 quarter 2 insert'),(0,2))
        self.assertEqual(engagement_key(2,'Approach nipple 2'),(2,1))
    def test_clear_long_lead_in_uses_actual_whole_square_clearance(self):
        accepted,quality=ik_acceptance('Approach nipple 0',.000805,.00225,.0008,solved_mouth_clearance_m=.005)
        self.assertTrue(accepted);self.assertEqual(quality['mode'],'clear_lead_in')
        self.assertFalse(ik_acceptance('Approach nipple 0',.000805,.00225,.0008,solved_mouth_clearance_m=.001)[0])
        self.assertTrue(ik_acceptance('Nipple 0 quarter 1 insert',.000805,.00225,.0008,solved_mouth_clearance_m=.005)[0])
        self.assertFalse(ik_acceptance('Nipple 0 quarter 1 insert',.000805,.00225,.0008,solved_mouth_clearance_m=.001)[0])
        self.assertFalse(ik_acceptance('Nipple 0 quarter 1 tighten',.000805,.00225,.0008,solved_mouth_clearance_m=.005)[0])
        self.assertTrue(ik_acceptance('Nipple 0 quarter 1 insert',.00045,.00126,.00044,solved_mouth_clearance_m=.001)[0])
        self.assertFalse(ik_acceptance('Nipple 0 quarter 1 insert',.00045,.00126,.00044,solved_mouth_clearance_m=-.001)[0])
    def test_approach_realign_waits_for_stable_observed_orientation(self):
        self.assertFalse(orientations_settled([spoke_phase(0.)]*4))
        self.assertFalse(orientations_settled([spoke_phase(a) for a in (0.,.5,.4,.01,.005)]))
        self.assertTrue(orientations_settled([spoke_phase(a) for a in (.005,.004,.003,.002,.001)]))
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

    def test_small_approach_residual_fits_flared_mouth(self):
        accepted,quality=ik_acceptance('Approach nipple 0',.000601,.001685,.000585)
        self.assertTrue(accepted)
        self.assertEqual(quality['mode'],'lead_in')
        self.assertLess(quality['jaw_error_bound_m'],.00075)

    def test_capture_allowance_does_not_apply_to_insert_or_turn(self):
        for stage in ('Nipple 0 quarter 1 insert','Nipple 0 quarter 1 tighten','Clear approach nipple 0'):
            self.assertFalse(ik_acceptance(stage,.000601,.001685,.000585)[0])

    def test_approach_error_outside_reserved_capture_is_rejected(self):
        self.assertFalse(ik_acceptance('Approach nipple 0',.0008,.001,.00075)[0])
        self.assertFalse(ik_acceptance('Approach nipple 0',.0001,.011,0.)[0])
        self.assertFalse(ik_acceptance('Approach nipple 0',float('nan'),0.,0.)[0])

    def test_measured_096_residual_fits_same_reserved_jaw_envelope(self):
        accepted,quality=ik_acceptance('Approach nipple 0 settle',
            .0007444145836,.0020857919752,.0007253163071)
        self.assertTrue(accepted)
        self.assertLess(quality['jaw_error_bound_m'],.00075)
        self.assertFalse(ik_acceptance('Nipple 0 quarter 1 tighten',
            .0007444145836,.0020857919752,.0007253163071)[0])
