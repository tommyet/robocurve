import unittest
import numpy as np
from turnover_contacts import summarize,TARGETS
class Tests(unittest.TestCase):
 def test_force_family_sum_does_not_rely_on_filter_order(self):
  a=np.arange(6*len(TARGETS),dtype=float).reshape(1,2,len(TARGETS),3)/10
  x=summarize(a,['tip_left','tip_right']);y=summarize(a[:,:,::-1],['tip_left','tip_right'])
  np.testing.assert_allclose(x['family_normal_force_on_fingertips_w_N'],y['family_normal_force_on_fingertips_w_N'])
  self.assertFalse(x['individual_filter_column_order_native_verified'])
 def test_opposed_sensor_reactions_remain_opposed(self):
  a=np.zeros((1,2,len(TARGETS),3));a[0,0,0,1]=2.
  l=summarize(a,['tip_left','tip_right']);r=summarize(-a,['tip_right','tip_left'])
  self.assertLess(np.dot(l['family_normal_force_on_fingertips_w_N'],r['family_normal_force_on_fingertips_w_N']),0.)
 def test_balanced_clamp_has_nonzero_force_magnitudes_even_if_net_zero(self):
  a=np.zeros((1,2,len(TARGETS),3));a[0,0,0,0]=2.;a[0,1,0,0]=-2.
  r=summarize(a,['tip_left','tip_right']);self.assertEqual(r['family_normal_force_norm_N'],0.);self.assertEqual(r['family_sum_of_normal_force_magnitudes_N'],4.)
 def test_bad_shape_wrong_body_and_nonfinite_rejected(self):
  a=np.zeros((1,2,len(TARGETS),3))
  for value,names in [(a[:,:,:3],['tip_left','tip_right']),(a,['base','tip_left']),(a+np.nan,['tip_left','tip_right'])]:
   with self.assertRaises(ValueError):summarize(value,names)
if __name__=='__main__':unittest.main()
