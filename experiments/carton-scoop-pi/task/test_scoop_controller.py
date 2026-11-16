"""Behavioral CPU guard tests; no native-motion success claim."""
import ast,copy,json,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from yam_arena import ik
from yam_arena.constants import FINGER_OPEN
from yam_arena.urdf import quat_xyzw_to_matrix
from scoop_controller import OuterNorthScoop,bounded_path_step,limit_reference
from open_coupon import OpeningCoupon

ROOT=Path(__file__).resolve().parents[1]
S=json.loads((ROOT/'start/snapshot.json').read_text())
R=np.array([[.5792432628694821,-.7070881058575399,.40559049911839984],[-.5792126674056348,-.707125456022336,-.40556907594397895],[.5735764363510462,0,-.8191520442889918]])
PLAN=dict(active_hand='left',target_flap='north_bottom',support_R=R.tolist(),support_point_tcp=[.006954508716650903,.005881295623088079,.010552623193168104],above_aperture=[.29565624051582506,-.017341078129940846,.91],staging=[.29565624051582506,-.017341078129940846,.84623047031539],inside=[.29565624051582506,-.017341078129940846,.77123047031539],insert=[.32040563147660683,-.042089161834954744,.77123047031539])
class Safety:
 def __init__(self):self.calls=[];self.safe=True
 def check(self,*args,**kw):self.calls.append(kw['contact']);return dict(safe=self.safe,hard_gap_m=.005,other_arm_aabb_gap_m=.1,intended_target_gap_m=None)
def controller():
 env=SimpleNamespace(rig=SimpleNamespace(bases={'left':(0,.305,.75)}),_low=np.r_[ik.LOWER,0,ik.LOWER,0],_high=np.r_[ik.UPPER,1,ik.UPPER,1])
 with patch('scoop_controller.ScoopSafety',Safety):p=OuterNorthScoop(env,S,PLAN)
 issued=np.array(S['held_action_14d']);issued[6]=.003/abs(FINGER_OPEN);p.begin(issued)
 hand=S['native_hands'][0];rh=S['native_hands'][1];poses={n:np.array(v)for n,v in S['poses'].items()};state=[np.array(hand['joints']),np.array([-.003,-.003]),np.array(hand['tcp']),np.array(hand['tcp_rotation'])]
 p.state=lambda:({'left':tuple(state),'right':(np.array(rh['joints']),np.array(rh['finger_joints']),np.array(rh['tcp']),np.array(rh['tcp_rotation']))},poses,np.array(S['cutter_pose']),-78.55758666992188,0.,0.)
 return p,issued,state,poses

