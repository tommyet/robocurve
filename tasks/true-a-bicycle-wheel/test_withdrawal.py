import unittest
import numpy as np
from withdrawal import axial_target
from wheel_scene import spoke_phase


class WithdrawalTests(unittest.TestCase):
    def test_nipple_moves_outward_in_tool_coordinates_without_twist(self):
        R=spoke_phase(.63);p=np.array((.31,.12,.95));nipple=p+R@np.array((0.,0.,.001))
        moved,rotation=axial_target(p,R,.016)
        np.testing.assert_allclose((nipple-moved)@rotation,(0.,.016,.001),atol=1e-12)
        np.testing.assert_array_equal(rotation,R)

    def test_rigid_world_transform_preserves_path(self):
        R=spoke_phase(.63);C=spoke_phase(-.4);p=np.array((.3,.1,.9));shift=np.array((.1,-.2,.05))
        a,_=axial_target(p,R,.02);b,_=axial_target(C@p+shift,C@R,.02)
        np.testing.assert_allclose(b,C@a+shift,atol=1e-12)

    def test_invalid_and_unbounded_targets_fail(self):
        for d in (-.001,.051,float('nan')):
            with self.assertRaises(ValueError):axial_target(np.zeros(3),np.eye(3),d)
        with self.assertRaises(ValueError):axial_target(np.zeros(3),np.eye(3)*2,.01)
