"""CPU geometry/rubric checks. These are not a simulated task demonstration."""
import unittest
import numpy as np
from cloth_mesh import tshirt,edge_strain
from scene import initial_layout,TABLE,support_geometry
from scoring import score


class Geometry(unittest.TestCase):
    def test_garment_has_four_openings_and_two_sewn_layers(self):
        m=tshirt()
        self.assertEqual(len(m.audit()['boundary_loops']),4)
        self.assertTrue(m.audit()['connected'])
        self.assertGreater(np.ptp(m.rest[:,2]),.001)
        self.assertGreater(m.audit()['surface_area_m2'],.18)
    def test_start_is_untouched_rest_shape_above_table(self):
        m=tshirt(); p=initial_layout(m)
        self.assertLess(np.abs(edge_strain(m.rest,p,m.faces)).max(),1e-10)
        self.assertGreater(p[:,2].min(),TABLE+.001)

    def test_support_clearance_checks_triangles_not_only_nodes(self):
        from fixture_clearance import fixture_intersections
        mesh=tshirt(); p=initial_layout(mesh)
        self.assertFalse(any(fixture_intersections(p,mesh.faces,support_geometry(),margin=.001).values()))
        lowered=p.copy();lowered[:,2]-=.005
        self.assertTrue(any(fixture_intersections(lowered,mesh.faces,support_geometry(),margin=0.).values()))


class Judging(unittest.TestCase):
    def record(self):
        return dict(evidence_sha256={k:'0'*64 for k in ('released_video','left_jaw_photo','right_jaw_photo')},
                    integrity_checked=True,intact=True,unsupported_hold_s=5.,minimum_clearance_mm=20.,
                    retained_pegs=[True,True],peg_separation_mm=200.,supported_only_by_line_and_pegs=True)
    def test_visible_retention_drives_credit(self):
        j=self.record(); self.assertEqual(score(j),1.)
        j['retained_pegs']=[True,False];self.assertEqual(score(j),.5)
        j['retained_pegs']=[False,False];self.assertEqual(score(j),0.)
    def test_held_or_resting_garment_fails(self):
        for field,value in [('unsupported_hold_s',4.99),('minimum_clearance_mm',19.99),('intact',False),('supported_only_by_line_and_pegs',False)]:
            j=self.record();j[field]=value;self.assertEqual(score(j),0.)
    def test_missing_integrity_or_evidence_cannot_score(self):
        for field in ('integrity_checked','evidence_sha256'):
            j=self.record();del j[field]
            with self.assertRaises(ValueError):score(j)
    def test_two_adjacent_pegs_are_not_full_credit(self):
        j=self.record();j['peg_separation_mm']=20.;self.assertEqual(score(j),.5)
    def test_unknown_numeric_measurement_cannot_score(self):
        j=self.record();j['minimum_clearance_mm']=float('nan')
        with self.assertRaises(ValueError):score(j)


if __name__=='__main__':unittest.main()
