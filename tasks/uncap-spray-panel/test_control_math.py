import unittest
import numpy as np
from control_math import grip_fraction,ramp_translation,can_frame_ramp_translation,transport_can_reference,release_command_target,actual_face_tcp_target


class GripperUnitTests(unittest.TestCase):
    def test_open_closed_and_loaded_grasp_units(self):
        self.assertEqual(grip_fraction(-.04695,-.04695),1.)
        self.assertEqual(grip_fraction(0.,-.04695),0.)
        self.assertAlmostEqual(grip_fraction(-.021,-.04695),.447284345,places=8)

    def test_original_positive_finger_bug_is_rejected(self):
        with self.assertRaises(ValueError):grip_fraction(.024,-.04695)

    def test_out_of_range_command_is_rejected(self):
        with self.assertRaises(ValueError):grip_fraction(-.06,-.04695)

class CanFrameFollowingTests(unittest.TestCase):
    def test_stationary_can_and_uninitialized_pose_keep_existing_ramp(self):
        current=np.array((.2,.3,.4));target=current+[.02,-.01,.03];pose=(np.zeros(3),np.eye(3))
        expected=ramp_translation(current,target,.01,.05)
        np.testing.assert_allclose(can_frame_ramp_translation(current,target,pose,pose,.01,.05),expected,atol=1e-15)
        np.testing.assert_allclose(can_frame_ramp_translation(current,target,None,([1,2,3],np.eye(3)),.01,.05),expected,atol=1e-15)

    def test_rigid_translation_and_rotation_carry_without_relative_stroke(self):
        angle=.4;R=np.array(((np.cos(angle),-np.sin(angle),0),(np.sin(angle),np.cos(angle),0),(0,0,1)))
        c0=np.array((.2,.1,.9));c1=np.array((.201,.098,.903));current=c0+[.01,-.02,.1]
        carried=c1+R@(current-c0)
        result=can_frame_ramp_translation(current,carried,(c0,np.eye(3)),(c1,R),.01,.05)
        np.testing.assert_allclose(result,carried,atol=1e-15)
        # World change exceeds the allowed relative stroke but is can motion.
        self.assertGreater(np.linalg.norm(carried-current),.0005)
        np.testing.assert_allclose(R.T@(result-c1),current-c0,atol=1e-15)

    def test_relative_increment_is_bounded_and_equivariant_in_world_frame(self):
        a=.6;R=np.array(((np.cos(a),0,np.sin(a)),(0,1,0),(-np.sin(a),0,np.cos(a))))
        c0=np.array((.2,-.1,.9));c1=c0+[0,.002,-.001];current=c0+[.03,.02,.1]
        carried=c1+R@(current-c0);goal=carried+[0,0,-.01]
        result=np.array(can_frame_ramp_translation(current,goal,(c0,np.eye(3)),(c1,R),.01,.05))
        self.assertAlmostEqual(np.linalg.norm(result-carried),.0005)
        b=.7;Q=np.array(((1,0,0),(0,np.cos(b),-np.sin(b)),(0,np.sin(b),np.cos(b))));shift=np.array((1,2,3))
        transformed=can_frame_ramp_translation(Q@current+shift,Q@goal+shift,(Q@c0+shift,Q),(Q@c1+shift,Q@R),.01,.05)
        np.testing.assert_allclose(transformed,Q@result+shift,atol=1e-15)

    def test_release_transport_stationary_identity_and_world_se3_covariance(self):
        p=np.array((.26,-.02,.95));R=np.eye(3);C=np.array((.26,0,.86))
        actual,rotation=transport_can_reference(p,R,(C,R),(C,R))
        np.testing.assert_allclose(actual,p,atol=1e-15);np.testing.assert_array_equal(rotation,R)
        a=.3;Q=np.array(((np.cos(a),-np.sin(a),0),(np.sin(a),np.cos(a),0),(0,0,1)));shift=np.array((.1,-.2,.3))
        C1=C+[0,.002,.010]
        actual,rotation=transport_can_reference(p,R,(C,R),(C1,Q))
        np.testing.assert_allclose(Q.T@(actual-C1),p-C,atol=1e-15)
        np.testing.assert_allclose(rotation,Q,atol=1e-15)
        b=.4;W=np.array(((1,0,0),(0,np.cos(b),-np.sin(b)),(0,np.sin(b),np.cos(b))))
        changed,changedR=transport_can_reference(W@p+shift,W@R,(W@C+shift,W@R),(W@C1+shift,W@Q))
        np.testing.assert_allclose(changed,W@actual+shift,atol=1e-15)
        np.testing.assert_allclose(changedR,W@rotation,atol=1e-15)

    def test_moving_release_keeps_relative_rate_and_thirty_mm_endpoint(self):
        C=np.array((.26,0,.86));start=C+[0,0,.08];goal=start+[0,0,.03]
        previous=start.copy();previousC=C.copy();previousR=np.eye(3)
        for tick in range(1,61):
            t=tick*.05;a=t*.02;R=np.array(((1,0,0),(0,np.cos(a),-np.sin(a)),(0,np.sin(a),np.cos(a))))
            nowC=C+[0,.001*t,.004*t]
            entry,_,_=release_command_target(start,goal,t)
            current,_=transport_can_reference(entry,np.eye(3),(C,np.eye(3)),(nowC,R))
            carried=nowC+R@previousR.T@(previous-previousC)
            self.assertLessEqual(np.linalg.norm(current-carried),.0005+1e-15)
            previous,previousC,previousR=current,nowC,R
        np.testing.assert_allclose(R.T@(current-nowC),goal-C,atol=1e-15)

    def test_invalid_pose_fails_closed_without_mutating_reference(self):
        current=np.array((.2,.3,.4));before=current.copy()
        with self.assertRaises(ValueError):can_frame_ramp_translation(current,current,([np.nan,0,0],np.eye(3)),([0,0,0],np.eye(3)),.01,.05)
        np.testing.assert_array_equal(current,before)


