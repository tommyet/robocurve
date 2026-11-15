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
  measured={s:probe.arm(s) for s in ('left','right')}
  q,_,_,_=measured['right'];rotation=probe.pressR
  measured['right']=(q,np.array((-.028,-.028)),np.array(port(SERVICE))+probe.local_contact+[0,0,.0041]-rotation@probe.point,rotation)
  probe.arm=lambda side:measured[side]
  output,report=probe.command(9.)
  self.assertFalse(np.array_equal(output[7:13],np.array(READY)))
  self.assertLess(output[13],1.)
  self.assertEqual(report['phase'],'depress_clip')
  self.assertEqual(len(report['arms'][1]['actual_finger_joints_m']),2)

 def test_pressing_witness_outside_real_tab_does_not_advance(self):
  probe=ReleaseProbe(environment(),np.array(port(SERVICE)));probe.phase='depress_clip'
  _,report=probe.command(9.)
  self.assertEqual(report['press_depth_m'],0.)
  self.assertIn('physical clip tab footprint',report['failure'])

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
  plug=np.array(port(SERVICE));above=plug+np.array(spec['contact'])+[0,0,.0041]-rotation@point
  q=np.array(READY)
  for offset in [(-.040*(1.-s),0,.025*(1.-s)) for s in np.linspace(0.,1.,21)]+[(0,0,-.006),(-.025,0,-.006),(-.105,0,.044)]:
   q,error,angle=ik.solve(above+offset,ik.matrix_to_quat_xyzw(rotation),q,base_pos=(0,-.305,.75),iters=300)
   self.assertLess(error,.0001)
   self.assertLess(angle,.001)

