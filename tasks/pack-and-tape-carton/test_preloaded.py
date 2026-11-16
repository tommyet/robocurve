import unittest
import numpy as np
from config import PRODUCTS,CENTER,BOARD,PRELOADED
from scoring import PackingScorer
from test_scoring import state
class Tests(unittest.TestCase):
 def test_two_items_fully_inside_and_separated_at_reset(self):
  self.assertTrue(PRELOADED);bounds=[];origin=np.array(CENTER)-[0,0,BOARD/2]
  for _,p,size,_,_ in PRODUCTS:
   local=np.array(p)-origin;lo=local-np.array(size)/2;hi=local+np.array(size)/2;self.assertTrue(np.all(lo>=np.array([-.104,-.084,.006])));self.assertTrue(np.all(hi<=np.array([.104,.084,.092])));bounds.append((lo,hi))
  self.assertGreater(bounds[1][0][0],bounds[0][1][0])
 def test_preload_has_zero_credit_and_closure_earns_progress(self):
  scorer=PackingScorer();s=state();self.assertEqual(scorer.update(s)['score'],0)
  s.update(time=.05,flap_angles=[0]*4,inner_flaps_under_outer=True);self.assertEqual(scorer.update(s)['score'],.25)
if __name__=='__main__':unittest.main()
