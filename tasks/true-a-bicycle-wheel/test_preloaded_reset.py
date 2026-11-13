import unittest
import numpy as np
from integrity import rim_strain
from preloaded_reset import load_configuration
from thread_coupling import rotation_batch


class PreloadedResetTests(unittest.TestCase):
    def test_complete_loaded_shape_has_visible_wobble_and_valid_rim(self):
        data,digest=load_configuration()
        self.assertEqual(len(set(r['body'] for r in data['bodies'])),129)
        self.assertEqual(len(digest),64)
        rows=sorted((r for r in data['bodies'] if r['body'].startswith('rim_')),key=lambda r:r['body'])
        p=np.array([r['position_in_hub_m'] for r in rows])
        R=rotation_batch(np.array([r['rotation_in_hub_xyzw'] for r in rows]))
        values=rim_strain(p,R)
        self.assertGreater(float(np.ptp(p[:,2])),.0005)
        self.assertLess(values['maximum_axial_bending_strain'],.003)
        self.assertLess(values['maximum_locked_joint_gap_m'],.0001)

    def test_preloading_does_not_repair_the_loose_nipples(self):
        data,_=load_configuration()
        turns=np.array(data['source_thread_turns'])
        self.assertAlmostEqual(turns[0],-.75,places=4)
        self.assertAlmostEqual(turns[2],-.75,places=4)
        self.assertLess(float(np.abs(np.delete(turns,[0,2])).max()),.0001)