class ActualFaceFeedbackTests(unittest.TestCase):
    def test_translation_error_equals_physical_point_error_under_deflection(self):
        a=.13;actualR=np.array(((np.cos(a),0,np.sin(a)),(0,1,0),(-np.sin(a),0,np.cos(a))))
        C=np.array((.26,-.035,.9));canR=np.eye(3);point=np.array((.004,-.018,.08));tcp=np.array((.25,-.02,.91))
        target=actual_face_tcp_target(C,canR,.0793,actualR,point)
        desired=C+canR@np.array((0,0,.0793));actual=tcp+actualR@point
        np.testing.assert_allclose(target-tcp,desired-actual,atol=1e-15)
        # The old ideal-orientation subtraction misses this physical offset.
        self.assertGreater(np.linalg.norm((C+[0,0,.0793]-point)-target),.001)

    def test_ideal_orientation_equivalence_and_world_se3_covariance(self):
        a=.2;R=np.array(((1,0,0),(0,np.cos(a),-np.sin(a)),(0,np.sin(a),np.cos(a))))
        C=np.array((.26,0,.9));point=np.array((.01,.02,.03));height=.08
        actual=actual_face_tcp_target(C,R,height,R,point)
        np.testing.assert_allclose(actual,C+R@(np.array((0,0,height))-point),atol=1e-15)
        b=.4;Q=np.array(((np.cos(b),-np.sin(b),0),(np.sin(b),np.cos(b),0),(0,0,1)));shift=np.array((.2,.1,.3))
        changed=actual_face_tcp_target(Q@C+shift,Q@R,height,Q@R,point)
        np.testing.assert_allclose(changed,Q@actual+shift,atol=1e-15)

    def test_nonfinite_or_incomplete_geometry_rejected(self):
        for C,R,h,H,p in (([np.nan,0,0],np.eye(3),.08,np.eye(3),[0,0,0]),
                         ([0,0,0],np.eye(3),float('inf'),np.eye(3),[0,0,0]),
                         ([0,0,0],np.eye(3),.08,np.eye(2),[0,0,0]),
                         ([0,0,0],np.eye(3),.08,np.eye(3),[0,0])):
            with self.assertRaises(ValueError):actual_face_tcp_target(C,R,h,H,p)


if __name__=='__main__':unittest.main()
