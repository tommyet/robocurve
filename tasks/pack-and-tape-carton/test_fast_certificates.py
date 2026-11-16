"""Early SAT acceptance must preserve rejection and every collision body."""
import unittest,math,json
from pathlib import Path
from unittest.mock import patch
import numpy as np
from roll_probe import box_gap,Geometry
from yam_arena.urdf import quat_xyzw_to_matrix
class PrimitiveTests(unittest.TestCase):
 def test_edge_cross_axis_still_runs_when_box_axes_cannot_certify(self):
  tri=np.array([[[.99,1.1,0],[1.1,.99,0],[1.1,1.1,0]]]);p=np.zeros(3);R=np.eye(3)
  with patch('roll_probe.np.cross',wraps=np.cross)as cross:
   value=box_gap(tri,p,R,[2,2,2],accept_gap=.0002);self.assertGreater(cross.call_count,0)
  self.assertGreater(value,.0002);self.assertEqual(value,box_gap(tri,p,R,[2,2,2]))
 def test_threshold_neighbours_for_positive_and_negative_acceptance(self):
  tri=np.array([[[0,-.1,-.1],[0,.1,-.1],[0,0,.1]]])
  for threshold in [-.001,.0002]:
   for offset in [-1e-8,0,1e-8]:
    p=np.array([.005+threshold+offset,0,0]);full=box_gap(tri,p,np.eye(3),[.01]*3);fast=box_gap(tri,p,np.eye(3),[.01]*3,accept_gap=threshold)
    self.assertEqual(fast>=threshold,full>=threshold);self.assertLessEqual(fast,full+1e-12)
 def test_passing_certificate_skips_axes_but_does_not_early_reject(self):
  tri=np.array([[[0,-.1,-.1],[0,.1,-.1],[0,0,.1]]]);p=np.array([.0045,0,0])
  with patch('roll_probe.np.cross',wraps=np.cross)as cross:
   gap=box_gap(tri,p,np.eye(3),[.01]*3,accept_gap=-.001);self.assertEqual(cross.call_count,0)
  self.assertGreaterEqual(gap,-.001)
  with patch('roll_probe.np.cross',wraps=np.cross)as cross:
   gap=box_gap(tri,p,np.eye(3),[.01]*3,accept_gap=.0002);self.assertGreater(cross.call_count,0)
  self.assertLess(gap,.0002)
 def test_randomized_poses_preserve_classification_and_conservative_bound(self):
  rng=np.random.default_rng(403)
  for _ in range(160):
   tri=rng.normal(size=(4,3,3))*.02;p=rng.normal(size=3)*.025;R,_=np.linalg.qr(rng.normal(size=(3,3)));size=rng.uniform(.005,.04,3);full=box_gap(tri,p,R,size)
   for threshold in [-.001,.0002]:
    fast=box_gap(tri,p,R,size,accept_gap=threshold);self.assertEqual(fast>=threshold,full>=threshold);self.assertLessEqual(fast,full+1e-12)
 def test_nonfinite_acceptance_threshold_fails_closed(self):
  for value in [float('nan'),float('inf'),-float('inf')]:
   with self.assertRaises(ValueError):box_gap(np.zeros((1,3,3)),np.zeros(3),np.eye(3),[1]*3,accept_gap=value)
class NativeGuardTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from test_closure_advance import FIXTURE
  cls.fixture=FIXTURE;cls.full=Geometry();cls.fast=Geometry(fast_certificates=True)
 def inputs(self):
  f=self.fixture;poses={n:(np.asarray(v[:3]),quat_xyzw_to_matrix(v[3:]))for n,v in f['native_poses'].items()}
  return [np.asarray(h['joints'])for h in f['native_hands']],[np.asarray(h['finger_joints'])for h in f['native_hands']],poses
 def compare(self,qs,fs,poses,**kw):
  full=self.full.check(qs,fs,poses,**kw);fast=self.fast.check(qs,fs,poses,**kw)
  self.assertEqual(fast['safe'],full['safe']);self.assertLessEqual(fast['hard_gap_m'],full['hard_gap_m']+1e-12);self.assertLessEqual(fast['target_gap_m'],full['target_gap_m']+1e-12);self.assertEqual(fast['other_arm_gap_m'],full['other_arm_gap_m']);self.assertIn('Conservative',fast['gap_reporting']);return full,fast
 def test_actual_and_issued_native_states_keep_pair_specific_masks(self):
  qs,fs,poses=self.inputs()
  for side in [0,1]:self.compare(qs,fs,poses,contact=True,contact_targets={'east_top'},contact_side=side)
  self.compare(qs,fs,poses,contact=False)
  q=np.asarray(self.fixture['previous_action']);self.compare([q[:6],q[7:13]],[[q[6]*-.04695]*2,[q[13]*-.04695]*2],poses,contact=True,contact_targets={'east_top'},contact_side=0)
 def test_changed_unrelated_pose_is_never_reused(self):
  qs,fs,poses=self.inputs();before,_=self.compare(qs,fs,poses,contact=True,contact_targets={'east_top'},contact_side=0);self.assertTrue(before['safe'])
  from yam_arena import ik
  poses['cutter']=(ik.tcp_pose(qs[0],np.array([0.,.305,.75]))[0],np.eye(3))
  after,_=self.compare(qs,fs,poses,contact=True,contact_targets={'east_top'},contact_side=0);self.assertFalse(after['safe'])

if __name__=='__main__':unittest.main()
