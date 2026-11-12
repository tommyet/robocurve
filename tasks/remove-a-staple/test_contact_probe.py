import unittest
import math
from contact_probe import run_probe
from materials import SteelSpec


class ContactTests(unittest.TestCase):
    def test_noncontact_jaw_does_not_bend_the_leg(self):
        result = run_probe(jaw_path_m=[-.001, -.0005, -.0001])
        self.assertLess(result["residual_leg_angle_rad"], 1e-12)
        self.assertEqual(result["maximum_jaw_force_n"], 0.)

    def test_jaw_outside_leg_footprint_has_no_effect(self):
        result = run_probe(jaw_path_m=[.001, .002], jaw_x_range_m=(.005, .006))
        self.assertLess(result["residual_leg_angle_rad"], 1e-12)
        self.assertEqual(result["maximum_jaw_force_n"], 0.)

    def test_contact_leaves_plastic_set_after_jaw_withdraws(self):
        result = run_probe()
        self.assertGreater(result["residual_leg_angle_rad"], math.radians(40))
        self.assertEqual(result["samples"][-1]["jaw_contact_force_n"], 0.)
        self.assertLess(result["maximum_moment_residual_nm"], 1e-10)

    def test_thicker_wire_needs_more_contact_force(self):
        a = run_probe(steel=SteelSpec(wire_thickness_m=.0003))
        b = run_probe(steel=SteelSpec(wire_thickness_m=.0006))
        self.assertGreater(b["maximum_jaw_force_n"], 3*a["maximum_jaw_force_n"])


if __name__ == "__main__":
    unittest.main()
