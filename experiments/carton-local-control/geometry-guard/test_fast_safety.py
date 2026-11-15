"""CPU equivalence checks; these do not validate native contact dynamics."""
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, '/private/tmp/spray-yam-source')
import copy
import unittest
from unittest.mock import patch
import numpy as np
import fast_safety
from baseline_safety import ScoopSafety as Baseline, convex_box_gap
from fast_safety import ScoopSafety as Fast
from workload import inputs


class FastSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = Baseline()
        cls.fast = Fast()

    def assertParity(self, data):
        self.assertEqual(self.baseline.check(**data), self.fast.check(**data))

    def test_absent_target_keeps_baseline_empty_intended_result(self):
        data = inputs(296)
        del data['poses']['north_bottom']
        self.assertTrue(data['contact'])
        self.assertParity(data)
        result = self.fast.check(**data)
        self.assertEqual(result['intended_target_gap_m'], 10.)
        self.assertEqual(result['intended_pair'], [None, None])

    def test_right_finger_cache_invalidates_by_values(self):
        data = inputs(191)
        self.fast.check(**data)
        builds = self.fast.stats['right_fk_builds']
        data['right_fingers'] = data['right_fingers'].copy()
        self.fast.check(**data)
        self.assertEqual(self.fast.stats['right_fk_builds'], builds)
        data['right_fingers'][1] += 1e-6
        self.assertParity(data)
        self.assertEqual(self.fast.stats['right_fk_builds'], builds + 1)

    def test_same_array_cutter_and_panel_changes_are_fresh(self):
        data = inputs(191)
        self.fast.check(**data)
        tool = self.fast.world(data['q'], data['fingers'], np.array([0, .305, .75]))
        point = tool[-1][1].reshape(-1, 3).mean(0)
        data['cutter'][:3] = point
        self.assertParity(data)
        self.assertFalse(self.fast.check(**data)['safe'])
        data['poses']['north'][:3] = point
        self.assertParity(data)

    def test_scalar_fallback_and_safety_threshold_sides(self):
        model = Fast.__new__(Fast)
        model.starts = np.arange(315, dtype=np.int64) * 3
        model.stats = dict(narrowphase_calls=0, all_piece_box_pairs=0)
        obstacle = ('box', np.array([-1., 0., 0.]), np.eye(3), np.array([2., 2., 2.]))
        for desired in (.0002 - 1e-8, .0002, .0002 + 1e-8,
                        .0003 - 1e-8, .0003, .0003 + 1e-8):
            # Face-normal separation is the exact SAT result for this triangle.
            triangle = np.array([[[desired, -.1, -.1], [desired, .1, -.1],
                                  [desired, 0., .1]]])
            left = [('piece', triangle.copy()) for _ in range(315)]
            vertices = np.concatenate([tri.reshape(-1, 3) for _, tri in left])
            expected = convex_box_gap(triangle, *obstacle[1:])
            with patch.object(fast_safety, 'convex_box_gap', wraps=convex_box_gap) as scalar:
                result = model._pair_gaps(left, vertices, [obstacle])[:, 1]
            np.testing.assert_array_equal(result, np.full(315, expected))
            self.assertEqual(bool(result[0] >= .0002), bool(expected >= .0002))
            if desired <= .0003:
                self.assertEqual(scalar.call_count, 315)
            else:
                self.assertEqual(scalar.call_count, 0)

    def test_ties_retain_original_piece_then_obstacle_order(self):
        data = inputs(191)
        # Two physically identical obstacles deliberately create a tied minimum.
        data['poses']['south_bottom'] = data['poses']['north_bottom'].copy()
        self.assertParity(data)

    def test_nonfinite_is_not_cached_or_accepted(self):
        for key in ('q', 'right_q', 'right_fingers', 'cutter'):
            data = inputs(191)
            data[key][0] = np.nan
            for model in (self.baseline, self.fast):
                with self.assertRaises(ValueError):
                    model.check(**data)


if __name__ == '__main__':
    unittest.main()
