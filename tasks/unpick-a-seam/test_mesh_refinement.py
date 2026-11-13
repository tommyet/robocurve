import unittest
from collections import Counter
import numpy as np
from geometry import patch,STITCH_Y


class HoleMeshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=patch(hole_half=.0008)
        cls.refined=patch(hole_half=.0008,hole_mesh_spacing=.0004)

    def test_quality_candidate_preserves_holes_and_eliminates_sliver_elements(self):
        from quality_mesh import quality_patch,quality
        for left in (True,False):
            mesh=quality_patch(left);q=quality(mesh)
            expected=patch(left,hole_half=.0008).audit()
            self.assertAlmostEqual(q['surface_area_m2'],expected['surface_area_m2'],places=14)
            self.assertEqual(q['boundary_loops'],13)
            self.assertLess(q['triangles'],3000)
            self.assertGreaterEqual(q['minimum_edge_m'],.0004-1e-12)
            self.assertGreater(q['minimum_angle_degrees'],17.)
            triangles=mesh.rest[mesh.faces]
            self.assertTrue(np.all(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])[:,2]>0.))

    def test_refinement_preserves_surface_area_connectivity_and_hole_count(self):
        a,b=self.base.audit(),self.refined.audit()
        self.assertEqual(b['boundary_loops'],13)
        self.assertTrue(b['connected'])
        self.assertAlmostEqual(a['surface_area_m2'],b['surface_area_m2'],places=15)
        np.testing.assert_allclose(self.base.rest.min(0),self.refined.rest.min(0),atol=1e-15)
        np.testing.assert_allclose(self.base.rest.max(0),self.refined.rest.max(0),atol=1e-15)

    def test_all_hole_edges_are_resolved_without_resizing_openings(self):
        mesh=self.refined
        counts=Counter(tuple(sorted((int(a),int(b)))) for face in mesh.faces
                       for a,b in zip(face,np.roll(face,-1)))
        checked=0
        for (a,b),count in counts.items():
            if count!=1:continue
            midpoint=(mesh.rest[a]+mesh.rest[b])/2
            if any(abs(max(abs(midpoint[0]-x),abs(midpoint[1]-y))-.0008)<1e-12
                   for x in (.295,.305) for y in STITCH_Y):
                self.assertLessEqual(np.linalg.norm(mesh.rest[a]-mesh.rest[b]),.0004*(1+1e-10))
                checked+=1
        self.assertGreaterEqual(checked,12*16)

    def test_refinement_preserves_triangle_orientation_and_rejects_bad_spacing(self):
        triangles=self.refined.rest[self.refined.faces]
        normal=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
        self.assertTrue(np.all(normal[:,2]>0.))
        with self.assertRaises(ValueError):patch(hole_mesh_spacing=0.)


if __name__=='__main__':unittest.main()
