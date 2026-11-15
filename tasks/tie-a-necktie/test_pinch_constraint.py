import unittest
import numpy as np
from pinch_constraint import Pinch


class TestPinch(unittest.TestCase):
    def patch(self):
        return np.array([[0., y, z] for y in (-.003, 0, .003) for z in (-.012, -.008, -.004)] + [[.1,.1,.1]])

    def test_contact_then_carry_only_held_nodes(self):
        p=self.patch(); v=np.zeros_like(p); c=Pinch(); r=np.eye(3)
        c.update(p,v,np.zeros(3),r,.002,.004)
        self.assertEqual(len(c.indices),9)
        original=p.copy()
        c.update(p,v,np.array([0,0,.005]),r,.002,.004)
        np.testing.assert_allclose(p[:9],original[:9]+[0,0,.005])
        np.testing.assert_array_equal(p[9],original[9])

    def test_closing_does_not_bury_contact_patch_in_finger(self):
        p=self.patch();p[:9,0]=-.0018;c=Pinch();v=np.zeros_like(p)
        c.update(p,v,np.zeros(3),np.eye(3),.004,.004)
        c.update(p,v,np.zeros(3),np.eye(3),0.,.004)
        np.testing.assert_allclose(c.local[:,0],0.)
        c.update(p,v,np.zeros(3),np.eye(3),.006,.004)
        np.testing.assert_allclose(c.local[:,0],0.)
        c.update(p,v,np.zeros(3),np.eye(3),.02,.004)
        self.assertFalse(len(c.indices))

    def test_folded_cloth_capture_and_opening_hysteresis(self):
        p=self.patch(); c=Pinch(); v=np.zeros_like(p)
        c.update(p,v,np.zeros(3),np.eye(3),.011,.004)
        self.assertEqual(len(c.indices),9)
        c.update(p,v,np.zeros(3),np.eye(3),.015,.004)
        self.assertEqual(len(c.indices),9)
        c.update(p,v,np.zeros(3),np.eye(3),.017,.004)
        self.assertFalse(len(c.indices))
        c.update(p,v,np.zeros(3),np.eye(3),.013,.004)
        self.assertFalse(len(c.indices))

    def test_open_or_missed_grasp_cannot_attach(self):
        for tcp,gap in ((np.zeros(3),.02),(np.array([.02,0,0]),.002)):
            p=self.patch(); before=p.copy(); c=Pinch()
            c.update(p,np.zeros_like(p),tcp,np.eye(3),gap,.004)
            self.assertFalse(len(c.indices)); np.testing.assert_array_equal(p,before)

    def test_open_releases_and_large_jump_slips(self):
        p=self.patch(); c=Pinch(); v=np.zeros_like(p)
        c.update(p,v,np.zeros(3),np.eye(3),.002,.004)
        c.update(p,v,np.zeros(3),np.eye(3),.02,.004)
        self.assertFalse(len(c.indices))
        c.update(p,v,np.zeros(3),np.eye(3),.002,.004)
        c.update(p,v,np.array([0,0,.03]),np.eye(3),.002,.004)
        self.assertFalse(len(c.indices)); self.assertTrue(c.blocked_until_open)
        c.update(p,v,np.zeros(3),np.eye(3),.002,.004)
        self.assertFalse(len(c.indices))


if __name__=='__main__': unittest.main()
