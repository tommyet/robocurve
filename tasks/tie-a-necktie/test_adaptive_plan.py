import unittest
from adaptive_plan import hold_suffix


class AdaptivePlanTest(unittest.TestCase):
    def test_measured_endpoint_replaces_stale_future_hold(self):
        frames = [dict(action14=[x] * 14, stage='planned') for x in (0., .1, .2, 9., 9.)]
        hold_suffix(frames, 3)
        self.assertEqual([f['action14'][0] for f in frames], [0., .1, .2, .2, .2])
        frames[3]['action14'][0] = .3
        self.assertEqual(frames[2]['action14'][0], .2)
        self.assertEqual(frames[4]['action14'][0], .2)

    def test_complete_plan_is_unchanged(self):
        frames = [dict(action14=[.4] * 14, stage='complete')]
        hold_suffix(frames, 1)
        self.assertEqual(frames[0]['stage'], 'complete')

    def test_empty_prefix_is_rejected(self):
        with self.assertRaises(ValueError):
            hold_suffix([dict(action14=[0.] * 14)], 0)
