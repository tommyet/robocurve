"""CPU mesh and evidence-rubric checks, not physics or knot-success evidence."""
import unittest
import numpy as np
from cloth_mesh import necktie,edge_strain
from layout import initial_layout,fixture_geometry,NECK,TABLE
from fixture_clearance import fixture_intersections,triangle_box_intersects,triangle_cylinder_intersects
from scoring import score


class Geometry(unittest.TestCase):
    def test_strip_has_width_and_two_different_tips(self):
        m=necktie()
        self.assertEqual(len(m.audit()['boundary_loops']),1)
        self.assertGreater(np.ptp(m.rest[:,0]),.069)
        self.assertAlmostEqual(np.ptp(m.rest[:,1]),1.1)
        self.assertNotEqual(m.markers['wide_tip'],m.markers['narrow_tip'])
    def test_diagnostic_drape_does_not_stretch_the_reset_mesh(self):
        m=necktie();p=initial_layout(m)
        # Chords approximate a true cylinder; geometric strain is below 0.03%.
        self.assertLess(np.max(np.abs(edge_strain(m.rest,p,m.faces))),.0003)
    def test_all_drape_triangles_clear_every_fixture_by_one_mm(self):
        m=necktie();p=initial_layout(m)
        self.assertEqual(fixture_intersections(p,m.faces,fixture_geometry(),margin=.001),
                         {name:[] for name in fixture_geometry()})
    def test_inside_out_drape_flips_face_without_crossing_or_prestretch(self):
        m=necktie();front=initial_layout(m);back=initial_layout(m,inside_out=True)
        self.assertLess(np.max(np.abs(edge_strain(m.rest,back,m.faces))),.0003)
        self.assertEqual(fixture_intersections(back,m.faces,fixture_geometry(),margin=.001),
                         {name:[] for name in fixture_geometry()})
        row=m.markers['row_nodes'][40]
        width_front=front[row[-1]]-front[row[0]]
        width_back=back[row[-1]]-back[row[0]]
        np.testing.assert_allclose(width_front,-width_back,atol=1e-12)
        np.testing.assert_allclose(front[row].mean(0),back[row].mean(0),atol=1e-12)
    def test_previous_rear_post_intersection_is_detected(self):
        m=necktie();fixtures=fixture_geometry()
        fixtures['Post']['center']=(NECK[0]+.055,0.,(NECK[2]+TABLE)/2)
        self.assertGreater(len(fixture_intersections(initial_layout(m),m.faces,fixtures,margin=0.)['Post']),0)
    def test_rotated_collar_flap_uses_its_actual_box(self):
        triangle=np.array(((-.02,.08,0.),(.02,.08,0.),(0.,.09,0.)))
        R=np.array(((0.,-1.,0.),(1.,0.,0.),(0.,0.,1.)))
        spec=dict(kind='box',center=(0.,0.,0.),size=(.2,.02,.1),rotation=R.tolist())
        self.assertEqual(fixture_intersections(triangle,[[0,1,2]],{'flap':spec},margin=0.),{'flap':[0]})
        del spec['rotation']
        self.assertEqual(fixture_intersections(triangle,[[0,1,2]],{'flap':spec},margin=0.),{'flap':[]})
    def test_adult_candidate_starts_clear_of_folded_collar(self):
        from adult_layout import make_mesh,initial_layout as adult_initial,fixture_geometry as adult_fixtures
        mesh=make_mesh();points=adult_initial(mesh)
        self.assertEqual(fixture_intersections(points,mesh.faces,adult_fixtures(),margin=.001),{name:[] for name in adult_fixtures()})
        self.assertLess(np.max(np.abs(edge_strain(mesh.rest,points,mesh.faces))),.0003)
    def test_face_crossings_without_inside_vertices_are_detected(self):
        triangle=np.array(((-2.,-2.,0.),(2.,-2.,0.),(0.,3.,0.)))
        self.assertTrue(triangle_box_intersects(triangle,(0,0,0),(1,1,1)))
        self.assertTrue(triangle_cylinder_intersects(triangle,(0,0,0),.5,1.))
        self.assertFalse(triangle_box_intersects(triangle+(0,0,2),(0,0,0),(1,1,1)))
        self.assertFalse(triangle_cylinder_intersects(triangle+(0,0,2),(0,0,0),.5,1.))


class Judging(unittest.TestCase):
    def record(self):
        return dict(evidence_sha256={k:'0'*64 for k in ('released_video','front_photo','rear_photo')},
                    integrity_checked=True,intact=True,simple_knot_verified=True,released_hold_s=5.,
                    wide_face_out=True,narrow_end_hidden=True,knot_zone_offset_mm=10.,
                    neckband_gap_mm=5.,wide_tip_below_collar_mm=420.,narrow_tip_above_wide_tip_mm=50.)
    def test_complete_and_retained_but_undressed_knot(self):
        j=self.record();self.assertEqual(score(j),1.)
        j['wide_face_out']=False;self.assertEqual(score(j),.5)
        j['simple_knot_verified']=False;self.assertEqual(score(j),0.)
    def test_physical_invalidity_erases_credit(self):
        j=self.record();j['intact']=False;self.assertEqual(score(j),0.)
        j=self.record();j['released_hold_s']=4.9;self.assertEqual(score(j),0.)
    def test_good_knot_bad_fit_is_partial(self):
        j=self.record();j['neckband_gap_mm']=11.;self.assertEqual(score(j),.5)
        j=self.record();j['wide_tip_below_collar_mm']=100.;self.assertEqual(score(j),.5)
    def test_narrow_tip_below_wide_is_not_ready_to_wear(self):
        j=self.record();j['narrow_tip_above_wide_tip_mm']=-5.;self.assertEqual(score(j),.5)
    def test_adult_tip_length_band_is_inclusive(self):
        for length,expected in ((399.9,.5),(400.,1.),(440.,1.),(440.1,.5)):
            j=self.record();j['wide_tip_below_collar_mm']=length;self.assertEqual(score(j),expected)
    def test_missing_assessment_raises(self):
        j=self.record();del j['simple_knot_verified']
        with self.assertRaises(ValueError):score(j)
    def test_unknown_fit_measurement_cannot_score(self):
        j=self.record();j['neckband_gap_mm']=float('nan')
        with self.assertRaises(ValueError):score(j)


if __name__=='__main__':unittest.main()
