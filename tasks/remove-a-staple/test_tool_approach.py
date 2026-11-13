import unittest
import numpy as np
from plan_reach import insertion_pitch,heel_supported_pose,tool_frame,heel_contact_height
from full_scene import STAPLE_XY,scene_layout
import itertools


class ToolApproachTests(unittest.TestCase):
    def test_heel_contact_and_tip_crown_alignment(self):
        corners=np.array(list(itertools.product((-.0075,.0075),(-.007,-.001),(-.003,.003))))
        for profile in ('floating-reference','supported-edge-candidate','pocket-support-candidate'):
            pitch=insertion_pitch(profile);R=tool_frame(pitch);root=heel_supported_pose(pitch,profile)
            heel=corners@R.T+root
            tip=root+R@np.array((0.,.025,.00005))
            self.assertAlmostEqual(heel[:,2].min(),heel_contact_height(profile),places=12)
            self.assertAlmostEqual(tip[0],STAPLE_XY[0],places=12)
            self.assertAlmostEqual(tip[2],scene_layout(profile)['crown_underside_z']-.000002,places=12)
            self.assertLess(pitch,0.)

    def test_all_heel_corners_clear_paper_through_lever_arc(self):
        corners=np.array(list(itertools.product((-.0075,.0075),(-.007,-.001),(-.003,.003))))
        for pitch in np.linspace(insertion_pitch('pocket-support-candidate'),0.,21):
            heel=corners@tool_frame(pitch).T+heel_supported_pose(pitch)
            self.assertAlmostEqual(heel[:,2].min(),heel_contact_height(),places=12)
