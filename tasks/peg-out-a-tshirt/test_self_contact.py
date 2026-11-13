"""Geometric controls for the independent cloth-intersection rejection audit."""
import unittest
import numpy as np
from audit_self_contact import crossing_pairs


class TransverseCrossingControls(unittest.TestCase):
    def setUp(self):
        self.a=np.array([[0.,0.,0.],[.01,0.,0.],[0.,.01,0.]])
        self.faces=np.array([[0,1,2],[3,4,5]])

    def test_separated_layers(self):
        self.assertEqual(crossing_pairs(np.r_[self.a,self.a+[0,0,.0016]],self.faces,cell=.005),[])

    def test_coincident_contact_is_not_transverse(self):
        self.assertEqual(crossing_pairs(np.r_[self.a,self.a[::-1]],self.faces,cell=.005),[])

    def test_actual_transverse_crossing(self):
        b=np.array([[.002,-.002,-.003],[.002,.008,.003],[.002,.008,-.003]])
        self.assertEqual(crossing_pairs(np.r_[self.a,b],self.faces,cell=.005),[[0,1]])

    def test_sewn_shared_vertex_neighbour_excluded(self):
        points=np.array([[0.,0.,0.],[.01,0.,0.],[0.,.01,0.],[.002,.008,.003],[.002,.008,-.003]])
        self.assertEqual(crossing_pairs(points,np.array([[0,1,2],[0,3,4]]),cell=.005),[])


if __name__=='__main__':unittest.main()
