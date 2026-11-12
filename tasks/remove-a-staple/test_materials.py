import unittest
import numpy as np
from materials import SteelSpec, PlasticHinge, PaperSpec, PaperBond, clinched_staple_centerline


class MaterialsTests(unittest.TestCase):
    def test_small_bend_recovers_elastically(self):
        h = PlasticHinge(SteelSpec())
        result = h.advance(.001)
        self.assertEqual(result["plastic_angle_rad"], 0.)
        self.assertGreater(result["moment_nm"], 0.)
        self.assertEqual(h.advance(0.)["moment_nm"], 0.)

    def test_large_bend_has_permanent_set(self):
        h = PlasticHinge(SteelSpec())
        r = h.advance(.8)
        self.assertGreater(r["plastic_angle_rad"], .7)
        self.assertGreater(r["dissipated_work_j"], 0.)
        self.assertEqual(h.advance(h.plastic_angle_rad)["moment_nm"], 0.)

    def test_thicker_wire_resists_bending(self):
        a, b = SteelSpec(), SteelSpec(wire_thickness_m=.0006)
        self.assertAlmostEqual(b.stiffness_nm_per_rad/a.stiffness_nm_per_rad, 8.)
        self.assertAlmostEqual(b.initial_yield_moment_nm/a.initial_yield_moment_nm, 4.)

    def test_reverse_yield_is_dissipative(self):
        h = PlasticHinge(SteelSpec())
        values = [h.advance(a)["dissipated_work_j"] for a in (.8, 0., -.8, 0., .8)]
        self.assertTrue(all(b >= a for a,b in zip(values[:-1], values[1:])))

    def test_paper_fracture_energy_matches_area_under_force(self):
        s = PaperSpec()
        b = PaperBond(s)
        x = np.linspace(0., s.final_opening_m, 1001)
        force = [b.advance(float(v))["force_n"] for v in x]
        work = np.trapezoid(force, x)
        self.assertAlmostEqual(float(work), s.fracture_energy_j_per_m2*s.area_m2, places=11)

    def test_paper_damage_does_not_heal_on_reclosure(self):
        s = PaperSpec()
        b = PaperBond(s)
        b.advance(s.final_opening_m)
        self.assertTrue(b.advance(0.)["broken"])
        self.assertEqual(b.advance(s.opening_at_peak_m)["force_n"], 0.)
        self.assertLess(b.advance(-1e-6)["force_n"], 0.)

    def test_staple_has_two_inward_clinched_ends(self):
        p = clinched_staple_centerline()
        self.assertLess(p[0, 2], -.0002)
        self.assertLess(p[-1, 2], -.0002)
        self.assertLess(abs(p[0,0]), .0064)
        self.assertLess(abs(p[-1,0]), .0064)
        self.assertLessEqual(float(np.max(np.linalg.norm(np.diff(p,axis=0),axis=1))), .0005+1e-10)

    def test_invalid_parameters_fail(self):
        with self.assertRaises(ValueError):
            SteelSpec(wire_thickness_m=-1)
        with self.assertRaises(ValueError):
            PaperSpec(fracture_energy_j_per_m2=1e-6)
        with self.assertRaises(ValueError):
            PlasticHinge(SteelSpec()).advance(float("nan"))


if __name__ == "__main__":
    unittest.main()
