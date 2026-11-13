import math
import unittest
import numpy as np
from thread_coupling import (response,response_batch,rotation,rotation_batch,relative_thread_angle,
    relative_thread_angle_batch,ThreadTravelOutOfScope,ThreadSpec)


def rotvec(vector):
    vector=np.asarray(vector,float);theta=np.linalg.norm(vector)
    return np.eye(3) if theta==0 else rotation(np.r_[vector*np.sin(theta/2)/theta,np.cos(theta/2)])


class ThreadTests(unittest.TestCase):
    def test_batch_material_preserves_slack_tension_and_travel_boundary(self):
        length=np.array((.189,.19,.1901,.1902));nominal=.1898
        turns=np.array((-1.,0.,.25,2.9));stiffness=2e6;spec=ThreadSpec()
        batch=response_batch(length,nominal,turns,stiffness,spec)
        scalar=[response(a,nominal,b,stiffness,spec) for a,b in zip(length,turns)]
        for key,values in batch.items():
            np.testing.assert_allclose(values,[row[key] for row in scalar],atol=1e-12)
        with self.assertRaises(ThreadTravelOutOfScope):response_batch(length,nominal,turns+1.,stiffness,spec)
        with self.assertRaises(ValueError):response_batch([.19,np.nan],nominal,0.,stiffness,spec)

    def test_batch_angle_and_torque_gradient_match_independent_scalar(self):
        shaft=np.array([rotvec((.1*i,-.05*i,.02*i)) for i in range(8)])
        nipple=np.array([s@rotvec((-.2*i,.03*i,-.01*i)) for i,s in enumerate(shaft)])
        reference=np.repeat(np.eye(3)[None],8,axis=0)
        angles,gradients=relative_thread_angle_batch(shaft,nipple,reference)
        scalar=[relative_thread_angle(s,n) for s,n in zip(shaft,nipple)]
        np.testing.assert_allclose(angles,[row[0] for row in scalar],atol=1e-14)
        np.testing.assert_allclose(gradients,[row[1] for row in scalar],atol=1e-14)
        with self.assertRaises(ThreadTravelOutOfScope):
            relative_thread_angle_batch(np.eye(3)[None],rotvec((0.,math.pi,0.))[None],np.eye(3)[None])

    def test_batched_native_rotations_match_scalar_convention(self):
        q=np.array(((0.,0.,0.,1.),(.2,-.3,.7,.1),(-.5,.3,1.,-.2),(0.,1.,0.,0.)))
        np.testing.assert_allclose(rotation_batch(q),np.array([rotation(row) for row in q]),atol=1e-14)
        for invalid in (np.zeros((2,4)),np.ones((2,3)),np.full((2,4),np.nan)):
            with self.assertRaises(ValueError):rotation_batch(invalid)

    def test_angle_shortens_rest_length_without_target_shape(self):
        a=response(.19,.1898,0.,2e6)
        b=response(.19,.1898,.25,2e6)
        self.assertAlmostEqual(a["rest_length_m"]-b["rest_length_m"],.000454*.25)
        self.assertGreater(b["tension_n"],a["tension_n"])

    def test_lead_torque_matches_energy_derivative(self):
        theta=.3
        eps=1e-6
        sign=ThreadSpec().tightening_sign
        plus=response(.19,.1898,sign*(theta+eps)/(2*math.pi),2e6)
        minus=response(.19,.1898,sign*(theta-eps)/(2*math.pi),2e6)
        state=response(.19,.1898,sign*theta/(2*math.pi),2e6)
        self.assertAlmostEqual((plus["energy_j"]-minus["energy_j"])/(2*eps),-state["lead_torque_nm"],places=6)

    def test_slack_spoke_has_no_lead_torque(self):
        s=response(.189,.1898,-1.,2e6)
        self.assertEqual(s["tension_n"],0.)
        self.assertEqual(s["lead_torque_nm"],0.)

    def test_excess_travel_invalidates_instead_of_clamping(self):
        with self.assertRaises(ThreadTravelOutOfScope):
            response(.19,.1898,3.01,2e6)
        with self.assertRaises(ThreadTravelOutOfScope):
            response(.19,.1898,-3.01,2e6)

    def test_common_shaft_rotation_does_not_advance_thread(self):
        frame=rotvec((.8,.3,-.7))
        angle,gradient=relative_thread_angle(frame,frame)
        self.assertAlmostEqual(angle,0.,places=12)
        np.testing.assert_allclose(gradient,frame[:,0],atol=1e-12)

    def test_global_wheel_motion_preserves_relative_thread_angle(self):
        shaft=rotvec((.2,.1,.3));nipple=shaft@rotvec((.7,0.,0.))
        angle,gradient=relative_thread_angle(shaft,nipple)
        world=rotvec((1.,-.3,.4))
        moved,moved_gradient=relative_thread_angle(world@shaft,world@nipple)
        self.assertAlmostEqual(angle,.7,places=12)
        self.assertAlmostEqual(moved,angle,places=12)
        np.testing.assert_allclose(moved_gradient,world@gradient,atol=1e-12)

    def test_tilted_thread_torques_match_energy_gradient_and_balance(self):
        shaft=rotvec((.4,-.1,.3));nipple=shaft@rotvec((.7,.2,-.1))
        angle,gradient=relative_thread_angle(shaft,nipple);eps=1e-6
        sign=ThreadSpec().tightening_sign
        material=response(.19,.1898,sign*angle/(2*math.pi),2e6)
        for axis in np.eye(3):
            def energy(s,n):
                value,_=relative_thread_angle(s,n)
                return response(.19,.1898,sign*value/(2*math.pi),2e6)['energy_j']
            dn=(energy(shaft,rotvec(axis*eps)@nipple)-energy(shaft,rotvec(-axis*eps)@nipple))/(2*eps)
            ds=(energy(rotvec(axis*eps)@shaft,nipple)-energy(rotvec(-axis*eps)@shaft,nipple))/(2*eps)
            self.assertAlmostEqual(dn,-material['lead_torque_nm']*np.dot(axis,gradient),places=7)
            self.assertAlmostEqual(ds,-dn,places=7)

    def test_right_hand_nipple_tightens_clockwise_from_rim(self):
        theta=-math.pi/2
        turns=ThreadSpec().tightening_sign*theta/(2*math.pi)
        before=response(.19,.1898,0.,2e6)
        after=response(.19,.1898,turns,2e6)
        self.assertEqual(turns,.25)
        self.assertAlmostEqual(before['rest_length_m']-after['rest_length_m'],.25*.000454)
        self.assertGreater(after['lead_torque_nm'],0.)  # opposes clockwise tightening


if __name__ == "__main__":
    unittest.main()
