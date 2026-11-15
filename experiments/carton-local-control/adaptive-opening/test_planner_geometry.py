"""Focused geometry/role regressions; not native or continuous-path proof."""
import sys
sys.dont_write_bytecode = True
import json
import unittest
import numpy as np
from geometry import Geometry, union_area_in_rectangle, BASES
from planner import Planner
from yam_arena import ik


class PlannerGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.planner = Planner()
        cls.geometry = cls.planner.model

    def test_polygon_union_does_not_double_count_or_fill_a_hole(self):
        square = np.array([[0., 0., 0.], [1., 0., 0.], [1., 1., 0.], [0., 1., 0.]])
        self.assertAlmostEqual(union_area_in_rectangle([square, square], [0, 1, 0, 1]), 1.)
        strips = []
        for x0, x1, y0, y1 in [(0, .4, 0, 1), (.6, 1, 0, 1),
                               (.4, .6, 0, .4), (.4, .6, .6, 1)]:
            strips.append(np.array([[x0, y0, 0], [x1, y0, 0],
                                    [x1, y1, 0], [x0, y1, 0]]))
        self.assertAlmostEqual(union_area_in_rectangle(strips, [0, 1, 0, 1]), .96)

    def test_heading_changes_tcp_while_physical_patch_stays_fixed(self):
        p = self.planner
        tcp0, R0, patch0, obs = p.state(p.a0, 0.)
        tcp, R, patch, _ = p.state(p.a0, 30.)
        np.testing.assert_allclose(patch, patch0, atol=1e-14)
        np.testing.assert_allclose(tcp+R@[0, 0, .0105], patch, atol=1e-14)
        self.assertGreater(np.linalg.norm(tcp-tcp0), .005)
        fp, fr, size = obs['north_bottom']
        old = fp+.055*fr[:, 0]+(-size[1]/2-.008)*fr[:, 1]
        np.testing.assert_allclose(tcp0, old, atol=1e-14)
        np.testing.assert_allclose(R.T@R, np.eye(3), atol=1e-12)

    def test_only_north_bottom_changes_in_reoriented_actual_world(self):
        p = self.planner
        *_, initial = p.state(p.a0, 0)
        *_, later = p.state(-40., 30)
        for name in initial:
            if name == 'north_bottom':
                continue
            for a, b in zip(initial[name], later[name]):
                np.testing.assert_array_equal(a, b)
        self.assertEqual(len(initial), 15)  # Twelve panels plus three cutter boxes.

    def test_local_jaw_shift_matches_pinned_urdf_fk(self):
        g = self.geometry
        p, R = ik.tcp_pose(np.zeros(6))
        actual = g.model.world(np.zeros(6), [-.001, -.002], np.zeros(3))
        for index, name, tri in g.local_hand((.001, .002)):
            np.testing.assert_allclose(tri, (actual[index][1]-p)@R, atol=1e-12)

    def test_true_opposing_contact_polygons_and_common_scalar(self):
        p = self.planner
        contact = p.model.contact(0, p.size)
        self.assertTrue(contact['valid'])
        self.assertTrue(contact['ordinary_single_grip_scalar'])
        for jaw in contact['jaws'].values():
            self.assertTrue(jaw['finite_patch_valid'])
            self.assertLess(abs(jaw['target_gap_m']), 1e-5)
            self.assertGreater(jaw['contact_union_area_m2'], 0.)
            self.assertGreaterEqual(jaw['contact_tangential_span_m'], .005)
            # This real contact is intentionally NOT a fictitious2mm-deep rectangle.
            self.assertLess(jaw['actual_contact_inboard_depth_m'], .002)
            pts = np.concatenate(jaw['contact_polygons_flap_local_m'])
            self.assertGreaterEqual(float(pts[:, 1].min()+p.size[1]/2), .002-1e-12)

    def test_explicit_left_right_bases_and_no_omitted_full_arm_pairs(self):
        p = self.planner
        native = p.native
        right = p.model.parts('right', native['right']['joints'], native['right']['finger_joints'])
        before = p.model.model.stats['all_piece_box_pairs']
        left_result = p.model.guard('left', native['left']['joints'],
            native['left']['finger_joints'], p.actual, right)
        self.assertEqual(p.model.model.stats['all_piece_box_pairs']-before, 315*15)
        left = p.model.parts('left', native['left']['joints'], native['left']['finger_joints'])
        right_result = p.model.guard('right', native['right']['joints'],
            native['right']['finger_joints'], p.actual, left)
        self.assertTrue(left_result['safe'])
        self.assertTrue(right_result['safe'])
        self.assertAlmostEqual(left_result['other_arm_gap_m'], right_result['other_arm_gap_m'])
        np.testing.assert_array_equal(BASES['left']-BASES['right'], [0, .610, 0])


if __name__ == '__main__':
    unittest.main()
