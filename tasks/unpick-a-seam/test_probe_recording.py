import unittest
import numpy as np
from probe_facets import native_snapshot


class ProbeRecordingTests(unittest.TestCase):
    def test_thread_and_panels_remain_distinct_owned_snapshots(self):
        panels=[np.ones((118,7)),np.full((118,7),2.)]
        threads=np.full((168,7),3.);lengths=np.full(168,.001)
        snap=native_snapshot(12,960,panels,threads,lengths)
        self.assertEqual(snap['thread'].shape,(168,7))
        self.assertEqual(snap['facet_poses_1'].shape,(118,7))
        threads[:]=4.;panels[1][:]=5.
        np.testing.assert_array_equal(snap['thread'],3.)
        np.testing.assert_array_equal(snap['facet_poses_1'],2.)
        with self.assertRaisesRegex(ValueError,'body count'):
            native_snapshot(12,960,panels,panels[1],lengths)


if __name__=='__main__':unittest.main()
