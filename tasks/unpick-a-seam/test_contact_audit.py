import unittest
import numpy as np
from contact_audit import ThreadClothAudit,capsule_endpoints


class ContactAuditTests(unittest.TestCase):
    def setUp(self):
        self.triangle=np.array(((0.,0.,0.),(1.,0.,0.),(0.,1.,0.)))
        self.faces=np.array(((0,1,2),))

    def test_intersection_rejected_but_passage_outside_fabric_allowed(self):
        a=ThreadClothAudit(self.faces)
        self.assertTrue(a.update(self.triangle,np.array([[[2.,2.,-.1],[2.,2.,.1]]]),0.))
        self.assertFalse(a.update(self.triangle,np.array([[[.2,.2,-.1],[.2,.2,.1]]]),.01))
        self.assertFalse(a.update(self.triangle,np.array([[[2.,2.,-.1],[2.,2.,.1]]]),.02))

    def test_translation_tunnelling_detected(self):
        a=ThreadClothAudit(self.faces)
        thread=np.array([[[.2,.2,.1],[.3,.2,.1]]])
        self.assertTrue(a.update(self.triangle,thread,0.))
        self.assertFalse(a.update(self.triangle+[0.,0.,.2],thread,.01))

    def test_joint_rigid_motion_does_not_create_crossing(self):
        a=ThreadClothAudit(self.faces)
        thread=np.array([[[.2,.2,.1],[.3,.2,.1]]])
        self.assertTrue(a.update(self.triangle,thread,0.))
        self.assertTrue(a.update(self.triangle+[0.,0.,.2],thread+[0.,0.,.2],.01))

    def test_capsule_rotation(self):
        poses=np.array([[1.,2.,3.,0.,0.,np.sin(np.pi/4),np.cos(np.pi/4)]])
        endpoints=capsule_endpoints(poses,[.2])
        np.testing.assert_allclose(endpoints,[[[1.,1.9,3.],[1.,2.1,3.]]])

    def test_last_partial_broadphase_group_keeps_a_collision(self):
        a=ThreadClothAudit(self.faces)
        threads=np.tile(np.array([[[2.,2.,-.1],[2.,2.,.1]]]),(57,1,1))
        threads[-1]=[[.2,.2,-.1],[.2,.2,.1]]
        self.assertFalse(a.update(self.triangle,threads,0.))


if __name__=='__main__':unittest.main()
