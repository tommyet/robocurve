"""Regression for a thin line passing through a convex hand between vertices."""
import unittest
import numpy as np
from audit_motion import segment_hull_interval


class FiniteLine(unittest.TestCase):
    def setUp(self):
        # Unit cube centered at zero, outward planes. A millimetre-radius line
        # through its middle has no cube vertex inside the line.
        self.planes=np.column_stack((np.r_[np.eye(3),-np.eye(3)],np.ones(6)*.5))
    def test_crossing_detected_when_no_vertices_touch_line(self):
        interval=segment_hull_interval(np.array([0.,-1.,0.]),np.array([0.,1.,0.]),self.planes)
        self.assertIsNotNone(interval)
        self.assertGreater(interval[1],interval[0])
    def test_parallel_outside_rejected(self):
        self.assertIsNone(segment_hull_interval(np.array([.6,-1.,0.]),np.array([.6,1.,0.]),self.planes))
    def test_finite_extent_respected(self):
        self.assertIsNone(segment_hull_interval(np.array([0.,.6,0.]),np.array([0.,1.,0.]),self.planes))
    def test_surface_tangency_is_not_axis_penetration(self):
        self.assertIsNone(segment_hull_interval(np.array([.5,-1.,0.]),np.array([.5,1.,0.]),self.planes))


if __name__=='__main__':unittest.main()
