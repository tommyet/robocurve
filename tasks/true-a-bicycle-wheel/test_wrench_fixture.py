import unittest
import numpy as np
from wrench_fixture import HandleFixture,bounded,rotation_vector


class FiniteFixtureTests(unittest.TestCase):
    def test_force_and_grasp_moment_are_separately_bounded(self):
        fixture=HandleFixture(.09,(0.,-.195,.011))
        R=np.array(((0.,-1.,0.),(1.,0.,0.),(0.,0.,1.)))
        result=fixture.command(np.zeros(3),np.eye(3),np.zeros(3),np.zeros(6),np.ones(3),R,.0001)
        self.assertAlmostEqual(np.linalg.norm(result['force_n']),10.)
        self.assertAlmostEqual(np.linalg.norm(result['moment_nm']),.35)
        np.testing.assert_allclose(result['position_m'],[0.,-.195,.011])

    def test_stationary_target_only_supplies_weight(self):
        fixture=HandleFixture(.09,(0.,-.195,.011))
        result=fixture.command(np.zeros(3),np.eye(3),np.zeros(3),np.zeros(6),np.zeros(3),np.eye(3),.0001)
        np.testing.assert_allclose(result['force_n'],[0.,0.,.09*9.80665])
        np.testing.assert_allclose(result['moment_nm'],0.)

    def test_nonfinite_load_is_rejected(self):
        with self.assertRaises(ValueError):bounded([np.nan,0.,0.],10.)
        np.testing.assert_allclose(rotation_vector(np.eye(3)),0.)


if __name__=='__main__':unittest.main()
