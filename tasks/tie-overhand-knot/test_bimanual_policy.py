"""Regression checks for abort guards; these do not establish robot feasibility."""
import unittest
import json
from pathlib import Path
import numpy as np

import bimanual_policy as policy
import telemetry


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.saved_sample = telemetry.latest_sample
        self.saved_events = telemetry.demo_events
        telemetry.demo_events = []
        self.addCleanup(setattr, telemetry, 'latest_sample', self.saved_sample)
        self.addCleanup(setattr, telemetry, 'demo_events', self.saved_events)
        telemetry.latest_sample = dict(time=0., metrics={'invalid': None},
            cord={'points': [[0., 0., .003]]}, hands=[dict(
                tcp=[0., 0., 0.], tcp_rotation=np.eye(3).tolist(),
                opening=.0051/.04695)])

    def test_closed_central_material_is_a_geometric_witness(self):
        policy._held(0, 0, require_loaded=True)
        self.assertTrue(telemetry.demo_events[-1]['passed'])

    def test_open_gripper_cannot_claim_loaded_contact(self):
        telemetry.latest_sample['hands'][0]['opening'] = 1.
        with self.assertRaises(policy._StopAttempt):
            policy._held(0, 0, require_loaded=True)

    def test_material_outside_inner_pad_gap_cannot_claim_contact(self):
        telemetry.latest_sample['cord']['points'][0][0] = .012
        with self.assertRaises(policy._StopAttempt):
            policy._held(0, 0, require_loaded=True)

    def test_invalid_geometry_stops_long_motion_at_next_capture(self):
        advanced = []
        def motion():
            for i in range(20):
                advanced.append(i)
                yield
        driven = policy._drive(motion())
        next(driven)
        telemetry.latest_sample['metrics']['invalid'] = 'penetration'
        with self.assertRaises(policy._StopAttempt):
            next(driven)
        self.assertEqual(advanced, [0])

    def test_loop_interior_uses_boundary_not_bounding_box(self):
        # A concave U: the notch lies inside the bounding box but outside it.
        polygon = np.array([[0., 0.], [3., 0.], [3., 3.], [2., 3.],
                            [2., 1.], [1., 1.], [1., 3.], [0., 3.], [0., 0.]])
        self.assertFalse(policy._inside_distance([1.5, 2.], polygon)[0])
        inside, clearance = policy._inside_distance([.5, 2.], polygon)
        self.assertTrue(inside)
        self.assertAlmostEqual(clearance, .5)

    def test_crossing_can_migrate_into_original_bend_material(self):
        fixture = json.loads((Path(__file__).parent / 'evidence' /
                              'loop-001-crossing.json').read_text())
        telemetry.latest_sample['cord']['polyline'] = fixture['polyline']
        crossing = policy._crossing()
        self.assertEqual(crossing['standing_index'], fixture['expected_standing_index'])
        self.assertEqual(crossing['working_index'], fixture['expected_working_index'])
        self.assertGreater(crossing['working_above_m'], .01)


if __name__ == '__main__':
    unittest.main()
