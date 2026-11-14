"""Geometry feedback regressions; no simulated completion claims."""
import unittest
import numpy as np
from feedback import capsule_gap,retaining_face,plug_fit,BootJawPredictor
from geometry import box_triangles
from collision_geometry import FingerGeometry
from robot import BOOT_LOCAL,R_GRIP
from config import *

class FeedbackGeometryTests(unittest.TestCase):
 def test_exact_capsule_support_does_not_use_square_radial_corners(self):
  # Radius1: a small cube around (.9,.9,0) is outside the round cylinder,
  # despite overlapping its enclosing square [-1,1]^2.
  triangles=box_triangles((.9,.9,0),(.02,.02,.02))
  self.assertGreater(capsule_gap(triangles,np.zeros(3),np.array((0,0,1)),2.,1.,.01),.2)
  touching=box_triangles((.8,0,0),(.1,.1,.1))
  self.assertEqual(capsule_gap(touching,np.zeros(3),np.array((0,0,1)),2.,1.),0.)
 def test_retention_uses_actual_clip_face_not_plug_reconstruction(self):
  clip=np.r_[np.array(port(TARGET))+[0,0,CLIP_Z],0,0,0,1.]
  self.assertTrue(retaining_face(clip,TARGET)['retained'])
  clip[0]-=.002
  self.assertFalse(retaining_face(clip,TARGET)['retained'])
  clip[0]+=.002;clip[2]-=.002
  self.assertFalse(retaining_face(clip,TARGET)['retained'])
 def test_actual_guide_footprint_requires_submillimetre_alignment(self):
  plug=np.r_[port(TARGET),0,0,0,1.]
  self.assertAlmostEqual(plug_fit(plug,TARGET)['minimum_clearance_m'],.0003)
  plug[2]+=.00025
  self.assertLess(plug_fit(plug,TARGET)['minimum_clearance_m'],.0001)
  plug[2]-=.00025;plug[1]+=.0006
  self.assertLess(plug_fit(plug,TARGET)['minimum_clearance_m'],0.)
 def test_expected_level_jaw_stops_are_independent_of_force_target(self):
  plug=np.r_[port(SERVICE),0,0,0,1.]
  result=BootJawPredictor(FingerGeometry()).predict(plug,plug[:3]+BOOT_LOCAL,R_GRIP,np.array((-.0035,-.0035)))
  np.testing.assert_allclose(result['opening_m'],[.003474,.003474],atol=.00002)
  self.assertTrue(all(result['contact_possible']))

 def test_nonfinite_geometry_fails_closed(self):
  from feedback import clearance
  triangle=box_triangles((0,0,0),(1,1,1));triangle[0,0,0]=np.nan
  result=clearance([triangle],({},{},{}))
  self.assertEqual(result['minimum_gap_m'],0.)
  self.assertIn('nonfinite',result['invalid'])
  clip=np.array([np.nan,0,0,0,0,0,1.])
  self.assertFalse(retaining_face(clip,TARGET)['retained'])
