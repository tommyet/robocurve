import unittest
import numpy as np
from audit_self_contact import crossing_pairs


class SelfContactAudit(unittest.TestCase):
    def test_transverse_crossing(self):
        p=np.array([[-1,-1,0],[1,-1,0],[0,1,0],[0,-.5,-1],[0,-.5,1],[0,.5,0]])*.01
        for cell in (.005,.01,.02):
            with self.subTest(cell=cell):
                self.assertEqual(crossing_pairs(p,[[0,1,2],[3,4,5]],cell=cell),[[0,1]])

    def test_planes_cross_but_triangle_segments_do_not(self):
        # Both AABBs overlap and each triangle straddles the other's plane,
        # but their intersection-line intervals are disjoint.
        p=np.array([[-1,-1,0],[1,-1,0],[0,1,0],[0,-.5,1],[0,-.5,2],[0,2,-.1]])*.01
        for cell in (.005,.01,.02):
            with self.subTest(cell=cell):
                self.assertEqual(crossing_pairs(p,[[0,1,2],[3,4,5]],cell=cell),[])

    def test_contact_and_adjacent_faces_are_not_transverse_crossings(self):
        p=np.array([[-1,-1,0],[1,-1,0],[0,1,0],[-1,-1,.1],[1,-1,.1],[0,1,.1]])*.01
        self.assertEqual(crossing_pairs(p,[[0,1,2],[3,4,5]]),[])
        self.assertEqual(crossing_pairs(p,[[0,1,2],[0,3,4]]),[])


if __name__=='__main__':unittest.main()
