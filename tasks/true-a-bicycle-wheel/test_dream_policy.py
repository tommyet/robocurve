import unittest
import numpy as np
from dream_policy import bounded_action

class BoundedActionTests(unittest.TestCase):
    def test_ordinary_limits(self):
        actual=bounded_action(np.full(14,2.),np.zeros(14),np.full(14,-1.),np.ones(14),np.full(14,.1))
        np.testing.assert_allclose(actual,.1)
    def test_invalid_policy_output(self):
        for bad in (np.zeros(13),np.full(14,np.nan)):
            with self.assertRaises(ValueError):
                bounded_action(bad,np.zeros(14),np.full(14,-1.),np.ones(14),np.full(14,.1))
    def test_position_limit(self):
        actual=bounded_action(np.full(14,2.),np.full(14,.95),np.full(14,-1.),np.ones(14),np.full(14,.1))
        np.testing.assert_allclose(actual,1.)

if __name__=='__main__':unittest.main()
