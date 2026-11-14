"""A small numerical boundary band must never exempt intact material."""
import unittest
import numpy as np
from contact_audit import ThreadClothAudit
from facet_cloth import mechanics
from geometry import Mesh
from panel_diagnostics import solid_contacts

class BoundaryContactTest(unittest.TestCase):
    def setUp(self):
        self.points=np.array([[0.,0.,0.],[.01,0.,0.],[.01,.01,0.],[0.,.01,0.]])
        self.faces=np.array([[0,1,2],[0,2,3]])
    def segment(self,x,y):return np.array([[[x,y,-.001],[x,y,.001]]])
    def test_boundary_band_records_shallow_contact(self):
        audit=ThreadClothAudit(self.faces,boundary_tolerance_m=.0001)
        self.assertTrue(audit.update(self.points,self.segment(.00005,.005),0.))
        self.assertGreater(audit.summary()['tolerated_boundary_hits'],0)
        self.assertAlmostEqual(audit.maximum_tolerated_depth_m,.00005)
    def test_interior_diagonal_is_not_a_hole(self):
        audit=ThreadClothAudit(self.faces,boundary_tolerance_m=.0001)
        self.assertFalse(audit.update(self.points,self.segment(.005,.005),0.))
    def test_deeper_crossing_still_fails(self):
        audit=ThreadClothAudit(self.faces,boundary_tolerance_m=.0001)
        self.assertFalse(audit.update(self.points,self.segment(.0002,.005),0.))
    def test_default_is_unchanged(self):
        self.assertFalse(ThreadClothAudit(self.faces).update(self.points,self.segment(.00005,.005),0.))
    def test_native_boundary_and_internal_panel_edge(self):
        points=np.array([[0.,0.,0.],[.005,0.,0.],[.01,0.,0.],[0.,.01,0.],[.005,.01,0.],[.01,.01,0.]])
        mesh=Mesh(points,np.array([[0,1,4],[0,4,3],[1,2,5],[1,5,4]]))
        model=mechanics(mesh,primitive_boxes=True)
        poses=np.c_[model['centres'],np.tile([0.,0.,0.,1.],(2,1))]
        shallow=solid_contacts(model,poses,self.segment(.00005,.005),boundary_tolerance_m=.0001)
        self.assertFalse(shallow['native_midplane_intersections'])
        self.assertTrue(shallow['tolerated_boundary_intersections'])
        inside=solid_contacts(model,poses,self.segment(.005,.005),boundary_tolerance_m=.0001)
        self.assertTrue(inside['native_midplane_intersections'])

if __name__=='__main__':unittest.main()
