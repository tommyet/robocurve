"""A still or a one-frame score cannot satisfy the native final video hold."""
import unittest
from audit_trial import verify_final_full_score_hold
class Tests(unittest.TestCase):
 def rows(self,n):return [{'time':i*.05,'metrics':{'score':1.}}for i in range(n)]
 def test_requires_elapsed_second_not_twenty_sample_count(self):
  with self.assertRaises(ValueError):verify_final_full_score_hold(self.rows(20))
  self.assertAlmostEqual(verify_final_full_score_hold(self.rows(21))['full_score_elapsed_s'],1.)
 def test_only_final_consecutive_full_score_span_counts(self):
  rows=self.rows(40);rows[30]['metrics']['score']=.75
  with self.assertRaises(ValueError):verify_final_full_score_hold(rows)
 def test_missing_sample_cannot_be_replaced_by_video_padding(self):
  rows=self.rows(22);del rows[10]
  with self.assertRaises(ValueError):verify_final_full_score_hold(rows)
if __name__=='__main__':unittest.main()
