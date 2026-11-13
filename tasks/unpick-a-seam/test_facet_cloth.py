import unittest
import numpy as np
from scipy.spatial.transform import Rotation
from facet_cloth import shell_mesh,mechanics,measured_surface,ShellMaterial
from quality_mesh import quality_patch


class FacetTests(unittest.TestCase):
    def test_same_material_surface_and_openings(self):
        for upper in (True,False):
            mesh=shell_mesh(upper);reference=quality_patch(upper)
            self.assertEqual(mesh.audit()['boundary_loops'],13)
            self.assertAlmostEqual(mesh.audit()['surface_area_m2'],reference.audit()['surface_area_m2'],14)
            np.testing.assert_allclose(mesh.rest.min(0),reference.rest.min(0))
            np.testing.assert_allclose(mesh.rest.max(0),reference.rest.max(0))
            self.assertEqual(len(mesh.faces),236)

    def test_mass_and_passive_bending_are_finite_and_positive(self):
        mesh=shell_mesh();material=ShellMaterial();model=mechanics(mesh,material)
        self.assertAlmostEqual(model['masses'].sum(),mesh.audit()['surface_area_m2']*.0004*350.,14)
        self.assertTrue(all(h['stiffness_nm_rad']>0 and h['damping_nms_rad']>0 for h in model['hinges']))
        for h in model['hinges']:
            np.testing.assert_allclose(h['frame'].T@h['frame'],np.eye(3),atol=1e-12)
            self.assertAlmostEqual(np.linalg.det(h['frame']),1.,12)
        self.assertLess(len(model['hinges']),400)

    def test_measured_reconstruction_and_gap_guard(self):
        mesh=shell_mesh();model=mechanics(mesh);shell={'mesh':mesh,'model':model}
        r=Rotation.from_euler('xyz',[.2,-.4,.1]);shift=np.array([.1,-.2,.3])
        poses=np.column_stack((r.apply(model['centres'])+shift,
                               np.tile(r.as_quat(),(len(mesh.faces),1))))
        points,audit=measured_surface(shell,poses)
        np.testing.assert_allclose(points,r.apply(mesh.rest)+shift,atol=1e-12)
        self.assertTrue(audit['valid']);self.assertLess(audit['maximum_hinge_endpoint_gap_m'],1e-12)
        poses[model['hinges'][0]['faces'][0],0]+=.0002
        _,audit=measured_surface(shell,poses)
        self.assertFalse(audit['valid'])
        self.assertGreater(audit['maximum_hinge_endpoint_gap_m'],.00019)

    def test_primitive_rectangles_preserve_surface_and_rigid_pose(self):
        for upper in (True,False):
            mesh=shell_mesh(upper);model=mechanics(mesh,primitive_boxes=True)
            self.assertEqual(len(model['points']),118)
            self.assertEqual(len(model['hinges']),189)
            self.assertAlmostEqual(model['masses'].sum(),.0008356992,14)
            r=Rotation.from_euler('xyz',[.9,.2,-.3]);shift=np.array([.3,.1,-.2])
            poses=np.column_stack((r.apply(model['centres'])+shift,
                                   np.tile(r.as_quat(),(len(model['centres']),1))))
            points,audit=measured_surface({'mesh':mesh,'model':model},poses)
            np.testing.assert_allclose(points,r.apply(mesh.rest)+shift,atol=1e-12)
            self.assertTrue(audit['valid'])
            self.assertTrue(all(h['stiffness_nm_rad']>0 for h in model['hinges']))


if __name__=='__main__':unittest.main()
