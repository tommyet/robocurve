import unittest
from scoring import score, CHECKS


def record():
    return {"schema": "staple-judging-v2", "checks": dict.fromkeys(CHECKS, True),
            "legs_clear_of_both_sheets": 2, "maximum_new_tear_mm": 0.,
            "any_new_damage_away_from_holes": False,
            "initial_relative_corner_offset_mm": [0.,12.],
            "final_relative_corner_offset_mm": [0.,42.], "release_seconds": 3.}


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

    def test_whole_stack_motion_does_not_prove_independent_sheets(self):
        r=record();r['final_relative_corner_offset_mm']=[0.,12.]
        self.assertEqual(score(r)['score'],.5)
        r=record();r['release_seconds']=0.
        self.assertEqual(score(r)['score'],.5)

    def test_sliding_either_direction_counts_without_disjoint_sheets(self):
        r=record();r['final_relative_corner_offset_mm']=[-30.,12.]
        self.assertEqual(score(r)['score'],1.)
        r['final_relative_corner_offset_mm']=[0.,-18.]
        self.assertEqual(score(r)['score'],1.)

    def test_initial_stagger_cannot_be_counted_as_new_motion(self):
        r=record();r['final_relative_corner_offset_mm']=[0.,30.]
        self.assertEqual(score(r)['score'],.5)
        r['initial_relative_corner_offset_mm']=[0.,0.]
        self.assertFalse(score(r)['record_valid'])

    def test_missing_or_nonfinite_observations_fail_closed(self):
        r = record()
        del r["checks"]["both_sheet_faces_inspected"]
        self.assertFalse(score(r)["record_valid"])
        r = record()
        r["maximum_new_tear_mm"] = float("nan")
        self.assertFalse(score(r)["record_valid"])


if __name__ == "__main__":
    unittest.main()
