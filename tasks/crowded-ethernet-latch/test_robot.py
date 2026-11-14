"""CPU controller invariants; these tests cannot establish a native grasp."""
from pathlib import Path
import json
from types import SimpleNamespace
import unittest
import numpy as np
from yam_arena import ik
from yam_arena.constants import READY,FINGER_OPEN
from robot import GraspProbe,ReleaseProbe,R_GRIP,BOOT_LOCAL,ENTRY_GRIP,PRESS_GRIP,GRIP,GRIP_OPENING
from config import port,SERVICE,TARGET,CLIP_Z,RELEASE_TRAVEL

class Array:
 def __init__(self,value):self.value=np.array(value,dtype=float)
 def detach(self):return self
 def cpu(self):return self
 def numpy(self):return self.value

def environment():
 ready=np.array(READY+[1.]+READY+[1.])
 joints=Array([READY+[FINGER_OPEN,FINGER_OPEN]])
 scene={s+'_robot':SimpleNamespace(data=SimpleNamespace(joint_pos=joints)) for s in ('left','right')}
 def pose(name):
  p=np.array(port(SERVICE))
  if name.startswith('clip'):p=p+[0,0,CLIP_Z]
  return Array([[*p,0,0,0,1]])
 return SimpleNamespace(_base=SimpleNamespace(scene=scene,arena_world=SimpleNamespace(get_pose_w=pose)),
                        _ready=Array(ready),_ids={s+'_robot':(list(range(6)),[6,7]) for s in ('left','right')},
                        rig=SimpleNamespace(bases={'left':(0,.305,.75),'right':(0,-.305,.75)}),
                        _low=np.full(14,-10.),_high=np.full(14,10.))

class RobotTests(unittest.TestCase):
 def test_boot_grasp_commands_left_arm_and_gripper(self):
  env=environment();probe=GraspProbe(env,np.array(port(SERVICE)))
  probe.phase='enter_boot'
  output,report=probe.command(1.5)
  self.assertTrue(np.array_equal(output[7:13],np.array(READY)))
  self.assertFalse(np.array_equal(output[:6],np.array(READY)))
  self.assertLess(output[6],1.)
  self.assertEqual(output[13],1.)
  self.assertAlmostEqual(report['left_target'][0],port(SERVICE)[0]+BOOT_LOCAL[0]-.020)

 def test_press_commands_right_tip_left_finger(self):
  env=environment();probe=ReleaseProbe(env,np.array(port(SERVICE)));probe.phase='depress_clip'
  output,report=probe.command(9.)
  self.assertFalse(np.array_equal(output[7:13],np.array(READY)))
  self.assertLess(output[13],1.)
  self.assertEqual(report['phase'],'depress_clip')
  self.assertEqual(len(report['arms'][1]['actual_finger_joints_m']),2)

 def test_withdrawal_pauses_when_measured_clip_returns(self):
  probe=ReleaseProbe(environment(),np.array(port(SERVICE)))
  probe.phase='withdraw_with_clip_pressed';probe.withdraw_start=probe.boot_goal.copy();probe.press_depth=.0019
  measured=[probe.arm(s) for s in ('left','right')]
  plug=np.array([*port(SERVICE),0,0,0,1.]);rotation=np.eye(3)
  targets=(probe.boot_goal,R_GRIP,.03,measured[1][2],measured[1][3],PRESS_GRIP)
  result=probe.release_targets(2.,2.,probe.phase,plug,rotation,RELEASE_TRAVEL-.0004,measured,targets)
  self.assertEqual(probe.pull_distance,0.)
  self.assertAlmostEqual(result[0][0],probe.boot_goal[0])
  result=probe.release_targets(2.05,2.05,probe.phase,plug,rotation,RELEASE_TRAVEL,measured,targets)
  self.assertGreater(probe.pull_distance,0.)
  self.assertLess(result[0][0],probe.boot_goal[0])

 def test_hook_release_and_full_tip_clearance_are_separate_measured_gates(self):
  probe=ReleaseProbe(environment(),np.array(port(SERVICE)))
  probe.phase='withdraw_with_clip_pressed';probe.withdraw_start=probe.boot_goal.copy();probe.press_depth=.0019
  measured=[probe.arm(s) for s in ('left','right')]
  targets=(probe.boot_goal,R_GRIP,.03,measured[1][2],measured[1][3],PRESS_GRIP)
  plug=np.array([*port(SERVICE),0,0,0,1.])
  probe.release_targets(2.,2.,probe.phase,plug,np.eye(3),RELEASE_TRAVEL,measured,targets)
  self.assertEqual(probe.phase,'withdraw_with_clip_pressed')
  plug[0]-=.007
  probe.release_targets(2.05,2.05,probe.phase,plug,np.eye(3),RELEASE_TRAVEL,measured,targets)
  self.assertEqual(probe.phase,'lift_press_finger')
  self.assertFalse(probe.source_clear)
  probe.phase='finish_withdrawal'
  probe.release_targets(4.,1.,probe.phase,plug,np.eye(3),0.,measured,targets)
  self.assertEqual(probe.phase,'finish_withdrawal')
  plug[0]-=.018
  probe.release_targets(4.05,1.05,probe.phase,plug,np.eye(3),0.,measured,targets)
  self.assertEqual(probe.phase,'clear_press_finger')
  self.assertTrue(probe.source_clear)

 def test_certified_waypoints_have_continuous_reachable_ik(self):
  spec=json.loads(Path(__file__).with_name('press_point.json').read_text())
  rotation=np.array(spec['rotation']);point=np.array(spec['point_tcp'])
  plug=np.array(port(SERVICE));above=plug+[-.010,0,.0086]-rotation@point
  q=np.array(READY)
  for offset in ((-.040,0,.025),(-.040,0,0),(0,0,0),(0,0,-.006),(-.025,0,-.006),(-.105,0,.044)):
   q,error,angle=ik.solve(above+offset,ik.matrix_to_quat_xyzw(rotation),q,base_pos=(0,-.305,.75),iters=300)
   self.assertLess(error,.0001)
   self.assertLess(angle,.001)

