import unittest
from scoring import score, CHECKS


def record():
    return {"schema": "staple-judging-v1", "checks": dict.fromkeys(CHECKS, True),
            "legs_clear_of_both_sheets": 2, "maximum_new_tear_mm": 0.,
            "any_new_damage_away_from_holes": False,
            "final_sheet_gap_mm": 30., "release_seconds": 3.}


class ScoringTests(unittest.TestCase):
    def test_extraction_and_separation(self):
        r = record()
        self.assertEqual(score(r)["score"], 1.)
        r["legs_clear_of_both_sheets"] = 1
        self.assertEqual(score(r)["score"], .5)
        r["legs_clear_of_both_sheets"] = 0
        self.assertEqual(score(r)["score"], 0.)

    def test_torn_paper_zeroes_partial_and_full(self):
        for legs in (1,2):
            r = record()
            r["legs_clear_of_both_sheets"] = legs
            r["maximum_new_tear_mm"] = 2.001
            self.assertEqual(score(r)["score"], 0.)

    def test_independent_damage_is_not_hidden_by_hole_tolerance(self):
        r = record()
        r["any_new_damage_away_from_holes"] = True
        self.assertEqual(score(r)["score"], 0.)

    def test_missing_release_or_gap_only_partial(self):
        for key in ("final_sheet_gap_mm", "release_seconds"):
            r = record()
            r[key] = 0.
            self.assertEqual(score(r)["score"], .5)

    def test_missing_or_nonfinite_observations_fail_closed(self):
        r = record()
        del r["checks"]["both_sheet_faces_inspected"]
        self.assertFalse(score(r)["record_valid"])
        r = record()
        r["maximum_new_tear_mm"] = float("nan")
        self.assertFalse(score(r)["record_valid"])


if __name__ == "__main__":
    unittest.main()
