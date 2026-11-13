import unittest
import numpy as np
from contact_audit import ThreadClothAudit
from contact_history import ContactHistory
from tool_geometry import blade_edge_samples,BLADE_SIZE,METAL_PARTS,HANDLE_SIZE,GUARDS


class DiagnosticHistoryTests(unittest.TestCase):
    def test_contact_recovery_does_not_clear_independent_validity_guard(self):
        points=np.array(((0.,0.,0.),(1.,0.,0.),(0.,1.,0.)))
        faces=np.array(((0,1,2),));guard=ThreadClothAudit(faces)
        history=ContactHistory(faces,.01,.001)
        crossing=np.array([[[.002,.2,-.1],[.002,.2,.1]]])
        clear=np.array([[[-.02,.2,-.1],[-.02,.2,.1]]])
        for step,segments in enumerate((crossing,crossing,clear)):
            guard.update(points,segments,step*.001)
            history.update(points,segments,step*.001)
        self.assertFalse(guard.summary()['valid'])
        run=history.summary()['static_intersection_intervals'][0]
        self.assertEqual(run['sample_count'],2)
        self.assertEqual(run['sampled_duration_s'],.002)
        self.assertTrue(run['recovered_before_end'])
        self.assertEqual(history.rows[-1]['static_intersections'],0)
        np.testing.assert_allclose(history.rows[0]['static_details'][0]
            ['axis_endpoints_signed_distance_to_triangle_plane_m'],[-.1,.1])

    def test_active_interval_at_trial_end_is_not_reported_recovered(self):
        points=np.array(((0.,0.,0.),(1.,0.,0.),(0.,1.,0.)))
        history=ContactHistory(np.array(((0,1,2),)),.01,.001)
        history.update(points,np.array([[[.2,.2,-.1],[.2,.2,.1]]]),.001)
        self.assertFalse(history.summary()['static_intersection_intervals'][0]['recovered_before_end'])

    def test_vertical_blade_audit_matches_tool_and_fork_fits_handle_height(self):
        edge=blade_edge_samples()
        np.testing.assert_allclose(edge[:,0],BLADE_SIZE[0]/2)
        np.testing.assert_allclose(edge[:,1],0.)
        self.assertAlmostEqual(np.ptp(edge[:,2]),BLADE_SIZE[2])
        self.assertTrue(all(abs(z)+r<HANDLE_SIZE[2]/2 for _,_,z,r in GUARDS))
        # The handle, shank and fork root overlap rather than floating apart.
        shank,root=METAL_PARTS
        self.assertLess(shank[2][0]-shank[1][0]/2,HANDLE_SIZE[0]/2)
        self.assertGreater(shank[2][0]+shank[1][0]/2,root[2][0]-root[1][0]/2)


if __name__=='__main__':unittest.main()
