import unittest
import numpy as np
from mechanics import WheelModel, WheelSpec, starting_turn_errors


class MechanicsTests(unittest.TestCase):
    def setUp(self):
        self.m = WheelModel()
        self.zero = np.zeros(self.m.spec.spokes)

    def test_balanced_reference_is_an_equilibrium(self):
        result = self.m.equilibrium(self.zero)
        np.testing.assert_allclose(result["displacement_m"], 0, atol=1e-12)
        np.testing.assert_allclose(result["tension_n"], 700, atol=1e-6)

    def test_one_nipple_has_distributed_effect(self):
        self.zero[0] = .25
        result = self.m.equilibrium(self.zero)
        self.assertGreater(np.count_nonzero(np.abs(result["displacement_m"][:,2]) > 1e-6), 5)
        self.assertLess(result["maximum_force_residual_n"], 1e-7)

    def test_reverse_turn_reverses_small_elastic_response(self):
        self.zero[0] = .1
        a = self.m.equilibrium(self.zero)
        b = self.m.equilibrium(-self.zero)
        np.testing.assert_allclose(a["displacement_m"], -b["displacement_m"], atol=1e-11)

    def test_twice_thread_pitch_changes_response(self):
        self.zero[0] = .1
        other = WheelModel(WheelSpec(nipple_pitch_m_per_turn=.000908))
        a, b = self.m.equilibrium(self.zero), other.equilibrium(self.zero)
        np.testing.assert_allclose(b["displacement_m"], 2*a["displacement_m"], atol=1e-10)

    def test_slack_spokes_cannot_push(self):
        result = self.m.equilibrium(np.full(self.m.spec.spokes, -4.))
        self.assertTrue(len(result["slack_spokes"]) > 0)
        self.assertGreaterEqual(float(np.min(result["tension_n"])), 0.)

    def test_restoring_rest_lengths_recovers_reference(self):
        offsets = starting_turn_errors()
        self.assertGreater(self.m.equilibrium(offsets)["lateral_peak_to_peak_m"], 1e-4)
        self.assertLess(self.m.equilibrium(offsets-offsets)["lateral_peak_to_peak_m"], 1e-10)

    def test_axial_proof_load_causes_reversible_distributed_deflection(self):
        forces = np.zeros((self.m.spec.spokes, 3))
        forces[0,2] = 4.903325
        loaded = self.m.equilibrium(self.zero, external_forces_n=forces)
        self.assertTrue(loaded["load_prediction_in_scope"])
        self.assertGreater(loaded["displacement_m"][0,2], 0.)
        self.assertLess(loaded["maximum_force_residual_n"], 1e-7)
        np.testing.assert_allclose(self.m.equilibrium(self.zero)["displacement_m"], 0., atol=1e-12)

    def test_slack_load_prediction_is_explicitly_out_of_scope(self):
        result = self.m.equilibrium(np.full(self.m.spec.spokes, -4.))
        self.assertFalse(result["load_prediction_in_scope"])

    def test_minimal_candidate_starts_untrue_then_four_quarter_turns_suffice_in_linear_model(self):
        turns = starting_turn_errors(profile="two-defect-candidate")
        self.assertEqual(np.count_nonzero(turns), 2)
        initial = self.m.equilibrium(turns)
        self.assertGreater(initial["lateral_peak_to_peak_m"], .0005)
        self.assertLess(np.min(initial["tension_n"]), 400.)
        turns[[0, 2]] += .5
        corrected = self.m.equilibrium(turns)
        self.assertLess(corrected["lateral_peak_to_peak_m"], .0005)
        self.assertGreater(np.min(corrected["tension_n"]), 400.)
        self.assertLess(np.max(corrected["tension_n"]), 1000.)
        with self.assertRaises(ValueError):
            starting_turn_errors(profile="unknown")

    def test_bad_inputs_fail(self):
        for turns in ([0], np.full(32, np.nan)):
            with self.assertRaises(ValueError):
                self.m.equilibrium(turns)
        with self.assertRaises(ValueError):
            WheelModel(WheelSpec(spokes=31))


if __name__ == "__main__":
    unittest.main()
