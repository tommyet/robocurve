"""Exact transform reuse must not reuse moving-object collision answers."""
import unittest
import numpy as np
from unittest.mock import patch
from turnover_safety import Geometry,BASES
from yam_arena.constants import READY,FINGER_OPEN
class Tests(unittest.TestCase):
 def test_exact_transforms_match_uncached_and_are_immutable(self):
  a,b=Geometry(),Geometry(cache_parts=True);q=np.array(READY);f=[FINGER_OPEN]*2
  for x,y in zip(a.parts('left',q,f),b.parts('left',q,f)):
   self.assertEqual(x[0],y[0]);np.testing.assert_array_equal(x[1],y[1]);self.assertFalse(y[1].flags.writeable)
  with patch.object(b.model,'world',wraps=b.model.world)as world:
   b.parts('left',q,f);self.assertEqual(world.call_count,0)
   z=q.copy();z[0]+=1e-8;b.parts('left',z,f);self.assertEqual(world.call_count,1)
 def test_obstacle_change_is_checked_despite_cached_robot(self):
  a=Geometry(cache_parts=True);q=np.array(READY);f=[FINGER_OPEN]*2;other=a.parts('right',q,f)
  obs={'moving':(np.array([10.,10.,10.]),np.eye(3),(.01,.01,.01))}
  clear=a.guard('left',q,f,obs,other);self.assertTrue(clear['safe'])
  mesh=a.parts('left',q,f);v=mesh[-1][1].reshape(-1,3);obs['moving']=(v.mean(0),np.eye(3),(.10,.10,.10))
  collision=a.guard('left',q,f,obs,other);self.assertFalse(collision['safe']);self.assertEqual(collision['hard_pair'][-1],'moving')
 def test_cache_is_explicitly_clearable_and_base_is_part_of_key(self):
  a=Geometry(cache_parts=True);q=np.array(READY);f=[FINGER_OPEN]*2;x=a.parts('left',q,f)
  with patch.dict(BASES,{'left':BASES['left']+np.array([.1,0,0])}):
   y=a.parts('left',q,f);np.testing.assert_allclose(y[0][1],x[0][1]+[.1,0,0],atol=1e-15)
  a.clear_parts_cache();self.assertEqual(len(a._parts_cache),0)
if __name__=='__main__':unittest.main()
