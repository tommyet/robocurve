"""Distance lower bounds must never invent complete extraction."""
import unittest
import numpy as np
from assess_trace import box_distance,clearance_lower_bound,measured_wire


class GeometryEvidenceTests(unittest.TestCase):
    def test_enclosing_boxes_overlap_is_inconclusive_zero(self):
        d=box_distance([[0,0,0]],[[1,1,1]],[[.5,.5,.5]],[[2,2,2]])
        self.assertEqual(float(d[0,0]),0.)

    def test_diagonal_gap(self):
        d=box_distance([[0,0,0]],[[1,1,1]],[[4,5,1]],[[5,6,2]])
        self.assertEqual(float(d[0,0]),5.)

    def test_wire_surface_clearance_includes_thickness(self):
        wire=np.array([[[0.,0.,.02],[.01,0.,.02]]])
        paper=np.array([[-1.,-1.,0.],[1.,-1.,0.],[0.,1.,0.]])
        d=clearance_lower_bound(wire,[paper],[np.array([[0,1,2]])])
        self.assertGreater(d,.019)
        self.assertLess(d,.02)
        wire[:,:,2]=0.
        self.assertEqual(clearance_lower_bound(wire,[paper],[np.array([[0,1,2]])]),0.)

    def test_measured_quaternion_rotates_wire_axis(self):
        row={'hardware_names':['staple/wire_000'],
             'hardware_poses':[[1.,2.,3.,0.,0.,2**-.5,2**-.5]]}
        wire=measured_wire(row,[.02])
        np.testing.assert_allclose(wire,[[[1,1.99,3],[1,2.01,3]]],atol=1e-12)


if __name__=='__main__':unittest.main()
