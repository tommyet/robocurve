"""Geometry/material checks for a candidate, not native contact evidence."""
import unittest
import numpy as np
from scipy.spatial.transform import Rotation
from facet_paper import coupon_mesh,box_coupon_mesh,box_task_mesh,mechanics,measured_surface,ShellMaterial


class FacetPaperTests(unittest.TestCase):
    def test_box_panels_preserve_paper_area_holes_mass_and_rigid_motion(self):
        mesh=box_coupon_mesh();model=mechanics(mesh,primitive_boxes=True)
        self.assertEqual(len(model['masses']),152)
        self.assertAlmostEqual(mesh.audit()['surface_area_m2'],.024*.020-2*.0006*.0008)
        self.assertAlmostEqual(sum(model['masses']),mesh.audit()['mass_kg'])
        centres=model['centres']
        for x0,x1,y0,y1 in mesh.holes:
            self.assertFalse(np.any((centres[:,0]>x0)&(centres[:,0]<x1)&
                                    (centres[:,1]>y0)&(centres[:,1]<y1)))
        r=Rotation.from_rotvec([.7,-.3,.1]);translation=np.array([.1,-.2,.4])
        poses=np.c_[r.apply(centres)+translation,np.tile(r.as_quat(),(len(centres),1))]
        points,guard=measured_surface(dict(mesh=mesh,model=model),poses)
        self.assertTrue(guard['valid'])
        np.testing.assert_allclose(points,r.apply(mesh.rest)+translation,atol=1e-14)
        poses[0,2]+=.0001
        self.assertFalse(measured_surface(dict(mesh=mesh,model=model),poses)[1]['valid'])

    def test_full_box_sheets_keep_real_a5_dimensions_and_punctures(self):
        from full_scene import SHEET_CENTRES,STAPLE_XY
        for i in range(2):
            mesh=box_task_mesh(i);model=mechanics(mesh,primitive_boxes=True)
            np.testing.assert_allclose(np.ptp(mesh.rest,axis=0),(.21,.148,0.),atol=1e-12)
            self.assertAlmostEqual(sum(model['masses']),(.21*.148-2*.0008*.0006)*.080)
            centers=np.array([[(a+b)/2,(c+d)/2] for a,b,c,d in mesh.holes])+SHEET_CENTRES[i]
            np.testing.assert_allclose(centers,[(STAPLE_XY[0],STAPLE_XY[1]-.0064),
                                               (STAPLE_XY[0],STAPLE_XY[1]+.0064)],atol=1e-12)

    def test_box_hinge_flexural_stiffness_is_width_scaled(self):
        mesh=box_coupon_mesh();material=ShellMaterial();model=mechanics(mesh,primitive_boxes=True)
        for hinge in model['hinges']:
            a,b=mesh.rest[list(hinge['edge'])];axis=(b-a)/np.linalg.norm(b-a)
            width=sum(np.linalg.norm(np.cross(model['centres'][i]-hinge['anchor'],axis))
                      for i in hinge['faces'])
            self.assertAlmostEqual(hinge['stiffness_nm_rad'],material.rigidity_nm*np.linalg.norm(b-a)/width)
            self.assertAlmostEqual(hinge['break_force_n'],1500*np.linalg.norm(b-a))

    def test_physical_mass_and_finite_strength(self):
        mesh=coupon_mesh();model=mechanics(mesh);material=ShellMaterial()
        self.assertAlmostEqual(sum(model['masses']),mesh.audit()['mass_kg'])
        self.assertAlmostEqual(material.rigidity_nm,2e9*.0001**3/(12*(1-.3**2)))
        for h in model['hinges']:
            length=np.linalg.norm(mesh.rest[h['edge'][1]]-mesh.rest[h['edge'][0]])
            self.assertAlmostEqual(h['break_force_n'],1500*length)
            self.assertGreater(h['stiffness_nm_rad'],0.)

    def test_rigid_motion_preserves_surface_and_detects_one_open_hinge(self):
        mesh=coupon_mesh();model=mechanics(mesh);shell=dict(mesh=mesh,model=model)
        r=Rotation.from_rotvec([.2,-.3,.1]);translation=np.array([.1,-.2,.4])
        poses=np.c_[r.apply(model['centres'])+translation,np.tile(r.as_quat(),(len(mesh.faces),1))]
        points,guard=measured_surface(shell,poses)
        self.assertTrue(guard['valid']);np.testing.assert_allclose(points,r.apply(mesh.rest)+translation,atol=1e-14)
        poses[0,2]+=.0001
        _,guard=measured_surface(shell,poses)
        self.assertFalse(guard['valid'])


if __name__=='__main__':unittest.main()