class ScoopControllerTests(unittest.TestCase):
 def test_path_speed_clock_pause_and_nonfinite_bounds(self):
  f=bounded_path_step(.2,.05,.1,0,.005);self.assertAlmostEqual((f-.2)*.1,.00025)
  self.assertEqual(bounded_path_step(.2,.05,.1,0,.005,allowed=False),.2)
  for dt in (-.1,.051,float('nan')):
   with self.assertRaises(ValueError):bounded_path_step(0,dt,.1,0,.005)

 def test_first_prepared_command_exact_idle_unchanged_and_jaws_are_not_reopened(self):
  p,issued,_,_=controller();out,r=p.command(0.)
  np.testing.assert_array_equal(out,issued);self.assertAlmostEqual(out[6]*abs(FINGER_OPEN),.003);self.assertEqual(r[0]['phase'],'ordinary_command_handoff')
  np.testing.assert_array_equal(out[7:],S['held_action_14d'][7:])
  self.assertTrue(p.safety.calls);self.assertFalse(p.safety.calls[0])

 def test_unsafe_fresh_scene_after_quiet_halts_without_issuing_motion(self):
  p,issued,_,_=controller();p.safety.safe=False
  out,r=p.command(0.);np.testing.assert_array_equal(out,issued);self.assertIn('actualnon-targetgeometry',p.failure)
  self.assertIsNone(p.motion)

 def test_raise_before_translation_and_fixed_rotation_inside_aperture(self):
  p,issued,_,_=controller();pos,rot=ik.tcp_pose(issued[:6],p.env.rig.bases['left'])
  self.assertEqual([x[0]for x in p.waypoints],['raise_clear','above_aperture','scoop_staging','inside_descend','underedge_insert','contact_acquire'])
  np.testing.assert_array_equal(p.waypoints[0][1][:2],pos[:2]);self.assertEqual(p.waypoints[0][1][2],.910);np.testing.assert_array_equal(p.waypoints[0][2],rot)
  for item in p.waypoints[1:]:np.testing.assert_array_equal(item[2],R)

 def test_handoff_reference_limiter_bounds_translation_and_rotation(self):
  p,Rout=limit_reference(np.zeros(3),np.eye(3),np.ones(3),R,.05,.005)
  self.assertLessEqual(np.linalg.norm(p),.00025+1e-15);self.assertLessEqual(np.linalg.norm(ik._rot_error(Rout,np.eye(3))),.0175+1e-14)
  p,Rout=limit_reference(np.zeros(3),np.eye(3),np.ones(3),R,0.,.005);np.testing.assert_array_equal(p,np.zeros(3));np.testing.assert_array_equal(Rout,np.eye(3))

 def test_arc_no_progress_timer_resets_at_acquire_handoff(self):
  p,issued,state,poses=controller();p.phase=5;goal=p.waypoints[5][1];state[2]=goal.copy();state[3]=R.copy();p.motion=dict(start=goal.copy(),Rstart=R.copy(),fraction=1.);p.last_time=10.;p.initial_angle=-78.55758666992188;p.last_angle=p.initial_angle;p.last_angle_progress=0.;p.last_advance=10.
  p.pi.begin(p.previous[:6],10.)
  proposal=p.pi.propose(p.nominal[:6],state[0],10.);p.pi.resolve(proposal,guard_safe=True)
  old=p.state;p.state=lambda:(*old()[:4],.1,0.)
  with patch('scoop_controller.ik.solve',side_effect=lambda pos,rot,q,**kw:(q.copy(),0.,0.)):
   for i in range(1,6):p.command(10.+i*.05)
  self.assertEqual(p.phase,6);self.assertAlmostEqual(p.last_angle_progress,10.25);self.assertEqual(p.command_angle,p.last_angle)
  with patch('scoop_controller.ik.solve',side_effect=lambda pos,rot,q,**kw:(q.copy(),0.,0.)):p.command(10.30)
  self.assertIsNone(p.failure)

 def test_terminal_frames_must_be_consecutive_and_lead_force_abort(self):
  p,issued,state,poses=controller();p.phase=6;p.last_time=0.;p.initial_angle=-78.5;p.last_angle=-30.;p.last_angle_progress=0.;p.command_angle=-31.;p.stable=3
  old=p.state;p.state=lambda:(*old()[:3],-31.,.1,0.)
  with patch('scoop_controller.ik.solve',side_effect=lambda pos,rot,q,**kw:(q.copy(),0.,0.)):p.command(.05)
  self.assertEqual(p.stable,0);self.assertFalse(p.done)
  q,issued,_,_=controller();q.phase=6;q.command_angle=-75.;q.initial_angle=-78.5;q.last_time=0.
  q.command(.05);self.assertIn('flaplead',q.failure)
  q,issued,_,_=controller();old=q.state;q.state=lambda:(*old()[:4],1.01,0.);q.command(0.);self.assertIn('forcebound',q.failure)

 def test_controller_has_no_pose_force_score_setter_or_teacher_import(self):
  source=Path(__file__).with_name('scoop_controller.py').read_text();tree=ast.parse(source)
  calls=[n.func.attr for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)]
  for name in calls:self.assertFalse(name.startswith(('write_root','write_joint','set_forces','apply_force')))
  imports=[n.module or ''for n in ast.walk(tree)if isinstance(n,ast.ImportFrom)]
  self.assertNotIn('scoring',imports);self.assertNotIn('robot',imports)

 def test_rejected_augmented_target_does_not_commit_bias_or_nominal_path(self):
  p,issued,state,poses=controller();p.command(0.)
  previous=p.previous.copy();nominal=p.nominal.copy();bias=p.pi.bias.copy()
  calls=[]
  def check(*args,**kwargs):
   calls.append(args[0].copy())
   return dict(safe=len(calls)==1)
  p.safety.check=check
  with patch('scoop_controller.ik.solve',side_effect=lambda pos,rot,q,**kw:(q+.001,0.,0.)):
   out,report=p.command(.05)
  self.assertIn('augmented command rejected',p.failure)
  np.testing.assert_array_equal(out,previous)
  np.testing.assert_array_equal(p.nominal,nominal)
  np.testing.assert_array_equal(p.pi.bias,bias)
  self.assertEqual(p.motion['fraction'],0.)

 def test_next_ik_seed_uses_nominal_not_integral_augmented_command(self):
  p,issued,state,poses=controller();p.command(0.);seeds=[]
  def solve(pos,rot,q,**kwargs):
   seeds.append(q.copy());return q+.001,0.,0.
  with patch('scoop_controller.ik.solve',side_effect=solve):
   p.command(.05)
   expected=p.nominal[:6].copy();augmented=p.previous[:6].copy()
   p.command(.1)
  np.testing.assert_array_equal(seeds[1],expected)
  self.assertGreater(np.max(abs(expected-augmented)),0.)

 def test_lower_insertion_preserves_final_contact_point(self):
  p,issued,_,_=controller();plan=copy.deepcopy(PLAN)
  plan['inside'][2]-=.004;plan['insert'][2]-=.004;plan['contact_acquire_lift_m']=.0048
  with patch('scoop_controller.ScoopSafety',Safety):other=OuterNorthScoop(p.env,S,plan)
  other.begin(issued)
  np.testing.assert_allclose(other.waypoints[5][1],p.waypoints[5][1],atol=1e-15)
  self.assertAlmostEqual(other.waypoints[4][1][2],p.waypoints[4][1][2]-.004)
  self.assertEqual(other.waypoints[5][3],p.waypoints[5][3])

 def test_invalid_acquisition_stroke_rejected(self):
  p,issued,_,_=controller();plan=copy.deepcopy(PLAN);plan['contact_acquire_lift_m']=float('nan')
  with patch('scoop_controller.ScoopSafety',Safety):other=OuterNorthScoop(p.env,S,plan)
  with self.assertRaises(ValueError):other.begin(issued)

if __name__=='__main__':unittest.main()


