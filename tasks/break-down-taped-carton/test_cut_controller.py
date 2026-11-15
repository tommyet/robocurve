"""Read-only coverage planning and released-tool hand-retreat regressions."""
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from yam_arena import ik
from yam_arena.demo import grip_rotation
from yam_arena.constants import READY,FINGER_OPEN
from robot import CartonCutProbe
from model import BladeCoverage,WIDTH,HEIGHT
from config import TOP

class Array:
 def __init__(self,value):self.value=np.array(value,dtype=float)
 def detach(self):return self
 def cpu(self):return self
 def numpy(self):return self.value

class CutControllerTests(unittest.TestCase):
 def test_missing_coverage_only_inserts_physical_actions_and_is_bounded(self):
  probe=CartonCutProbe.__new__(CartonCutProbe)
  probe.index=0;probe.phases=[('return_hover',None,None)];probe.repass_round=0
  probe.cuts_verified=False;probe.failure=None;probe.seam_depth=-.000275
  coverage=BladeCoverage();task=SimpleNamespace(_tracker=SimpleNamespace(coverage=coverage))
  with patch.dict(sys.modules,{'task':task}):
   for repeat in range(3):
    probe.index=next(i for i,p in enumerate(probe.phases) if p[0]=='return_hover')
    probe.schedule_remaining_cuts()
    self.assertEqual(probe.repass_round,repeat+1)
    self.assertTrue(probe.phases[probe.index][0].startswith('repass_'))
    self.assertEqual(coverage.cut,set())
    self.assertFalse(probe.cuts_verified)
   probe.schedule_remaining_cuts()
  self.assertIn('three measured physical retraces',probe.failure)
  self.assertEqual(coverage.cut,set())

 def test_empty_kernel_is_not_mistaken_for_success(self):
  probe=CartonCutProbe.__new__(CartonCutProbe);probe.failure=None
  with patch.dict(sys.modules,{'task':SimpleNamespace(_tracker=None)}):probe.schedule_remaining_cuts()
  self.assertIn('coverage unavailable',probe.failure)

 def test_released_cutter_stays_parked_while_hand_retracts(self):
  base=(0,.305,.75)
  q,_,_=ik.solve(np.array((.13,.21,TOP+.026)),ik.matrix_to_quat_xyzw(grip_rotation()),np.array(READY),base_pos=base,iters=300)
  native=Array([[*q,FINGER_OPEN,FINGER_OPEN]])
  ready=np.r_[q,1.,READY,1.]
  env=SimpleNamespace(_ready=Array(ready),_ids={'left_robot':(list(range(6)),[6,7])},
                      _base=SimpleNamespace(scene={'left_robot':SimpleNamespace(data=SimpleNamespace(joint_pos=native))}),
                      rig=SimpleNamespace(bases={'left':base}),_low=np.full(14,-10.),_high=np.full(14,10.))
  probe=CartonCutProbe.__new__(CartonCutProbe)
  probe.env=env;probe.previous=ready.copy();probe.failure=None;probe.done=False
  probe.index=0;probe.phases=[('retreat',None,None)];probe.motion=None;probe.bias=np.zeros(3)
  probe.last_time=0.;probe.calibrated=True;probe.initial_tip_in_hand=np.zeros(3);probe.rest_time=1.95
  probe.coverage_report={};probe.repass_round=0;probe.cuts_verified=True;probe.rest_tool=None
  probe.park=SimpleNamespace(duration=0.,action7=lambda t:(np.r_[READY,1.],None))
  probe.pickup=SimpleNamespace(duration=0.)
  parked=np.array((.13,.21,TOP+.022));identity=np.eye(3)
  probe.pose=lambda name:(parked.copy(),identity.copy()) if name=='cutter' else (np.array((.27,WIDTH/2,TOP+.1+HEIGHT/2)),identity.copy())
  start=ik.tcp_pose(q,base)[0]
  for step in range(300):
   action,report=probe.command(step*.05)
   native.value[0,:6]=action[:6]
   if probe.done or probe.failure:break
  self.assertIsNone(probe.failure)
  self.assertTrue(probe.done)
  self.assertTrue(report[0]['hand_retreat'])
  self.assertGreater(ik.tcp_pose(native.value[0,:6],base)[0][2]-start[2],.075)
  np.testing.assert_allclose(probe.pose('cutter')[0],parked)

