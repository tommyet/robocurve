import unittest
import numpy as np
from paper import perforated_sheet
from contact_guard import PaperWireCrossingGuard


class CrossingTests(unittest.TestCase):
    def test_withdrawal_through_authored_hole_is_valid(self):
        mesh=perforated_sheet();guard=PaperWireCrossingGuard(mesh.faces)
        wire=np.array([[[-.0064,0.,-.001],[-.0064,0.,.001]]])
        self.assertTrue(guard.update(mesh.rest,wire)['valid'])
        self.assertTrue(guard.update(mesh.rest,wire+[0,0,.004])['valid'])

    def test_wire_through_untorn_sheet_is_invalid_and_latched(self):
        mesh=perforated_sheet();guard=PaperWireCrossingGuard(mesh.faces)
        wire=np.array([[[.001,.001,-.001],[.001,.001,.001]]])
        self.assertFalse(guard.update(mesh.rest,wire)['valid'])
        self.assertFalse(guard.update(mesh.rest,wire+[0,0,.004])['valid'])

    def test_fast_wire_jump_through_paper_is_detected(self):
        mesh=perforated_sheet();guard=PaperWireCrossingGuard(mesh.faces)
        wire=np.array([[[.001,.001,.001],[.002,.001,.001]]])
        self.assertTrue(guard.update(mesh.rest,wire)['valid'])
        self.assertFalse(guard.update(mesh.rest,wire-[0,0,.002])['valid'])

    def test_sheet_cannot_fall_through_stationary_clinch(self):
        mesh=perforated_sheet();guard=PaperWireCrossingGuard(mesh.faces)
        wire=np.array([[[.001,.001,-.001],[.002,.001,-.001]]])
        self.assertTrue(guard.update(mesh.rest,wire)['valid'])
        self.assertFalse(guard.update(mesh.rest-[0,0,.002],wire)['valid'])

    def test_common_rigid_translation_is_not_tunnelling(self):
        mesh=perforated_sheet();guard=PaperWireCrossingGuard(mesh.faces)
        wire=np.array([[[.001,.001,.001],[.002,.001,.001]]])
        self.assertTrue(guard.update(mesh.rest,wire)['valid'])
        self.assertTrue(guard.update(mesh.rest+[.1,.2,.3],wire+[.1,.2,.3])['valid'])


if __name__=='__main__':unittest.main()
