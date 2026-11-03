"""Behavioral tests of temporal scoring using synthetic measured observations.

These traces exercise the scoring contract, not a physics simulation. Passing
them does not establish that the dimensions, timing, or thresholds are feasible
for the robot; that requires the recorded simulator demonstration.

Run with:
    python -m unittest discover -s tasks/roll-a-die -p test_scoring.py -v
"""

import math
import unittest

import numpy as np

from scoring import EDGE, LIFT_HOLD_S, MIN_TUMBLE, REST_HOLD_S, TABLE_TOP, TABLE_X, RollTracker, rotation


DT = 0.05


def quaternion(axis, angle):
    axis = np.asarray(axis, dtype=float)
    axis = axis / np.linalg.norm(axis)
    return np.r_[axis * math.sin(angle / 2), math.cos(angle / 2)]


class Trace:
    """Construct consistent cube bounds and measured hand positions per sample."""

    def __init__(self):
        self.tracker = RollTracker()
        self.time = -DT
        self.quat = np.array([0.0, 0.0, 0.0, 1.0])

    def sample(self, *, clearance=0.0, quat=None, lin_vel=(0, 0, 0),
               ang_vel=(0, 0, 0), hand="far", x=0.25,
               hand_opening=None, tcp_offset=None, closing_axis=None):
        self.time += DT
        if quat is not None:
            self.quat = np.asarray(quat, dtype=float)
        half_bounds = np.abs(rotation(self.quat)) @ np.full(3, EDGE / 2)
        pos = np.array([x, 0.0, TABLE_TOP + clearance + half_bounds[2]])
        tcp = pos + np.array([0.20, 0.0, 0.20])
        opening = 1.0
        if hand in {"closed", "open_near", "open_too_close"}:
            tcp = pos + np.array([0.0, 0.0, 0.01 if hand == "open_too_close" else 0.025])
            opening = 0.0 if hand == "closed" else 1.0
        if hand_opening is not None:
            opening = hand_opening
        if tcp_offset is not None:
            tcp = pos + np.asarray(tcp_offset)
        first_hand = {"tcp": tcp.tolist(), "opening": opening}
        if closing_axis is not None:
            first_hand["closing_axis"] = list(closing_axis)
        return {
            "time": self.time,
            "pos": pos.tolist(),
            "low": (pos - half_bounds).tolist(),
            "high": (pos + half_bounds).tolist(),
            "quat_xyzw": self.quat.tolist(),
            "lin_vel": list(lin_vel),
            "ang_vel": list(ang_vel),
            "hands": [
                first_hand,
                {"tcp": (pos + np.array([-0.20, 0.0, 0.20])).tolist(), "opening": 1.0},
            ],
        }

    def step(self, **kwargs):
        return self.tracker.update(self.sample(**kwargs))

    def pickup(self):
        self.step()
        # Extra observations avoid making most tests depend on dwell boundaries.
        for _ in range(math.ceil(LIFT_HOLD_S / DT) + 2):
            self.step(clearance=0.08, hand="closed")
        return self

    def release(self):
        # Previous vertical velocity is zero. This sample records gravitational
        # downward acceleration and sufficient geometric clearance from hands.
        self.step(clearance=0.08 - 0.5 * 9.81 * DT**2, lin_vel=(0, 0, -9.81 * DT))
        return self

    def tumble(self, *, axis=(1, 0, 0), angle=MIN_TUMBLE):
        for value in np.linspace(angle / 4, angle, 4):
            self.step(clearance=0.04, quat=quaternion(axis, value),
                      lin_vel=(0, 0, -0.2), ang_vel=np.asarray(axis) * 4.0)
        return self

    def rest(self, samples=None):
        if samples is None:
            samples = math.ceil(REST_HOLD_S / DT) + 2
        for _ in range(samples):
            self.step()
        return self


