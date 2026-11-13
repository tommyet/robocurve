import unittest
import numpy as np
from integrity import rim_strain,RimDomainGuard
from thread_coupling import rotation


def circle():
    angle=np.arange(32)*2*np.pi/32
    vertices=np.column_stack((.21*np.cos(angle),.21*np.sin(angle),np.zeros(32)))
    centres=(vertices+np.roll(vertices,-1,axis=0))/2
    yaw=angle+np.pi/32+np.pi/2
    matrices=np.array([rotation((0.,0.,np.sin(v/2),np.cos(v/2))) for v in yaw])
    return centres,matrices


class IntegrityTests(unittest.TestCase):
    def test_rigid_world_motion_does_not_create_material_strain(self):
        p,R=circle();world=rotation((.2,-.3,.1,.8));offset=np.array((2.,-.6,.7))
        initial=rim_strain(p,R);moved=rim_strain(p@world.T+offset,world@R)
        self.assertLess(initial['maximum_axial_bending_strain'],1e-12)
        self.assertLess(moved['maximum_axial_bending_strain'],1e-12)
        self.assertLess(moved['maximum_locked_joint_gap_m'],1e-12)

    def test_failed_domain_does_not_recover_after_restoring_a_round_shape(self):
        p,R=circle();bad=p.copy();bad[0,2]+=.002
        guard=RimDomainGuard()
        self.assertTrue(guard.update(p,R)['valid'])
        self.assertFalse(guard.update(bad,R)['valid'])
        restored=guard.update(p,R)
        self.assertFalse(restored['valid']);self.assertEqual(restored['first_failure']['step'],2)


if __name__=='__main__':unittest.main()
