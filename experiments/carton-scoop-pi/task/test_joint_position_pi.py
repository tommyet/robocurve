import json
import unittest
import numpy as np
from joint_position_pi import JointPositionPI


LOWER = np.array([-2., -2., -2., -2., -2., -2.])
UPPER = -LOWER


def started(**kwargs):
    pi = JointPositionPI(LOWER, UPPER, **kwargs)
    pi.begin(np.zeros(6), 0.)
    proposal = pi.propose(np.zeros(6), np.zeros(6), 0.)
    pi.resolve(proposal, guard_safe=True)
    return pi


class JointPositionPITests(unittest.TestCase):
    def test_biased_lagged_plant_converges_without_hardware_gain_change(self):
        # Synthetic discrete lag plant, not evidence of native friction stability.
        disturbance = np.array([-.003, .001, .002, .004, .004, -.00835])
        pi = started()
        actual = np.zeros(6)
        for tick in range(1, 401):
            proposal = pi.propose(np.zeros(6), actual, tick * .05)
            receipt = pi.resolve(proposal, guard_safe=True)
            actual += .2 * (np.asarray(receipt.command) - disturbance - actual)
        self.assertLess(np.max(np.abs(actual)), 5e-6)
        np.testing.assert_allclose(pi.bias, disturbance, atol=5e-6)
        self.assertGreater(np.max(np.abs(disturbance)), .008)

    def test_exact_loaded_handoff_duplicate_and_immutable_proposals(self):
        pi = JointPositionPI(LOWER, UPPER)
        issued = np.linspace(-.6, .6, 6)
        pi.begin(issued, 2.)
        issued[:] = 0.  # Mutating caller arrays cannot change held command.
        proposal = pi.propose(np.ones(6), -np.ones(6), 2.05)
        expected = np.linspace(-.6, .6, 6)
        np.testing.assert_array_equal(proposal.command, expected)
        receipt = pi.resolve(proposal, guard_safe=True)
        self.assertEqual(receipt.path_dt_s, 0.)
        np.testing.assert_array_equal(pi.bias, np.zeros(6))
        duplicate = pi.propose(-np.ones(6), np.zeros(6), 2.05)
        self.assertEqual(duplicate.kind, 'duplicate_clock')
        receipt = pi.resolve(duplicate, guard_safe=True)
        self.assertFalse(receipt.accepted)
        np.testing.assert_array_equal(receipt.command, expected)
        with self.assertRaises((AttributeError, TypeError)):
            duplicate.command[0] = .4

    def test_guard_rejection_is_atomic_and_does_not_catch_up(self):
        pi = started()
        for tick in range(1, 6):
            proposal = pi.propose(np.zeros(6), -np.ones(6), tick * .05)
            receipt = pi.resolve(proposal, guard_safe=False)
            self.assertFalse(receipt.accepted)
            self.assertEqual(receipt.path_dt_s, 0.)
            np.testing.assert_array_equal(pi.bias, np.zeros(6))
            np.testing.assert_array_equal(pi.issued, np.zeros(6))
        proposal = pi.propose(np.zeros(6), -np.ones(6), .30)
        receipt = pi.resolve(proposal, guard_safe=True)
        np.testing.assert_allclose(pi.bias, np.full(6, .00025), atol=1e-15)
        self.assertAlmostEqual(receipt.path_dt_s, .05)

    def test_nominal_error_not_augmented_error_and_offset_added_once(self):
        pi = started()
        for tick in range(1, 6):
            proposal = pi.propose(np.zeros(6), -np.ones(6), tick * .05)
            pi.resolve(proposal, guard_safe=True)
        before = pi.bias
        proposal = pi.propose(np.zeros(6), np.zeros(6), .30)
        # A command-minus-actual integrator would keep growing here.
        np.testing.assert_array_equal(proposal.proposed_bias, before)
        np.testing.assert_array_equal(proposal.command, before)
        pi.resolve(proposal, guard_safe=True)

    def test_joint_limit_antiwindup_and_recovery(self):
        pi = JointPositionPI(np.full(6, -.1), np.full(6, .1))
        pi.begin(np.full(6, .1), 0.)
        pi.resolve(pi.propose(np.full(6, .1), np.zeros(6), 0.), guard_safe=True)
        for tick in range(1, 11):
            proposal = pi.propose(np.full(6, .1), np.zeros(6), tick * .05)
            receipt = pi.resolve(proposal, guard_safe=True)
            np.testing.assert_array_equal(receipt.command, np.full(6, .1))
            np.testing.assert_array_equal(pi.bias, np.zeros(6))
        # Error reversal may unwind immediately; limit blocking is directional.
        proposal = pi.propose(np.full(6, .1), np.full(6, .2), .55)
        receipt = pi.resolve(proposal, guard_safe=True)
        self.assertTrue(all(x < 0 for x in receipt.bias))
        self.assertTrue(all(x < .1 for x in receipt.command))

    def test_slew_antiwindup_total_bias_cap_and_clipped_path_hold(self):
        pi = started()
        proposal = pi.propose(np.ones(6), np.zeros(6), .05)
        receipt = pi.resolve(proposal, guard_safe=True)
        np.testing.assert_array_equal(receipt.command, np.full(6, .04))
        np.testing.assert_array_equal(pi.bias, np.zeros(6))
        self.assertEqual(receipt.path_dt_s, 0.)
        self.assertEqual(receipt.reason, 'command_limit_path_hold')
        pi = started()
        previous = pi.issued
        for tick in range(1, 201):
            receipt = pi.resolve(pi.propose(np.zeros(6), -np.ones(6), tick * .05),
                                 guard_safe=True)
            command = np.asarray(receipt.command)
            self.assertLessEqual(np.max(np.abs(command - previous)), .04)
            self.assertLessEqual(np.max(np.abs(pi.bias)), .02)
            previous = command
        np.testing.assert_allclose(pi.bias, np.full(6, .02))

    def test_invalid_input_latches_last_command_without_new_integration(self):
        for bad_q, clock in [(np.full(6, np.nan), .05),
                             (np.zeros(5), .05), (np.zeros(6), .2),
                             (np.zeros(6), -.05), (np.zeros(6), float('nan'))]:
            pi = started()
            proposal = pi.propose(np.zeros(6), bad_q, clock)
            self.assertFalse(proposal.valid)
            receipt = pi.resolve(proposal, guard_safe=True)
            self.assertFalse(receipt.accepted)
            self.assertEqual(receipt.path_dt_s, 0.)
            np.testing.assert_array_equal(pi.bias, np.zeros(6))
            np.testing.assert_array_equal(receipt.command, np.zeros(6))
            proposal = pi.propose(np.zeros(6), np.zeros(6), .05)
            self.assertFalse(proposal.valid)
            json.dumps(proposal.__dict__, allow_nan=False)

    def test_stale_transactions_cannot_commit_or_mutate_private_state(self):
        pi = started()
        proposal = pi.propose(np.zeros(6), -np.ones(6), .05)
        pi.resolve(proposal, guard_safe=False)
        with self.assertRaises(RuntimeError):
            pi.resolve(proposal, guard_safe=True)
        with self.assertRaises(RuntimeError):
            pi.resolve(None, guard_safe=True)
        bias_copy = pi.bias
        bias_copy[:] = .02
        np.testing.assert_array_equal(pi.bias, np.zeros(6))
        with self.assertRaises(ValueError):
            JointPositionPI(LOWER, UPPER, bias_cap=.03)

    def test_illegal_nominal_and_nonboolean_guard_never_commit(self):
        pi = started()
        proposal = pi.propose(np.full(6, 3.), np.zeros(6), .05)
        self.assertFalse(proposal.valid)
        receipt = pi.resolve(proposal, guard_safe=True)
        self.assertFalse(receipt.accepted)
        np.testing.assert_array_equal(pi.issued, np.zeros(6))
        pi = started()
        proposal = pi.propose(np.zeros(6), -np.ones(6), .05)
        with self.assertRaises(ValueError):
            pi.resolve(proposal, guard_safe=1)
        np.testing.assert_array_equal(pi.bias, np.zeros(6))
        pi.resolve(proposal, guard_safe=False)


if __name__ == '__main__':
    unittest.main()
