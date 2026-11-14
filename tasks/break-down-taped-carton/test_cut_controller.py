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
