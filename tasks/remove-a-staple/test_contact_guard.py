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


class SteelContinuityTests(unittest.TestCase):
    def test_actual_overlapping_boxes_do_not_count_as_a_broken_chain(self):
        from contact_guard import wire_chain_continuity
        poses=np.array([[0.,0.,0.,0.,0.,0.,1.],[.00049,0.,.00004,0.,0.,0.,1.]])
        half=np.array([.00025,0.,0.])
        segments=np.stack((poses[:,:3]-half,poses[:,:3]+half),axis=1)
        self.assertFalse(wire_chain_continuity(segments)['valid'])
        result=wire_chain_continuity(segments,poses_xyzw=poses)
        self.assertTrue(result['valid'])
        self.assertLess(result['native_box_checks'][0]['maximum_separating_axis_gap_m'],0.)

    def test_a_real_gap_is_not_excused_by_nearby_box_bounds(self):
        from contact_guard import wire_chain_continuity
        poses=np.array([[0.,0.,0.,0.,0.,0.,1.],[.00049,0.,.00031,0.,0.,0.,1.]])
        half=np.array([.00025,0.,0.]);segments=np.stack((poses[:,:3]-half,poses[:,:3]+half),axis=1)
        self.assertFalse(wire_chain_continuity(segments,poses_xyzw=poses)['valid'])
        with self.assertRaises(ValueError):
            wire_chain_continuity(segments,poses_xyzw=poses+np.array([.001,0,0,0,0,0,0]))

    def test_a_disconnected_leg_is_not_an_intact_staple(self):
        from contact_guard import wire_chain_continuity
        chain=np.array([[[0.,0.,0.],[.001,0.,0.]],[[.001,0.,0.],[.001,.001,0.]]])
        self.assertTrue(wire_chain_continuity(chain)['valid'])
        chain[1,:,2]+=.000031
        self.assertFalse(wire_chain_continuity(chain)['valid'])
