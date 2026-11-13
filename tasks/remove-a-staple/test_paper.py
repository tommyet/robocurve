import unittest
import numpy as np
from paper import perforated_sheet, ElasticDomainGuard, PaperIntegrityGuard, PaperMesh


class PaperTests(unittest.TestCase):
    def test_punctures_are_empty_and_mass_matches_material(self):
        mesh=perforated_sheet()
        centre=mesh.rest[mesh.faces].mean(1)
        for lo,hi,bottom,top in mesh.holes:
            self.assertFalse(np.any((centre[:,0]>lo)&(centre[:,0]<hi)&(centre[:,1]>bottom)&(centre[:,1]<top)))
        area=.030*.024-2*.00042*.00062
        self.assertAlmostEqual(mesh.audit()['surface_area_m2'],area,places=12)
        self.assertAlmostEqual(mesh.audit()['mass_kg'],area*.08,places=12)

    def test_rigid_rotations_do_not_count_as_damage(self):
        mesh=perforated_sheet();guard=ElasticDomainGuard(mesh)
        a=.73;R=np.array([[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]])
        result=guard.update(mesh.rest@R.T+[.4,-.2,1.])
        self.assertTrue(result['valid'])
        self.assertLess(result['maximum_tensile_strain'],1e-9)
        self.assertLess(result['maximum_surface_bending_strain'],1e-5)

    def test_stretch_failure_is_irreversible(self):
        mesh=perforated_sheet();guard=ElasticDomainGuard(mesh)
        p=mesh.rest.copy();p[:,0]*=1.01
        self.assertFalse(guard.update(p)['valid'])
        self.assertFalse(guard.update(mesh.rest)['valid'])
        self.assertAlmostEqual(guard.maximum_tensile_strain,.01,places=8)

    def test_sharp_fold_fails_even_without_stretch(self):
        mesh=perforated_sheet();guard=ElasticDomainGuard(mesh)
        p=mesh.rest.copy();select=p[:,1]>0
        p[select,2]=p[select,1];p[select,1]=0
        self.assertFalse(guard.update(p)['valid'])
        self.assertGreater(guard.maximum_bending_strain,.003)

    def test_bad_state_fails_closed(self):
        mesh=perforated_sheet();guard=ElasticDomainGuard(mesh)
        p=mesh.rest.copy();p[0,0]=np.nan
        self.assertFalse(guard.update(p)['valid'])
        self.assertFalse(guard.update(mesh.rest)['valid'])

    def test_task_allows_an_isometric_crease_but_reports_it(self):
        mesh=PaperMesh(np.array(((-.01,0.,0.),(.01,0.,0.),(0.,.01,0.),(0.,-.01,0.))),
                       np.array(((0,1,2),(1,0,3))),[])
        folded=mesh.rest.copy();folded[3]=[0.,0.,-.01]
        result=PaperIntegrityGuard(mesh).update(folded)
        self.assertTrue(result['valid'])
        self.assertIsNotNone(result['first_bending_warning'])
        self.assertFalse(result['bending_is_failure'])
        self.assertFalse(ElasticDomainGuard(mesh).update(folded)['valid'])

    def test_task_membrane_failure_remains_latched(self):
        mesh=perforated_sheet();guard=PaperIntegrityGuard(mesh)
        stretched=mesh.rest.copy();stretched[:,0]*=1.004
        self.assertFalse(guard.update(stretched)['valid'])
        self.assertFalse(guard.update(mesh.rest)['valid'])

    def test_degenerate_sheet_is_invalid_even_with_bending_warning_only(self):
        mesh=perforated_sheet();guard=PaperIntegrityGuard(mesh)
        flatline=mesh.rest.copy();flatline[:,1]=0
        self.assertFalse(guard.update(flatline)['valid'])


if __name__=='__main__':unittest.main()
