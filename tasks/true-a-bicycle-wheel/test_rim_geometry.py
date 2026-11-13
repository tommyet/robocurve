import unittest
import numpy as np
from rim_geometry import sector_mesh, maximum_radial_chord_error_m


class RimGeometryTests(unittest.TestCase):
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