class RollScoringTests(unittest.TestCase):
    def test_lift_release_tumble_and_settle_reaches_full_score(self):
        trace = Trace().pickup()
        self.assertTrue(trace.tracker.lifted)
        self.assertEqual(trace.tracker.value, 0.25)
        trace.release()
        self.assertTrue(trace.tracker.released)
        self.assertAlmostEqual(trace.tracker.tumble, 0.0)
        trace.tumble()
        self.assertAlmostEqual(trace.tracker.tumble, MIN_TUMBLE)
        self.assertEqual(trace.tracker.value, 0.5)
        trace.rest()
        self.assertEqual(trace.tracker.value, 1.0)
        self.assertIsNone(trace.tracker.invalid)
        self.assertEqual([event["event"] for event in trace.tracker.events], ["pickup", "release"])

    def test_flat_yaw_spin_does_not_count_as_tumbling(self):
        trace = Trace().pickup().release().tumble(axis=(0, 0, 1), angle=2 * math.pi).rest()
        self.assertTrue(trace.tracker.released)
        self.assertAlmostEqual(trace.tracker.tumble, 0.0)
        self.assertEqual(trace.tracker.value, 0.25)

    def test_placing_cube_on_table_does_not_count_as_release_or_roll(self):
        trace = Trace().pickup()
        trace.step(hand="closed")
        trace.rest()
        self.assertFalse(trace.tracker.released)
        self.assertEqual(trace.tracker.value, 0.25)

    def test_rotation_while_held_is_not_credited_after_release(self):
        trace = Trace().pickup()
        for angle in np.linspace(0, math.pi, 9):
            trace.step(clearance=0.08, hand="closed", quat=quaternion((1, 0, 0), angle))
        trace.release().rest()
        self.assertTrue(trace.tracker.released)
        self.assertAlmostEqual(trace.tracker.tumble, 0.0)
        self.assertEqual(trace.tracker.value, 0.25)

    def test_release_transition_itself_cannot_supply_tumble_credit(self):
        trace = Trace().pickup()
        trace.step(clearance=0.06, quat=quaternion((1, 0, 0), math.pi / 2),
                   lin_vel=(0, 0, -9.81 * DT))
        trace.rest()
        self.assertTrue(trace.tracker.released)
        self.assertAlmostEqual(trace.tracker.tumble, 0.0)
        self.assertEqual(trace.tracker.value, 0.25)

    def test_partial_jaw_opening_confirms_release_during_upward_flight(self):
        trace = Trace().pickup()
        # A 24% opening leaves 3.27 mm on each side of an aligned 16 mm die.
        # At the first clear observation it is still within 22 mm of the TCP.
        trace.step(clearance=0.12, lin_vel=(0, 0, 0.80), hand_opening=0.24,
                   tcp_offset=(0, 0, 0.012), closing_axis=(0, 1, 0))
        self.assertFalse(trace.tracker.released)
        clear_time = trace.time
        trace.step(clearance=0.14, quat=quaternion((0, 1, 0), math.pi / 4),
                   lin_vel=(0, 0, 0.80 - 9.81 * DT), hand_opening=0.28,
                   tcp_offset=(0, 0, 0.03), closing_axis=(0, 1, 0))
        self.assertTrue(trace.tracker.released)
        self.assertAlmostEqual(trace.tracker.tumble, math.pi / 4)
        self.assertAlmostEqual(trace.tracker.events[-1]["credited_from"], clear_time)
        trace.step(clearance=0.14, quat=quaternion((0, 1, 0), math.pi / 2),
                   lin_vel=(0, 0, 0.80 - 2 * 9.81 * DT), hand_opening=0.30,
                   tcp_offset=(0, 0, 0.05), closing_axis=(0, 1, 0))
        trace.rest()
        self.assertAlmostEqual(trace.tracker.tumble, MIN_TUMBLE)
        self.assertEqual(trace.tracker.value, 1.0)

    def test_verified_near_jaw_flight_history_is_preserved_until_clearance(self):
        trace = Trace().pickup()
        for index, angle in enumerate((0, math.pi / 6, math.pi / 3, math.pi / 2)):
            trace.step(clearance=0.12, quat=quaternion((0, 1, 0), angle),
                       lin_vel=(0, 0, 1.4 - index * 9.81 * DT), hand_opening=0.30,
                       tcp_offset=(0, 0, 0.03 if index == 3 else 0.015),
                       closing_axis=(0, 1, 0))
            self.assertEqual(trace.tracker.released, index == 3)
        self.assertAlmostEqual(trace.tracker.tumble, MIN_TUMBLE)
        trace.rest()
        self.assertEqual(trace.tracker.value, 1.0)

    def test_projected_jaw_clearance_accounts_for_die_width_and_offset(self):
        for quat, offset in (
            (quaternion((0, 0, 1), math.pi / 4), (0, 0, 0.03)),
            ([0, 0, 0, 1], (0, 0.006, 0.03)),
        ):
            with self.subTest(quat=quat, offset=offset):
                trace = Trace().pickup()
                # The same 25% opening fits a centred, axis-aligned die with
                # margin, but not a 45-degree die or one displaced by 6 mm.
                trace.step(clearance=0.08, quat=quat, lin_vel=(0, 0, -9.81 * DT),
                           hand_opening=0.25, tcp_offset=offset, closing_axis=(0, 1, 0))
                self.assertFalse(trace.tracker.released)
                self.assertAlmostEqual(trace.tracker.tumble, 0.0)

    def test_partial_open_release_does_not_credit_held_boundary_rotation(self):
        trace = Trace().pickup()
        trace.step(clearance=0.08, quat=quaternion((0, 1, 0), math.pi / 2),
                   lin_vel=(0, 0, -9.81 * DT), hand_opening=0.28,
                   tcp_offset=(0, 0, 0.03), closing_axis=(0, 1, 0))
        self.assertTrue(trace.tracker.released)
        self.assertAlmostEqual(trace.tracker.tumble, 0.0)
        trace.rest()
        self.assertEqual(trace.tracker.value, 0.25)

    def test_regrasp_before_confirmation_discards_pending_rotation(self):
        trace = Trace().pickup()
        for index, angle in enumerate((0, math.pi / 4)):
            trace.step(clearance=0.12, quat=quaternion((0, 1, 0), angle),
                       lin_vel=(0, 0, 0.80 - index * 9.81 * DT), hand_opening=0.28,
                       tcp_offset=(0, 0, 0.015), closing_axis=(0, 1, 0))
        self.assertFalse(trace.tracker.released)
        self.assertAlmostEqual(trace.tracker.pending_tumble, math.pi / 4)
        trace.step(clearance=0.10, quat=quaternion((0, 1, 0), math.pi / 2),
                   lin_vel=(0, 0, 0.80 - 2 * 9.81 * DT), hand="closed")
        self.assertAlmostEqual(trace.tracker.pending_tumble, 0.0)
        trace.step(clearance=0.08, quat=quaternion((0, 1, 0), math.pi),
                   lin_vel=(0, 0, 0.80 - 3 * 9.81 * DT), hand_opening=0.28,
                   tcp_offset=(0, 0, 0.03), closing_axis=(0, 1, 0))
        self.assertTrue(trace.tracker.released)
        self.assertAlmostEqual(trace.tracker.tumble, 0.0)

    def test_partial_open_upward_yaw_spin_still_gets_no_tumble_credit(self):
        trace = Trace().pickup()
        for index, angle in enumerate((0, math.pi / 2, math.pi, 3 * math.pi / 2)):
            trace.step(clearance=0.12, quat=quaternion((0, 0, 1), angle),
                       lin_vel=(0, 0, 1.4 - index * 9.81 * DT), hand_opening=0.32,
                       tcp_offset=(0, 0, 0.015 if index == 0 else 0.03),
                       closing_axis=(0, 1, 0))
        self.assertTrue(trace.tracker.released)
        self.assertAlmostEqual(trace.tracker.tumble, 0.0)
        trace.rest()
        self.assertEqual(trace.tracker.value, 0.25)

    def test_free_tumbling_without_recorded_pickup_has_no_credit(self):
        trace = Trace()
        trace.step()
        trace.tumble(angle=math.pi).rest()
        self.assertFalse(trace.tracker.lifted)
        self.assertFalse(trace.tracker.released)
        self.assertEqual(trace.tracker.value, 0.0)

    def test_off_table_failure_erases_each_credit_level_permanently(self):
        for stage in ("lifted", "rolled", "complete"):
            with self.subTest(stage=stage):
                trace = Trace().pickup()
                if stage != "lifted":
                    trace.release().tumble()
                if stage == "complete":
                    trace.rest()
                self.assertGreater(trace.tracker.value, 0.0)
                trace.step(x=TABLE_X[1] + EDGE)
                self.assertEqual(trace.tracker.value, 0.0)
                self.assertIsNotNone(trace.tracker.invalid)
                trace.rest()
                self.assertEqual(trace.tracker.value, 0.0)

    def test_falling_below_table_is_a_permanent_failure(self):
        trace = Trace().pickup().release().tumble()
        trace.step(clearance=-0.02)
        self.assertEqual(trace.tracker.value, 0.0)
        trace.rest()
        self.assertEqual(trace.tracker.value, 0.0)

    def test_renewed_closed_hand_proximity_erases_earned_credit(self):
        trace = Trace().pickup().release().tumble().rest()
        self.assertEqual(trace.tracker.value, 1.0)
        trace.step(hand="closed")
        self.assertEqual(trace.tracker.value, 0.0)
        self.assertIsNotNone(trace.tracker.invalid)
        trace.rest()
        self.assertEqual(trace.tracker.value, 0.0)

    def test_open_hand_inside_clearance_also_invalidates_the_roll(self):
        trace = Trace().pickup().release().tumble()
        trace.step(hand="open_too_close")
        self.assertEqual(trace.tracker.value, 0.0)
        self.assertIsNotNone(trace.tracker.invalid)

    def test_rest_must_be_continuous_across_motion_interruption(self):
        trace = Trace().pickup().release().tumble()
        trace.rest(12)
        self.assertLess(trace.tracker.value, 1.0)
        trace.step(ang_vel=(0.5, 0, 0))
        self.assertEqual(trace.tracker.rest_hold, 0.0)
        trace.rest(12)
        self.assertLess(trace.tracker.value, 1.0)
        trace.rest()
        self.assertEqual(trace.tracker.value, 1.0)

    def test_rest_dwell_starts_at_first_resting_observation(self):
        trace = Trace().pickup().release().tumble()
        trace.step()
        self.assertAlmostEqual(trace.tracker.rest_hold, 0.0)
        trace.rest(math.ceil(REST_HOLD_S / DT) - 1)
        self.assertLess(trace.tracker.value, 1.0)
        trace.step()
        self.assertEqual(trace.tracker.value, 1.0)

    def test_pickup_dwell_starts_at_first_held_observation(self):
        trace = Trace()
        trace.step()
        trace.step(clearance=0.08, hand="closed")
        self.assertAlmostEqual(trace.tracker.lift_hold, 0.0)
        for _ in range(math.ceil(LIFT_HOLD_S / DT) - 1):
            trace.step(clearance=0.08, hand="closed")
        self.assertFalse(trace.tracker.lifted)
        trace.step(clearance=0.08, hand="closed")
        self.assertTrue(trace.tracker.lifted)

    def test_quaternion_sign_flips_do_not_create_rotation(self):
        trace = Trace().pickup().release()
        for index in range(8):
            sign = -1 if index % 2 else 1
            trace.step(clearance=0.04, quat=[0, 0, 0, sign])
        trace.rest()
        self.assertAlmostEqual(trace.tracker.tumble, 0.0)
        self.assertEqual(trace.tracker.value, 0.25)

    def test_nonfinite_time_is_rejected(self):
        for time in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(time=time):
                trace = Trace()
                sample = trace.sample()
                sample["time"] = time
                with self.assertRaises(ValueError):
                    trace.tracker.update(sample)

    def test_nonincreasing_time_and_observation_gaps_are_rejected(self):
        trace = Trace()
        trace.step()
        for time in (0.0, -0.05, 0.10):
            with self.subTest(time=time):
                sample = trace.sample()
                sample["time"] = time
                with self.assertRaises(ValueError):
                    trace.tracker.update(sample)


if __name__ == "__main__":
    unittest.main()
