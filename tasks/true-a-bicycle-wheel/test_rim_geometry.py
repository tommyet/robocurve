import unittest
import numpy as np
from rim_geometry import sector_mesh, maximum_radial_chord_error_m
from wheel_scene import x_frame


class RimGeometryTests(unittest.TestCase):
    def test_spoke_frame_does_not_destroy_metric_placement_vector(self):
        direction=np.array((.183,-.014,-.025));original=direction.copy()
        frame=x_frame(direction)
        np.testing.assert_array_equal(direction,original)
        np.testing.assert_allclose(frame[:,0],original/np.linalg.norm(original),atol=1e-14)
        np.testing.assert_allclose(frame.T@frame,np.eye(3),atol=1e-14)

    def test_real_contact_edge_is_round_to_less_than_rubric_tolerance(self):
        self.assertGreater(maximum_radial_chord_error_m(subdivisions=1),.001)
        self.assertLess(maximum_radial_chord_error_m(),.00003)

    def test_sector_mesh_is_closed_and_nondegenerate(self):
        points,faces=sector_mesh()
        e=np.sort(np.concatenate((faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]])),axis=1)
        _,count=np.unique(e,axis=0,return_counts=True)
        self.assertTrue(np.all(count==2))
        p=points[faces]
        self.assertTrue(np.all(np.linalg.norm(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),axis=1)>1e-8))


if __name__=='__main__':unittest.main()


class WrenchLeadInTests(unittest.TestCase):
    def test_mouth_is_wider_but_working_slot_unchanged(self):
        from wheel_scene import wrench_jaw_mesh
        for side in (-1,1):
            points,faces=wrench_jaw_mesh(side)
            self.assertEqual(points.shape,(10,3))
            self.assertEqual(faces.shape,(16,3))
            self.assertAlmostEqual(np.min(np.abs(points[:,0])),.00325/2)
            self.assertAlmostEqual(np.min(np.abs(points[np.isclose(points[:,1],.004),0])),.005/2)
            self.assertAlmostEqual(np.ptp(points[:,2]),.004)
            triangles=points[faces]
            volume=np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2])).sum()/6
            self.assertGreater(volume,0.)
