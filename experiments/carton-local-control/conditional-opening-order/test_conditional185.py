"""Only the authorized condition and its fixed-wall blocker are tested."""
import sys
sys.dont_write_bytecode = True
import json
import unittest
import numpy as np
from conditional185 import Conditional185, ROOT, box_gap
from scene import layout


class Conditional185Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.planner = Conditional185()

    def test_south185_preserves_hinge_anchor_and_every_other_panel(self):
        p = self.planner
        hinge = next(h for h in layout()[1] if h['b'] == 'south_bottom')
        oldp, oldR, _ = p.original_south
        newp, newR, _ = p.conditional_south
        np.testing.assert_allclose(oldp+oldR@hinge['anchor_b'],
                                   newp+newR@hinge['anchor_b'], atol=1e-13)
        _, _, _, one = p.state(-78., 0)
        _, _, _, two = p.state(-35., 45)
        for name in one:
            if name == 'north_bottom':
                continue
            for a, b in zip(one[name], two[name]):
                np.testing.assert_array_equal(a, b)
        # The condition is isolated; actual source-world SOUTH is never written.
        self.assertGreater(np.linalg.norm(p.actual['south_bottom'][0]-newp), .1)

    def test_conditional_panels_clear_but_next_gripper_hits_real_wall(self):
        p = self.planner
        self.assertTrue(p.panels(-35.)['safe'])
        tcp, R, patch, obs = p.state(-35., 45.)
        cheap = p.model.cheap_hand(tcp, R, obs)
        self.assertFalse(cheap['safe'])
        self.assertEqual(cheap['hard_gap'][1:], ['gripper', 'south'])
        self.assertAlmostEqual(cheap['hard_gap'][0], -.00017209510471328984, places=10)
        np.testing.assert_allclose(tcp+R@[0,0,.0105], patch, atol=1e-13)

    def test_panel_sat_detects_overlap_without_deleting_other_panels(self):
        p = self.planner
        panel = p.rotated['south_bottom']
        self.assertLess(box_gap(panel, panel), -.0029)
        shifted = (panel[0]+np.array([3.,0,0]), panel[1], panel[2])
        self.assertGreater(box_gap(panel, shifted), 1.)
        report = json.loads((ROOT/'conditional-report.json').read_text())
        self.assertEqual(len(report['prefix_revalidation']), 49)
        self.assertTrue(all(x['passed'] for x in report['prefix_revalidation']))
        self.assertEqual(report['status'], 'CONDITIONAL_NEXT_ANGLE_BLOCKED')
        self.assertEqual(report['best_prefix'][-1]['angle_deg'], -40.)
        self.assertIsNone(report['densified_arc'])
        self.assertLessEqual(report['full315_certificates'], 600)


if __name__ == '__main__':
    unittest.main()