class BimanualGeometryTests(unittest.TestCase):
 def test_diagonal_route_bypasses_loaded_hand(self):
  from collision_geometry import FingerGeometry,minimum_separation
  spec=json.loads(Path(__file__).with_name('press_point.json').read_text())
  rotation,point=np.array(spec['rotation']),np.array(spec['point_tcp']);geometry=FingerGeometry()
  left=[a@R_GRIP.T+BOOT_LOCAL for _,a in geometry.pieces([-.003678,-.003402])]
  def sweep(start,end):
   return [np.concatenate([(a-point)@rotation.T+position for position in (np.array(start),np.array(end))])
           for _,a in geometry.pieces([-.028,-.028])]
  above=np.array(spec['contact'])+[0,0,.0041];far=above+[-.040,0,.025]
  self.assertGreater(minimum_separation(left,sweep(far,above)),.0002)
  self.assertEqual(minimum_separation(left,sweep(far,above+[-.040,0,0])),0.)

 def test_press_handoff_checks_whole_leg_before_transition(self):
  from unittest.mock import patch
  probe=ReleaseProbe(environment(),np.array(port(SERVICE)));probe.phase='prepare_press';probe.stable_frames=4
  measured=[probe.arm(s) for s in ('left','right')]
  blocked={'rigid_gap_m':.01,'wire_gap_m':.01,'minimum_gap_m':.01}
  with patch('robot.clearance',return_value=blocked),patch('robot.snapshot',return_value=({},{},{})),patch('robot.minimum_separation',return_value=0.):
   probe.press_handoff(True,4.,4.,'approach_above_clip',4.,measured,measured[1][2]+[.04,0,0],measured[1][3])
  self.assertEqual(probe.phase,'prepare_press')
  self.assertIn('sweep clearance',probe.failure)

 def test_flexible_cable_overlap_is_logged_without_inventing_entry_contact_ban(self):
  from unittest.mock import patch
  probe=ReleaseProbe(environment(),np.array(port(SERVICE)))
  measured=[probe.arm(s) for s in ('left','right')]
  cert={'rigid_gap_m':.01,'wire_gap_m':0.,'minimum_gap_m':0.}
  with patch('robot.clearance',return_value=cert),patch('robot.snapshot',return_value=({},{},{})),patch('robot.minimum_separation',return_value=.01):
   self.assertTrue(probe.certify_press_path(measured,measured[1][2]+[.04,0,0],measured[1][3],'approach_above_clip'))
  self.assertEqual(probe.press_approach_certificate['wire_gap_m'],0.)
  self.assertIsNone(probe.failure)

 def test_entire_press_stroke_checks_housing_excluding_only_intended_clip(self):
  from unittest.mock import patch
  probe=ReleaseProbe(environment(),np.array(port(SERVICE)));probe.phase='prepress_endpoint';probe.stable_frames=4
  plug=np.r_[port(SERVICE),0,0,0,1.];measured=[probe.arm(s) for s in ('left','right')]
  above=plug[:3]+probe.local_contact+[0,0,.0041]-probe.pressR@probe.point
  measured[1]=(measured[1][0],np.array((-.028,-.028)),above-[0,0,.0005],probe.pressR)
  targets=(measured[0][2],measured[0][3],GRIP,above,probe.pressR,PRESS_GRIP)
  blocked={'rigid_gap_m':0.,'wire_gap_m':0.,'minimum_gap_m':0.}
  with patch.object(probe,'press_endpoint_ready',return_value=True),patch('robot.clearance',return_value=blocked) as check,patch('robot.snapshot',return_value=({},{},{})),patch('robot.minimum_separation',return_value=.005):
   probe.release_targets(.75,.75,probe.phase,plug,np.eye(3),0.,measured,targets)
  self.assertEqual(probe.phase,'prepress_endpoint')
  self.assertIn('sweep clearance',probe.failure)
  self.assertEqual(check.call_args.kwargs['exclude'],((f'clip_{SERVICE}','tab'),(f'clip_{SERVICE}','hook')))
  self.assertEqual(probe.press_approach_certificate['next_phase'],'depress_clip')

 def test_full_press_clears_native_socket_boxes_at_recorded_guided_attitudes(self):
  from collision_geometry import FingerGeometry,minimum_separation
  from geometry import socket_boxes,box_triangles
  from yam_arena.urdf import quat_xyzw_to_matrix
  spec=json.loads(Path(__file__).with_name('press_point.json').read_text());geometry=FingerGeometry()
  # Measured source poses from release014, before/during its blocked stroke.
  poses=(
   [.40410491824,-.02440889925,.94978857040,-.00013160703,-.02550235577,.01587020420,.99954873323],
   [.40409517288,-.02430232055,.94978797436,-.00026333713,-.02543388307,.01727148145,.99952727556],
   [.40409025550,-.02431264892,.94978612661,-.00047534870,-.02516027912,.01696897484,.99953925610])
  obstacles=[box_triangles(center,size) for _,center,size,_ in socket_boxes()]
  for pose in poses:
   pose=np.array(pose);body=quat_xyzw_to_matrix(pose[3:]);rotation=body@np.array(spec['rotation'])
   contact=pose[:3]+body@np.array(spec['contact']);point=np.array(spec['point_tcp'])
   sweep=[np.concatenate([(a-point)@rotation.T+contact+body@np.array((0,0,z)) for z in (.0041,-.0023)])
          for _,a in geometry.pieces([-.028,-.028])]
   self.assertGreater(minimum_separation(sweep,obstacles),.0002)

 def test_actual_right_housing_proximity_stops_press_before_more_depth(self):
  probe=ReleaseProbe(environment(),np.array(port(SERVICE)));probe.phase='depress_clip'
  measured=[probe.arm(s) for s in ('left','right')]
  probe.stationary_hold_clearance={'right_non_target_rigid_gap_m':.0001}
  targets=(measured[0][2],measured[0][3],GRIP,measured[1][2],measured[1][3],PRESS_GRIP)
  result=probe.release_targets(5.,5.,probe.phase,np.r_[port(SERVICE),0,0,0,1.],np.eye(3),0.,measured,targets)
  self.assertEqual(probe.press_depth,0.)
  np.testing.assert_array_equal(result[3],measured[1][2])
  self.assertIn('clearance during press approach',probe.failure)

 def test_loaded_hands_have_separating_planes_for_entire_press_stroke(self):
  from collision_geometry import FingerGeometry,minimum_separation
  spec=json.loads(Path(__file__).with_name('press_point.json').read_text())
  rotation,point=np.array(spec['rotation']),np.array(spec['point_tcp']);geometry=FingerGeometry()
  sweep=[np.concatenate([(a-point)@rotation.T+[spec['contact'][0],spec['contact'][1],z] for z in (.0022,.0086)])
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
  contact=np.array((spec['contact'][0],spec['contact'][1],.0022))
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

class PressEndpointTests(unittest.TestCase):
 def test_hover_and_prepress_allow_12s_settle_without_changing_precision_gates(self):
  for phase,duration in (('approach_above_clip',4.),('prepress_endpoint',.75)):
   with self.subTest(phase=phase):
    probe=ReleaseProbe(environment(),np.array(port(SERVICE)));probe.phase=phase
    measured=[probe.arm(s) for s in ('left','right')]
    plug=np.r_[port(SERVICE),0,0,0,1.]
    targets=(measured[0][2],measured[0][3],GRIP,measured[1][2],measured[1][3],PRESS_GRIP)
    probe.release_targets(duration+9.,duration+9.,phase,plug,np.eye(3),0.,measured,targets)
    self.assertIsNone(probe.failure);self.assertEqual(probe.phase,phase)
    probe.release_targets(duration+12.05,duration+12.05,phase,plug,np.eye(3),0.,measured,targets)
    self.assertIn('settle gate',probe.failure)

 def endpoint(self,hover=False,prepress=False):
  probe=ReleaseProbe(environment(),np.array(port(SERVICE)));probe.phase='approach_above_clip' if hover else 'prepress_endpoint' if prepress else 'depress_clip'
  goal=np.array(port(SERVICE))+probe.local_contact+[0,0,.0041 if hover else .0036 if prepress else -.0023]-probe.pressR@probe.point
  reference,_,_=ik.solve(goal,ik.matrix_to_quat_xyzw(probe.pressR),np.array(READY),base_pos=(0,-.305,.75),iters=350,tol=1e-6)
  actual=reference.copy();actual[2]+=.003
  left=probe.arm('left')
  probe.boot_goal=left[2].copy();probe.boot_rotation=left[3].copy()
  def arm(side):
   if side=='left':return left
   tcp,rotation=ik.tcp_pose(actual,(0,-.305,.75))
   return actual,np.array((-.028,-.028)),tcp,rotation
  probe.arm=arm
  probe.previous[7:13]=reference;probe.q[1]=reference.copy()
  return probe,actual

 def test_precise_hover_freezes_then_moving_prepress_uses_new_ik_plus_bias(self):
  from unittest.mock import patch
  probe,actual=self.endpoint(hover=True)
  def certified(*args,**kwargs):
   probe.press_approach_certificate={'other_hand_gap_m':.01,'wire_gap_m':.01}
   return True
  with patch.object(probe,'stationary_hold_safety',return_value={'rigid_gap_m':.01,'other_hand_gap_m':.01,'right_non_target_rigid_gap_m':.01}),patch.object(probe,'certify_press_path',side_effect=certified):
   probe.command(3.9);self.assertIsNone(probe.press_joint_servo.reference)
   for t in (4.05,4.1,4.15,4.2):probe.command(t)
   self.assertEqual(probe.press_servo_stage,'HOVER')
   reference=probe.press_joint_servo.reference.copy();actual[:]=reference
   for t in (4.25,4.3,4.35,4.4,4.45,4.5):probe.command(t)
   self.assertEqual(probe.phase,'prepress_endpoint');self.assertTrue(probe.press_joint_servo.frozen)
   before=probe.press_joint_servo.bias.copy()
   action,report=probe.command(4.75)
   np.testing.assert_array_equal(probe.press_joint_servo.bias,before)
   np.testing.assert_array_equal(probe.press_joint_servo.reference,reference)
   self.assertGreater(np.linalg.norm(action[7:13]-(reference+before)),1e-4)
   self.assertIsNone(report['failure']);self.assertEqual(report['press_servo_stage'],'HOVER')

 def test_max_depth_relatches_unbiased_reference_preserving_bias_once(self):
  from unittest.mock import patch
  probe,actual=self.endpoint();measured=[probe.arm(side) for side in ('left','right')]
  goal=np.array(port(SERVICE))+probe.local_contact-[0,0,.0023]-probe.pressR@probe.point
  old_reference=actual+.01;probe.press_joint_servo.latch(old_reference)
  learned=np.arange(6)*.001;probe.press_joint_servo.bias[:]=learned;probe.press_joint_servo.freeze()
  probe.press_servo_stage='PREPRESS';probe.press_latched_pose=(goal+[0,0,.0059],probe.pressR)
  probe.right_joint_velocity=np.zeros(6);probe.press_endpoint_low_velocity_frames=2
  expected,_,_=ik.solve(goal,ik.matrix_to_quat_xyzw(probe.pressR),actual,base_pos=(0,-.305,.75),iters=220,tol=1e-6)
  with patch.object(probe,'certify_press_path',return_value=True) as certify:
   for _ in range(2):probe.stationary_press_correction(goal,probe.pressR,measured,'PRESS_ENDPOINT',RELEASE_TRAVEL)
  self.assertEqual(certify.call_count,1);self.assertEqual(probe.press_servo_stage,'PRESS_ENDPOINT')
  np.testing.assert_array_equal(probe.press_joint_servo.bias,learned)
  np.testing.assert_allclose(probe.press_joint_servo.reference,expected,atol=1e-12)
  self.assertFalse(probe.press_joint_servo.frozen);self.assertAlmostEqual(probe.press_endpoint_goal_drift,0.)

 def test_precise_joint_gate_rejects_small_tcp_error_with_unsettled_wrist(self):
  probe,actual=self.endpoint(hover=True);reference=probe.q[1].copy();actual[:]=reference;actual[5]+=.001
  probe.press_joint_servo.latch(reference);probe.press_servo_stage='HOVER';probe.right_joint_velocity=np.zeros(6)
  goal=np.array(port(SERVICE))+probe.local_contact+[0,0,.0041]-probe.pressR@probe.point
  measured=[probe.arm(s) for s in ('left','right')]
  self.assertLess(np.linalg.norm(measured[1][2]-goal),.0002)
  self.assertFalse(probe.press_endpoint_ready(measured,goal,probe.pressR,'HOVER'))
  actual[5]=reference[5]+.00025;measured=[probe.arm(s) for s in ('left','right')]
  self.assertTrue(probe.press_endpoint_ready(measured,goal,probe.pressR,'HOVER'))

 def test_prepress_relatches_then_freezes_bias_for_remaining_5p9mm_stroke(self):
  from unittest.mock import patch
  probe,actual=self.endpoint(prepress=True)
  goal=np.array(port(SERVICE))+probe.local_contact+[0,0,.0036]-probe.pressR@probe.point
  probe.press_joint_servo.latch(actual+.01);probe.press_joint_servo.bias[:]=.001
  probe.press_joint_servo.freeze();probe.press_servo_stage='HOVER';probe.press_latched_pose=(goal+[0,0,.0005],probe.pressR)
  def certified(*args,**kwargs):
   probe.press_approach_certificate={'other_hand_gap_m':.01,'wire_gap_m':.01}
   return True
  with patch.object(probe,'stationary_hold_safety',return_value={'rigid_gap_m':.01,'other_hand_gap_m':.01,'right_non_target_rigid_gap_m':.01}),patch.object(probe,'certify_press_path',side_effect=certified):
   for t in (.8,.85,.9,.95):probe.command(t)
   self.assertEqual(probe.press_servo_stage,'PREPRESS');self.assertFalse(probe.press_joint_servo.frozen)
   reference=probe.press_joint_servo.reference.copy();actual[:]=reference
   for t in (1.,1.05,1.1,1.15,1.2,1.25):probe.command(t)
   self.assertEqual(probe.phase,'depress_clip');self.assertTrue(probe.press_joint_servo.frozen)
   self.assertAlmostEqual(probe.press_depth,-.0036)
   before=probe.press_joint_servo.bias.copy();action,report=probe.command(1.75)
   np.testing.assert_array_equal(probe.press_joint_servo.bias,before)
   self.assertGreater(np.linalg.norm(action[7:13]-(reference+before)),1e-4)
   self.assertEqual(report['press_servo_stage'],'PREPRESS');self.assertIsNone(report['failure'])
   self.assertAlmostEqual(probe.press_depth,-.0036+.0007*.5)

 def test_right_fixed_reference_integrates_only_after_stationary_max_depth(self):
  from unittest.mock import patch
  probe,actual=self.endpoint()
  with patch.object(probe,'stationary_hold_safety',return_value={'rigid_gap_m':.01,'other_hand_gap_m':.01,'right_non_target_rigid_gap_m':.01}),patch.object(probe,'certify_press_path',return_value=True):
   for t in (8.5,8.55,8.6):probe.command(t)
   self.assertIsNone(probe.press_joint_servo.reference)
   np.testing.assert_array_equal(probe.press_joint_servo.bias,np.zeros(6))
   for t in (9.2,9.25,9.3):action,report=probe.command(t)
   reference=probe.press_joint_servo.reference.copy();before=probe.press_joint_servo.bias.copy()
   self.assertLess(before[2],0.)
   action,report=probe.command(9.35)
   np.testing.assert_array_equal(probe.press_joint_servo.reference,reference)
   np.testing.assert_allclose(action[7:13],reference+probe.press_joint_servo.bias,atol=1e-6)
   np.testing.assert_array_equal(probe.entry_joint_servo.bias,np.zeros(6))
   self.assertAlmostEqual(report['press_depth_m'],.0023)
   self.assertLessEqual(np.abs(probe.press_joint_servo.bias-before).max(),.00025)

 def test_clip_constraint_failure_stops_right_integral_and_command(self):
  from unittest.mock import patch
  probe,actual=self.endpoint();read=probe.object_pose
  def bad(name):
   value=read(name)
   if name==f'clip_{USED_PORTS[-1]}':value[3:]=[np.sin(np.radians(.5)),0,0,np.cos(np.radians(.5))]
   return value
  # The numerical constraint is checked for every connector, including one
  # outside the source/target pair. It cannot silently keep integrating.
  from config import USED as USED_PORTS
  probe.object_pose=bad
  with patch.object(probe,'stationary_hold_safety',return_value={'rigid_gap_m':.01,'other_hand_gap_m':.01,'right_non_target_rigid_gap_m':.01}):
   action,report=probe.command(9.5)
  self.assertIn('slider constraint guard',report['failure'])
  np.testing.assert_allclose(action[7:13],actual,atol=1e-6)
  np.testing.assert_array_equal(probe.press_joint_servo.bias,np.zeros(6))
  self.assertEqual(len(report['clip_joint_constraints']),7)

 def test_measured_release_freezes_bias_for_moving_clip_follow(self):
  from unittest.mock import patch
  probe,_=self.endpoint()
  with patch.object(probe,'stationary_hold_safety',return_value={'rigid_gap_m':.01,'other_hand_gap_m':.01,'right_non_target_rigid_gap_m':.01}),patch.object(probe,'certify_press_path',return_value=True):
   for t in (9.2,9.25,9.3,9.35):probe.command(t)
   before=probe.press_joint_servo.bias.copy();read=probe.object_pose
   def released(name):
    value=read(name)
    if name==f'clip_{SERVICE}':value[2]-=.0019
    return value
   probe.object_pose=released
   for t in (9.4,9.45,9.5,9.55,9.6):probe.command(t)
   self.assertEqual(probe.phase,'withdraw_with_clip_pressed');self.assertTrue(probe.press_joint_servo.frozen)
   probe.command(9.65)
   np.testing.assert_array_equal(probe.press_joint_servo.bias,before)

class ReleaseGeometryGateTests(unittest.TestCase):
 def test_only_certified_free_press_standoff_accepts_1p3mm_tracking_offset(self):
  from unittest.mock import patch
  for certificate in (False,True):
   probe=ReleaseProbe(environment(),np.array(port(SERVICE)));probe.phase='prepare_press'
   plug=np.r_[port(SERVICE),0,0,0,1.];measured=[probe.arm(s) for s in ('left','right')]
   above=plug[:3]+probe.local_contact+[0,0,.0041]-probe.pressR@probe.point
   far=above+[-.040,0,.025];probe.press_start=(far.copy(),probe.pressR)
   measured[1]=(measured[1][0],np.array((-.028,-.028)),far+[.00074,0,-.00107],probe.pressR)
   targets=(measured[0][2],measured[0][3],GRIP,far,probe.pressR,PRESS_GRIP)
   with patch.object(probe,'certify_press_path',return_value=certificate) as check:
    for i in range(5):probe.release_targets(4.+i*.05,4.+i*.05,probe.phase,plug,np.eye(3),0.,measured,targets)
   self.assertEqual(check.call_count,1)
   self.assertEqual(probe.phase,'approach_above_clip' if certificate else 'prepare_press')
   np.testing.assert_allclose(check.call_args.args[1],above)

 def test_same_1p3mm_offset_does_not_pass_clip_contact_waypoint(self):
  from unittest.mock import patch
  probe=ReleaseProbe(environment(),np.array(port(SERVICE)));probe.phase='approach_above_clip'
  plug=np.r_[port(SERVICE),0,0,0,1.];measured=[probe.arm(s) for s in ('left','right')]
  above=plug[:3]+probe.local_contact+[0,0,.0041]-probe.pressR@probe.point
  measured[1]=(measured[1][0],np.array((-.028,-.028)),above+[.0013,0,0],probe.pressR)
  targets=(measured[0][2],measured[0][3],GRIP,above,probe.pressR,PRESS_GRIP)
  with patch.object(probe,'certify_press_path') as check:
   for i in range(5):probe.release_targets(4.+i*.05,4.+i*.05,probe.phase,plug,np.eye(3),0.,measured,targets)
  self.assertEqual(probe.phase,'approach_above_clip');check.assert_not_called()

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
