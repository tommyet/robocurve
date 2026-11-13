import unittest
import numpy as np
from thread_integrity import ThreadIntegrity,ClosedJunctionCrossings
from contact_audit import ThreadClothAudit


class ThreadIntegrityTests(unittest.TestCase):
    def test_wraps_each_loop_and_omits_only_severed_joint(self):
        e=np.arange(36,dtype=float).reshape(6,2,3)*1e-5
        audit=ThreadIntegrity((3,3),.0004);connectors=audit.update(e,{1},0.)
        np.testing.assert_array_equal(connectors[:,0],e[[2,0,1,5,3,4],1])
        np.testing.assert_array_equal(connectors[[0,2,3,4,5],1],e[[0,2,3,4,5],0])
        np.testing.assert_array_equal(connectors[1,0],connectors[1,1])

    def test_disjoint_closed_endcaps_latch_without_calling_it_a_cut(self):
        points=np.array([[0.,0.,0.],[.001,0.,0.],[.001,.001,0.]])
        ends=np.stack((points,np.roll(points,-1,axis=0)),axis=1)
        audit=ThreadIntegrity((3,),.0004);audit.update(ends,set(),0.)
        moved=ends.copy();moved[1,0,2]+=.00081
        audit.update(moved,set(),.1);self.assertFalse(audit.summary()['valid'])
        self.assertEqual(audit.first_failure['joint'],1)
        audit.update(ends,set(),.2);self.assertFalse(audit.summary()['valid'])
        allowed=ThreadIntegrity((3,),.0004);allowed.update(moved,{1},.1)
        self.assertTrue(allowed.summary()['valid'])

    def test_connector_catches_crossing_between_capsule_endpoints(self):
        # Two adjacent measured axes stop on opposite sides of a face. Their
        # short native-joint connector still crosses the intact surface.
        ends=np.array([[[0.,0.,.0001],[0.,0.,.0002]],
                       [[0.,0.,-.0002],[0.,0.,-.0001]],
                       [[.002,0.,-.0001],[.002,0.,.0001]]])
        triangle=np.array([[-.001,-.001,0.],[.001,-.001,0.],[0.,.001,0.]])
        junctions=ThreadIntegrity((3,),.0004).update(ends,set(),0.)
        bare=ThreadClothAudit([[0,1,2]]);bare.update(triangle,ends,0.)
        joined=ThreadClothAudit([[0,1,2]]);joined.update(triangle,junctions,0.)
        self.assertIsNone(bare.first_failure)
        self.assertIsNotNone(joined.first_failure)

    def test_cut_drops_only_its_own_sweep_history(self):
        triangle=np.array([[-1.,-1.,0.],[1.,-1.,0.],[0.,1.,0.]])
        first=np.array([[[2.,0.,-.1],[2.1,0.,-.1]],
                        [[0.,0.,-.1],[.1,0.,-.1]],
                        [[.2,0.,-.1],[.3,0.,-.1]]])
        for move_remaining in (False,True):
            audit=ClosedJunctionCrossings([[[0,1,2]]],3)
            self.assertFalse(audit.update([triangle],first,set(),0.))
            current=first.copy();current[1,:,2]=.1
            if move_remaining:current[2,:,2]=.1
            self.assertEqual(audit.update([triangle],current,{1},.1),move_remaining)
            np.testing.assert_array_equal(audit.audits[0].previous,current[[0,2]])
            if move_remaining:
                self.assertEqual(audit.audits[0].first_failure['joint_indices_in_segment_order'],[0,2])
                self.assertTrue(audit.update([triangle],current,{1,2},.2))


if __name__=='__main__':unittest.main()
