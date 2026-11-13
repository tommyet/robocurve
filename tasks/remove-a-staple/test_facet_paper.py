"""Geometry/material checks for a candidate, not native contact evidence."""
import unittest
import numpy as np
from scipy.spatial.transform import Rotation
from facet_paper import (coupon_mesh,box_coupon_mesh,box_task_mesh,mechanics,measured_surface,
    ShellMaterial,geometric_edge_measurements,_rectangular_mesh)


class FacetPaperTests(unittest.TestCase):
    def test_geometry_diagnostic_does_not_stop_on_harmless_overlap(self):
        mesh=_rectangular_mesh(np.array((0.,.01,.02)),np.array((0.,.01)),[])
        model=mechanics(mesh,primitive_boxes=True);shell=dict(mesh=mesh,model=model)
        poses=np.c_[model['centres'],np.tile((0.,0.,0.,1.),(2,1))]
        poses[0,0]+=.0002
        nodes,old=measured_surface(shell,poses)
        new_nodes,new=measured_surface(shell,poses,geometry_aperture_m=.00015)
        self.assertFalse(old['valid']);self.assertTrue(new['valid'])
        self.assertAlmostEqual(new['geometry']['maximum_empty_aperture_m'],0.)
        np.testing.assert_array_equal(nodes,new_nodes)
        poses[0,0]-=.0004
        self.assertFalse(measured_surface(shell,poses,geometry_aperture_m=.00015)[1]['valid'])

    def test_geometry_diagnostic_rejects_lost_edge_overlap(self):
        mesh=_rectangular_mesh(np.array((0.,.01,.02)),np.array((0.,.01)),[])
        model=mechanics(mesh,primitive_boxes=True);shell=dict(mesh=mesh,model=model)
        poses=np.c_[model['centres'],np.tile((0.,0.,0.,1.),(2,1))]
        poses[0,1]+=.011
        _,result=measured_surface(shell,poses,geometry_aperture_m=.00015)
        self.assertFalse(result['valid'])
        self.assertEqual(result['geometry']['edges_without_overlap'],1)

    def edge_geometry(self,shift):
        mesh=_rectangular_mesh(np.array((0.,.01,.02)),np.array((0.,.01)),[])
        model=mechanics(mesh,primitive_boxes=True)
        world=model['points'].copy();world[0]+=shift
        return geometric_edge_measurements(model,world,np.tile(np.eye(3),(2,1,1)))

    def test_compressed_edges_are_not_reported_as_open_cracks(self):
        result=self.edge_geometry(np.array((.00012,0.,0.)))
        self.assertAlmostEqual(result['maximum_empty_aperture_m'],0.)
        self.assertAlmostEqual(result['maximum_across_edge_compression_m'],.00012)

    def test_positive_edge_opening_is_retained(self):
        result=self.edge_geometry(np.array((-.00012,0.,0.)))
        self.assertAlmostEqual(result['maximum_empty_aperture_m'],.00012)
        self.assertAlmostEqual(result['maximum_across_edge_compression_m'],0.)

    def test_normal_clearance_accounts_for_physical_panel_thickness(self):
        self.assertAlmostEqual(self.edge_geometry(np.array((0.,0.,.00008)))['maximum_empty_normal_clearance_m'],0.)
        self.assertAlmostEqual(self.edge_geometry(np.array((0.,0.,.00014)))['maximum_empty_normal_clearance_m'],.00004)

    def test_along_edge_slip_is_distinct_from_opening(self):
        result=self.edge_geometry(np.array((0.,.002,0.)))
        self.assertAlmostEqual(result['maximum_empty_aperture_m'],0.)
        self.assertAlmostEqual(result['maximum_along_edge_slip_m'],.002)
        self.assertAlmostEqual(result['minimum_shared_edge_overlap_m'],.008)
        self.assertEqual(result['edges_without_overlap'],0)

    def test_edge_opening_is_invariant_to_world_frame(self):
        mesh=_rectangular_mesh(np.array((0.,.01,.02)),np.array((0.,.01)),[])
        model=mechanics(mesh,primitive_boxes=True);world=model['points'].copy()
        world[0, :, 0]-=.00012
        R=Rotation.from_rotvec((.6,-.9,.2)).as_matrix()
        result=geometric_edge_measurements(model,world@R.T+(.1,-.3,.4),np.tile(R,(2,1,1)))
        self.assertAlmostEqual(result['maximum_empty_aperture_m'],.00012)
        self.assertAlmostEqual(result['maximum_empty_normal_clearance_m'],0.)

    def test_diagnostic_envelope_does_not_change_measured_geometry(self):
        mesh=box_coupon_mesh();model=mechanics(mesh,primitive_boxes=True)
        shell=dict(mesh=mesh,model=model)
        poses=np.c_[model['centres'],np.tile((0.,0.,0.,1.),(len(model['centres']),1))]
        poses[0,0]+=.00003;before=poses.copy()
        strict,first=measured_surface(shell,poses)
        diagnostic,second=measured_surface(shell,poses,.0001)
        self.assertFalse(first['valid']);self.assertTrue(second['valid'])
        self.assertAlmostEqual(first['maximum_hinge_endpoint_gap_m'],.00003)
        self.assertEqual(first['maximum_hinge_endpoint_gap_m'],second['maximum_hinge_endpoint_gap_m'])
        np.testing.assert_array_equal(strict,diagnostic)
        np.testing.assert_array_equal(before,poses)

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