class BimanualGeometryTests(unittest.TestCase):
 def test_loaded_hands_have_separating_planes_for_entire_press_stroke(self):
  from collision_geometry import FingerGeometry,minimum_separation
  spec=json.loads(Path(__file__).with_name('press_point.json').read_text())
  rotation,point=np.array(spec['rotation']),np.array(spec['point_tcp']);geometry=FingerGeometry()
  sweep=[np.concatenate([(a-point)@rotation.T+[-.010,0,z] for z in (.0022,.0086)])
         for _,a in geometry.pieces([-.028,-.028])]
  for jaw in (-.0035,-.0038,-.0045,-.005):
   left=[a@R_GRIP.T+BOOT_LOCAL for _,a in geometry.pieces([jaw,jaw])]
   self.assertGreater(minimum_separation(left,sweep),0.)

 def test_press_finger_lifts_before_crossing_boot(self):
  from collision_geometry import FingerGeometry,minimum_separation
  spec=json.loads(Path(__file__).with_name('press_point.json').read_text())
  rotation,point=np.array(spec['rotation']),np.array(spec['point_tcp']);geometry=FingerGeometry()
  left=[a@R_GRIP.T+BOOT_LOCAL for _,a in geometry.pieces([-.0038,-.0038])]
  def translated_sweep(start,delta):
   return [np.concatenate([(a-point)@rotation.T+start+fraction*np.array(delta) for fraction in (0.,1.)])
           for _,a in geometry.pieces([-.028,-.028])]
  contact=np.array((-.010,0,.0022))
  # The earlier, more forward grasp made direct diagonal retreat unsafe.
  old_left=[a@R_GRIP.T+[-.0265,.0005,-.0005] for _,a in geometry.pieces([-.0038,-.0038])]
  self.assertEqual(minimum_separation(old_left,translated_sweep(contact,(-.080,0,.050))),0.)
  self.assertGreater(minimum_separation(left,translated_sweep(contact,(0,0,.020))),.0002)
  self.assertGreater(minimum_separation(left,translated_sweep(contact+[0,0,.020],(-.080,0,.030))),.003)


class EntryEndpointTests(unittest.TestCase):
 def test_endpoint_reference_stays_fixed_while_joint_feedback_rejects_contact_load(self):
  from unittest.mock import patch
  probe=GraspProbe(environment(),np.array(port(SERVICE)))
  probe.bias[0][:]=.001
  probe.transition('enter_boot',0.)
  np.testing.assert_array_equal(probe.bias[0],np.zeros(3))
  goal=np.array(port(SERVICE))+BOOT_LOCAL
  measured=[probe.arm(side) for side in ('left','right')]
  left=(measured[0][0],np.array((-.0065,-.0065)),goal-np.array((.0008,0,0)),R_GRIP)
  probe.arm=lambda side:left if side=='left' else measured[1]
  safe={'rigid_gap_m':.002,'wire_gap_m':.001,'minimum_gap_m':.001}
  with patch('robot.clearance',return_value=safe),patch('robot.snapshot',return_value=({},{},{})),patch.object(probe,'stationary_hold_safety',return_value={'rigid_gap_m':.002,'other_hand_gap_m':.002}):
   probe.command(2.9)
   np.testing.assert_array_equal(probe.bias[0],np.zeros(3))
   for time in (3.05,3.10,3.15):probe.command(time)
   self.assertIsNotNone(probe.entry_joint_servo.reference)
   self.assertGreater(np.linalg.norm(probe.entry_joint_servo.bias),0.)
   np.testing.assert_array_equal(probe.bias[0],np.zeros(3))
   self.assertEqual(probe.phase,'enter_boot')
   learned=probe.entry_joint_servo.bias.copy();reference=probe.entry_joint_servo.reference.copy()
   probe.transition('close_on_boot',3.2);probe.command(3.25)
   self.assertGreater(np.linalg.norm(probe.entry_joint_servo.bias-learned),0.)
   np.testing.assert_array_equal(probe.entry_joint_servo.reference,reference)
   self.assertFalse(probe.entry_joint_servo.frozen)

