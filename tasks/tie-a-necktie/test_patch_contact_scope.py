import unittest
import numpy as np
from adult_knot import classify_patch_contacts


class PatchContactScopeTests(unittest.TestCase):
    def check_contact(self,material,link='tip_right',step=109):
        rest=np.array([[0.,s,0.] for s in material]);faces=np.array([[0,1,2]])
        return classify_patch_contacts([dict(step=step,hits=[dict(link=link,faces=[0])])],
            rest,faces,longitudinal=.20,patch_half_width=.065)

    def test_adjacent_same_strip_contact_is_disclosed_during_insertion(self):
        blocked,intended=self.check_contact([.245,.255,.260])
        self.assertFalse(blocked);self.assertEqual(len(intended),1)

    def test_narrow_tail_and_early_or_palm_contact_remain_blocked(self):
        for values in ([1.24,1.25,1.26],[.26,.27,.28]):
            self.assertTrue(self.check_contact(values)[0])
        self.assertTrue(self.check_contact([.19,.20,.21],step=50)[0])
        self.assertTrue(self.check_contact([.19,.20,.21],link='gripper')[0])

    def test_allowance_cannot_expand_to_an_entire_strand(self):
        with self.assertRaises(ValueError):
            classify_patch_contacts([],np.empty((0,3)),np.empty((0,3),int),
                longitudinal=.20,patch_half_width=.3)
