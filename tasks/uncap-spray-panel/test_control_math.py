import unittest
from control_math import grip_fraction


class GripperUnitTests(unittest.TestCase):
    def test_open_closed_and_loaded_grasp_units(self):
        self.assertEqual(grip_fraction(-.04695,-.04695),1.)
        self.assertEqual(grip_fraction(0.,-.04695),0.)
        self.assertAlmostEqual(grip_fraction(-.021,-.04695),.447284345,places=8)

    def test_original_positive_finger_bug_is_rejected(self):
        with self.assertRaises(ValueError):grip_fraction(.024,-.04695)

    def test_out_of_range_command_is_rejected(self):
        with self.assertRaises(ValueError):grip_fraction(-.06,-.04695)

if __name__=='__main__':unittest.main()
