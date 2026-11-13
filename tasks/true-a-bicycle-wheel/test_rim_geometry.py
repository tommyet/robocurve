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
            self.assertAlmostEqual(np.min(np.abs(points[np.isclose(points[:,1],.008),0])),.005/2)
            self.assertAlmostEqual(np.ptp(points[:,2]),.004)
            inner=points[np.isclose(np.abs(points[:,0]),.00325/2)]
            self.assertLess(float(inner[:,1].min()),-.00323/2)
            self.assertGreater(float(inner[:,1].max()),.00323/2)
            triangles=points[faces]
            volume=np.einsum('ij,ij->i',triangles[:,0],np.cross(triangles[:,1],triangles[:,2])).sum()/6
            self.assertGreater(volume,0.)


class WheelClockingTests(unittest.TestCase):
    def test_clocking_preserves_axle_and_relative_geometry(self):
        from wheel_scene import wheel_world_frame,spoke_phase
        from plan_turns import nominal_nipple
        angle=np.deg2rad(10.);hub=np.array((.35,0.,1.005))
        frame=wheel_world_frame(angle)
        np.testing.assert_allclose(frame[:,2],[1.,0.,0.],atol=1e-14)
        for spoke in (0,2,11,31):
            p,R=nominal_nipple(spoke,np.pi/4)
            actual_p,actual_R=nominal_nipple(spoke,np.pi/4,angle)
            np.testing.assert_allclose(actual_p-hub,spoke_phase(angle)@(p-hub),atol=1e-14)
            np.testing.assert_allclose(actual_R,spoke_phase(angle)@R,atol=1e-14)
            np.testing.assert_allclose(actual_R.T@frame,R.T@wheel_world_frame(),atol=1e-14)


class ToolAccessTests(unittest.TestCase):
    def test_nipple_working_flats_and_jaw_are_inside_rim_inner_edge(self):
        from wheel_scene import NIPPLE_FLAT_LENGTH_M
        from plan_turns import nominal_nipple
        hub=np.array((.35,0.,1.005))
        for clock in (0.,np.pi/18):
            for spoke in range(32):
                p,R=nominal_nipple(spoke,0.,clock)
                # All flat ends lie on the open hub side of the20mm deep rim.
                points=np.array([p+R@np.array((x,y,z))
                    for x in (-NIPPLE_FLAT_LENGTH_M/2,NIPPLE_FLAT_LENGTH_M/2)
                    for y in (-.001625,.001625) for z in (-.001625,.001625)])
                radial=np.linalg.norm((points-hub)[:,1:],axis=1)
                self.assertLess(float(radial.max()),.200)