class CutHandoffRegressionTests(unittest.TestCase):
 def test_frozen007_lower_to_cut_preserves_world_bias_target_rotation_and_same_seed_ik(self):
  from feedback_geometry import blade_tcp_target,cut_entry_bias
  # Native007 lower endpoint28.35s, captured before its subsequent bias reset.
  point=np.array((.3552039120161092,.08439563500842412,.8477760605317747))
  bias=np.array((-.003,.0022331102096589265,-.00041211273765918153))
  grasp=np.array(((-.0010000767014928988,-.9999996926373426,.0000070758653124889615),
                  (-.9881483605769099,.0009892715895942026,.1534998302638446),
                  (-.15349979310875858,.00014651609364036604,-.9881486677410051)))
  offset=np.array((-.00006471925043257483,-.06386046555153711,.017945017246602635))
  rotation=np.array(((-.7088817678785438,.7053273275770655,.000011932531551042828),
                     (-.7053273276770948,-.708881767803308,-.000010389646893103713),
                     (.0000011306521826897853,-.00001578137184853684,.9999999998748348)))
  seed=np.array((-.477059543132782,2.1774799823760986,2.083102226257324,-1.414480209350586,-.14799317717552185,1.8793575763702393))
  local=np.array((.12,0,-.000275));localR=np.diag((-1.,1.,-1.))
  previous=dict(phase='seam_lower',local_endpoint=local.copy(),local_rotation=localR.copy())
  retained=cut_entry_bias(bias,previous,'seam_cut',local,localR)
  np.testing.assert_array_equal(retained,bias);self.assertFalse(np.shares_memory(retained,bias))
  old_target,oldR=blade_tcp_target(point+bias,rotation,grasp,offset)
  target,R=blade_tcp_target(point+retained,rotation,grasp,offset)
  np.testing.assert_array_equal(target,old_target);np.testing.assert_array_equal(R,oldR)
  np.testing.assert_allclose(target,(.3949816947273354,.1291973133992306,.8748987948985376),atol=2e-8,rtol=0.)
  oldq,_,_=ik.solve(old_target,ik.matrix_to_quat_xyzw(oldR),seed,base_pos=(0,.305,.75),iters=140)
  q,_,_=ik.solve(target,ik.matrix_to_quat_xyzw(R),seed,base_pos=(0,.305,.75),iters=140)
  np.testing.assert_array_equal(q,oldq)
  reset_target,_=blade_tcp_target(point,rotation,grasp,offset)
  self.assertGreater(np.linalg.norm(reset_target-target),.0037)

 def test_bias_carry_requires_same_lower_identity_local_endpoint_and_rotation(self):
  from feedback_geometry import cut_entry_bias
  bias=np.array((-.003,.002,-.0004));start=np.array((.12,0,-.000275));R=np.eye(3)
  previous=dict(phase='seam_lower',local_endpoint=start,local_rotation=R)
  for phase,endpoint,rotation in (('front_cut',start,R),('seam_cut',start+[.001,0,0],R),('seam_cut',start,np.diag((-1,-1,1)))):
   np.testing.assert_array_equal(cut_entry_bias(bias,previous,phase,endpoint,rotation),np.zeros(3))
  repass={**previous,'phase':'repass_1_seam_lower'}
  np.testing.assert_array_equal(cut_entry_bias(bias,repass,'repass_1_seam_cut',start,R),bias)
  with self.assertRaises(ValueError):cut_entry_bias([.0031,0,0],previous,'seam_cut',start,R)

 def test_cut_watchdogs_reset_only_idle_and_preserve_hard_wall_cap(self):
  from feedback_geometry import cut_watchdog
  self.assertIsNone(cut_watchdog(80.,20.))
  self.assertIn('no accepted advance',cut_watchdog(80.,20.01))
  self.assertIsNone(cut_watchdog(80.,0.)) # Actual cursor increment resets idle.
  self.assertIsNone(cut_watchdog(100.,0.))
  self.assertIn('hard cap',cut_watchdog(100.01,0.))
