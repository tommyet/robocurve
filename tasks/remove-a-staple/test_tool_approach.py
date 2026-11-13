import unittest
import numpy as np
from plan_reach import insertion_pitch,heel_supported_pose,tool_frame
from full_scene import SUPPORT_TOP,STAPLE_XY,scene_layout


class ToolApproachTests(unittest.TestCase):
    def test_heel_contact_and_tip_crown_alignment(self):
        for profile in ('floating-reference','supported-edge-candidate'):
            pitch=insertion_pitch(profile);R=tool_frame(pitch);root=heel_supported_pose(pitch)
            heel=root+R@np.array((0.,-.004,-.003))
            tip=root+R@np.array((0.,.025,.00005))
            self.assertAlmostEqual(heel[2],SUPPORT_TOP,places=12)
            self.assertAlmostEqual(tip[0],STAPLE_XY[0],places=12)
            self.assertAlmostEqual(tip[2],scene_layout(profile)['crown_underside_z']-.000002,places=12)
            self.assertLess(pitch,0.)
