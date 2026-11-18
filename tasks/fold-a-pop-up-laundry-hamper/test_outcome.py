"""Physical dimensions must include cloth and ignore rigid scene orientation."""
import unittest
import numpy as np
from scipy.spatial.transform import Rotation
from model import Model

class OutcomeTests(unittest.TestCase):
 def test_dimensions_are_rigid_transform_invariant(self):
  m=Model();a=m.measure();Q=Rotation.from_euler('xyz',[21,47,13],degrees=True)
  m.poses[:,:3]=Q.apply(m.poses[:,:3])+[.4,-.3,.8]
  m.poses[:,3:]=(Q*Rotation.from_quat(m.poses[:,3:])).as_quat()
  m.R=Rotation.from_quat(m.poses[:,3:]).as_matrix();b=m.measure()
  for key in ['bundle_long_mm','bundle_short_mm','thickness_mm']:
   self.assertAlmostEqual(a[key],b[key],places=7)
  self.assertEqual(m.score(),0.)
 def test_protruding_fabric_is_included(self):
  m=Model();before=m.measure();m.poses[m.index['mesh_0_0_0'],2]+=.2
  after=m.measure();self.assertGreater(after['thickness_mm'],before['thickness_mm']+150)

if __name__=='__main__':unittest.main()