class ReleaseGeometryGateTests(unittest.TestCase):
 def make_state(self,phase):
  probe=ReleaseProbe(environment(),np.array(port(SERVICE)));probe.phase=phase
  measured=[probe.arm(side) for side in ('left','right')]
  probe.right_clear=(measured[1][2].copy(),measured[1][3].copy())
  probe.align_plug_start=probe.target_origin+np.array((-.038,0,0));probe.align_body_start=np.eye(3)
  probe.insertion_x=float(probe.align_plug_start[0]);probe.frozen_alignment_rotation=np.eye(3)
  targets=(measured[0][2],measured[0][3],0.,measured[1][2],measured[1][3],PRESS_GRIP)
  return probe,measured,targets

 def test_negative_x_alignment_bias_cannot_deadlock_actual_insertion_progress(self):
  probe,measured,targets=self.make_state('insert_empty_target')
  probe.alignment_bias[0]=-.001
  plug=np.r_[probe.align_plug_start+[-.001,0,0],0,0,0,1.]
  before=probe.insertion_x
  probe.release_targets(1.,1.,probe.phase,plug,np.eye(3),0.,measured,targets)
  self.assertGreater(probe.insertion_x,before)

 def test_bad_actual_guide_footprint_blocks_entry_even_with_a_good_tcp(self):
  probe,measured,targets=self.make_state('align_empty_target')
  plug=np.r_[probe.align_plug_start+[0,0,.00025],0,0,0,1.]
  for i in range(8):probe.release_targets(3+i*.05,3+i*.05,probe.phase,plug,np.eye(3),0.,measured,targets)
  self.assertEqual(probe.phase,'align_empty_target')
  self.assertLess(probe.guide_geometry['minimum_clearance_m'],.0001)

 def test_partial_jaws_do_not_fully_open_without_all_wire_clearance(self):
  from unittest.mock import patch
  probe,measured,targets=self.make_state('certify_open_clearance')
  plug=np.r_[port(TARGET),0,0,0,1.]
  blocked={'rigid_gap_m':.010,'wire_gap_m':0.,'minimum_gap_m':0.}
  with patch('robot.snapshot',return_value=({},{},{})),patch('robot.clearance',return_value=blocked):
   result=probe.release_targets(1.,1.,probe.phase,plug,np.eye(3),0.,measured,targets)
  self.assertEqual(result[2],ENTRY_GRIP)
  self.assertNotEqual(probe.phase,'open_clear_hands')
  self.assertIsNotNone(probe.failure)

 def test_full_opening_requires_complete_sweep_clearance(self):
  from unittest.mock import patch
  probe,measured,targets=self.make_state('certify_open_clearance')
  plug=np.r_[port(TARGET),0,0,0,1.]
  clear={'rigid_gap_m':.020,'wire_gap_m':.010,'minimum_gap_m':.010}
  with patch('robot.snapshot',return_value=({},{},{})),patch('robot.clearance',return_value=clear),patch('robot.minimum_separation',return_value=.020):
   result=probe.release_targets(1.,1.,probe.phase,plug,np.eye(3),0.,measured,targets)
  self.assertEqual(probe.phase,'open_clear_hands')
  self.assertEqual(result[2],ENTRY_GRIP)


class HoldPreloadTests(unittest.TestCase):
 def test_measured_preload_command_persists_in_hold_and_clip_operation(self):
  for cls,phase in ((GraspProbe,'verified_boot_hold'),(ReleaseProbe,'depress_clip')):
   probe=cls(environment(),np.array(port(SERVICE)));probe.phase=phase;probe.previous[6]=GRIP
   action,report=probe.command(1.)
   self.assertAlmostEqual(action[6],GRIP)
   self.assertAlmostEqual(report['hold_command_opening_m'],GRIP_OPENING)
