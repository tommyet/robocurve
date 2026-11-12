import math
import unittest
from thread_coupling import response, ThreadTravelOutOfScope


class ThreadTests(unittest.TestCase):
    def test_angle_shortens_rest_length_without_target_shape(self):
        a=response(.19,.1898,0.,2e6)
        b=response(.19,.1898,.25,2e6)
        self.assertAlmostEqual(a["rest_length_m"]-b["rest_length_m"],.000454*.25)
        self.assertGreater(b["tension_n"],a["tension_n"])

    def test_lead_torque_matches_energy_derivative(self):
        theta=.3
        eps=1e-6
        plus=response(.19,.1898,(theta+eps)/(2*math.pi),2e6)
        minus=response(.19,.1898,(theta-eps)/(2*math.pi),2e6)
        state=response(.19,.1898,theta/(2*math.pi),2e6)
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


if __name__ == "__main__":
    unittest.main()
