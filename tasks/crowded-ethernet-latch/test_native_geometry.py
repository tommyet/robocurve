"""Topology checks independent from Isaac; physical evidence needs run.py."""
import unittest
from config import *
class GeometryTests(unittest.TestCase):
 def test_eight_ports_six_neighbours_and_service(self):
  self.assertEqual(len({port(i) for i in range(8)}),8)
  self.assertEqual(len(USED),7)
  self.assertNotIn(TARGET,USED)
  self.assertIn(SERVICE,USED)
 def test_chains_connect_to_boot_and_have_reasonable_lengths(self):
  from math import dist
  for i in USED:
   p=cable_points(i)
   self.assertEqual(len(p),LINKS+1)
   self.assertLess(dist(p[0],port(i)),.020)
   self.assertTrue(all(.015<dist(a,b)<.018 for a,b in zip(p,p[1:])))
 def test_clip_has_clearance_and_return_spring(self):
  self.assertLess(RELEASE_TRAVEL,CLIP_TRAVEL)
  self.assertGreater(CLIP_STIFFNESS*RELEASE_TRAVEL,.1)
