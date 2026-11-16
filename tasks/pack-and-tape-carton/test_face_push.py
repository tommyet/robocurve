"""Selectedsensor evidence, bounded ordinary targets, realgeometry ACK/gates."""
import copy,unittest
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from yam_arena import ik
from yam_arena.constants import READY,FINGER_OPEN
from face_push import FacePushClosureProbe,InitialForceGate
from face_push_geometry import FaceTargets,ROUTES
from roll_probe import Geometry,BASES
from test_roll_probe import Tensor
from check_roll_probe import nominal_poses

def packet(i,time,force=.08,target='east_top',names=('tip_left','tip_right')):
 a=np.zeros((2,1,3));a[list(names).index('tip_left'),0,2]=force
 return dict(clock_verified=True,native_filter_target_verified=True,selected_target=target,requested_control_time_s=time,sample_id=i,sides={'left':dict(target_binding=dict(native_verified=True,target=target),body_names=list(names),normal_force_matrix_w=a.tolist(),individual_filter_column_order_native_verified=True,configured_target_family=[target])})

def environment():
 poses=nominal_poses();ready=np.r_[READY,1.,READY,1.].astype(np.float32).astype(float);scene={s+'_robot':SimpleNamespace(data=SimpleNamespace(joint_pos=Tensor([[*ready[7*j:7*j+6],FINGER_OPEN,FINGER_OPEN]])))for j,s in enumerate(('left','right'))};env=SimpleNamespace(_ready=Tensor([ready]),_low=np.r_[ik.LOWER,0.,ik.LOWER,0.],_high=np.r_[ik.UPPER,1.,ik.UPPER,1.],_ids={s+'_robot':(list(range(6)),[6,7])for s in('left','right')},rig=SimpleNamespace(bases=BASES),_base=SimpleNamespace(arena_world=SimpleNamespace(get_pose_w=lambda n:Tensor([[*poses[n][0],*ik.matrix_to_quat_xyzw(poses[n][1])]])),scene=scene));return env,poses

class ForceTests(unittest.TestCase):
 def test_five_distinct_singleton_samples_not_pre_post_replays(self):
  g=InitialForceGate()
  for i in range(1,6):
   r=g.consume(packet(i,i*.05),i*.05,'east_top','left','tip_left',[0,0,1],True);self.assertEqual(r['initial_force_streak'],i)
   again=g.consume(packet(i,i*.05),i*.05,'east_top','left','tip_left',[0,0,1],True);self.assertEqual(again['initial_force_streak'],i);self.assertFalse(again['fresh_force_sample'])
  self.assertTrue(r['initial_contact_verified'])
 def test_wrong_sign_zero_force_wrong_target_and_no_geometry_cannot_acquire(self):
  for force,geom in[(0.,True),(-.1,True),(.08,False)]:
   g=InitialForceGate()
   for i in range(1,8):r=g.consume(packet(i,i*.05,force),i*.05,'east_top','left','tip_left',[0,0,1],geom)
   self.assertFalse(r['initial_contact_verified'])
  with self.assertRaises(ValueError):InitialForceGate().consume(packet(1,0,target='west_top'),0,'east_top','left','tip_left',[0,0,1],True)
 def test_body_rows_verified_and_target_identity_resets(self):
  g=InitialForceGate();a=g.consume(packet(1,0,names=('tip_right','tip_left')),0,'east_top','left','tip_left',[0,0,1],True);self.assertAlmostEqual(a['signed_selected_pad_normal_force_N'],.08)
  b=g.consume(packet(1,.05,target='west_top'),.05,'west_top','left','tip_left',[0,0,1],True);self.assertEqual(b['initial_force_streak'],1)
 def test_missing_binding_stale_request_nonfinite_and_excess_force_failclosed(self):
  cases=[];a=packet(1,0);a['native_filter_target_verified']=False;cases.append(a);a=packet(1,.1);cases.append(a);a=packet(1,0,float('nan'));cases.append(a);a=packet(1,0,4.01);cases.append(a)
  for p in cases:
   with self.assertRaises(ValueError):InitialForceGate().consume(p,0,'east_top','left','tip_left',[0,0,1],True)

class GeometryTests(unittest.TestCase):
 def test_model_reference_declines_near_release_and_excess_measured_force_reduces_target(self):
  env,poses=environment();p=FacePushClosureProbe(env,max_flaps=1);reference=[]
  for angle in(-175.,-70.):
   poses['east_top']=p.targets.flap_pose('east',angle);target,R,w=p.targets.target('east',angle);q,pe,re=ik.solve(target,ik.matrix_to_quat_xyzw(R),np.array(ROUTES['east']['seed']),base_pos=BASES['left'],iters=220,tol=1e-6);self.assertLess(pe,.0003)
   low=p.targets.normal_reference('east',angle,q,BASES['left'],w,0.);high=p.targets.normal_reference('east',angle,q,BASES['left'],w,.3);self.assertLessEqual(high['total_normal_depth_reference_m'],low['total_normal_depth_reference_m']);self.assertLessEqual(low['total_normal_depth_reference_m'],.00065);reference.append(low['required_normal_force_N'])
  self.assertGreater(reference[0],.1);self.assertLess(reference[1],.03);self.assertGreater(reference[0],reference[1]*4)

class ControllerTests(unittest.TestCase):
 def test_constructor_requires_bounded_requested_prefix(self):
  env,_=environment()
  for n in(0,5,True):
   with self.assertRaises(ValueError):FacePushClosureProbe(env,max_flaps=n)
 def test_failed_native_step_never_commits_issued_action(self):
  env,_=environment();p=FacePushClosureProbe(env,max_flaps=1);old=p.previous.copy();a,r=p.command(0.);self.assertIsNone(r['failure']);self.assertIsNotNone(p.pending)
  with self.assertRaises(RuntimeError):p.command(.05)
  p.acknowledge_step(0.,False);np.testing.assert_array_equal(p.previous,old);self.assertIn('env.step failed',p.failure);self.assertFalse(p.done)
 def test_open160_waits_and_settle_deadline_never_forces_scene(self):
  env,poses=environment();p=FacePushClosureProbe(env,max_flaps=1);original=copy.deepcopy(poses);a,r=p.command(0);self.assertEqual(p.stage,'settle_open');p.acknowledge_step(0,True)
  for n in poses:np.testing.assert_array_equal(poses[n][0],original[n][0]);np.testing.assert_array_equal(poses[n][1],original[n][1])
  p.started=-9.;_,r=p.command(.05);self.assertIn('settle',r['failure']);self.assertTrue(r['not_issued'])
 def test_five_actual_settled_samples_gate_approach(self):
  env,poses=environment();p=FacePushClosureProbe(env,max_flaps=1)
  for n in p.ORDER:poses[n+'_top']=p.targets.flap_pose(n,-175.)
  for i in range(5):a,r=p.command(i*.05);self.assertIsNone(r['failure']);p.acknowledge_step(i*.05,True)
  self.assertEqual(p.stage,'approach_high');self.assertFalse(p.done);self.assertFalse(r['full_task_completed']);self.assertEqual(len(p.geometry.raw),315)
 def test_prefix_done_is_only_after_successful_ack_and_is_not_taskcompletion(self):
  env,poses=environment();p=FacePushClosureProbe(env,max_flaps=1)
  for n in p.ORDER:poses[n+'_top']=p.targets.flap_pose(n,0. if n=='east'else-175.)
  p.stage='released_hold';p.started=-2.1;p.closed_hold=1.95;p.hold_previous_qualified=True;p.last_angles={n:0. if n=='east'else-175. for n in p.ORDER}
  a,r=p.command(0);self.assertIsNone(r['failure']);self.assertFalse(p.done);self.assertFalse(p.prefix_complete);self.assertFalse(r['full_task_completed']);p.acknowledge_step(0,True);self.assertTrue(p.done);self.assertTrue(p.prefix_complete);self.assertTrue(r['prefix_complete']);self.assertFalse(r['full_task_completed'])

 def test_float32_wire_target_respects_exact_original_slew(self):
  env,_=environment();p=FacePushClosureProbe(env,max_flaps=1);p.stage='approach_high';p.started=-6.;p.startq=p.previous[:6].copy();p.startg=1.;p.highq=p.startq+np.array([.2,.2,.2,.2,-.2,.2]);old=p.previous.copy();action,r=p.command(0.)
  self.assertIsNone(r['failure']);delta=np.array([.04]*6+[.05]+[.04]*6+[.05]);self.assertTrue(np.all(abs(action-old)<=delta));np.testing.assert_array_equal(action,action.astype(np.float32).astype(float));p.acknowledge_step(0.,True)
 def final_hold(self):
  env,poses=environment();p=FacePushClosureProbe(env,max_flaps=1)
  for n in p.ORDER:poses[n+'_top']=p.targets.flap_pose(n,0. if n=='east'else-175.)
  p.stage='released_hold';p.started=-2.1;p.closed_hold=1.95;p.hold_previous_qualified=True;p.last_angles={n:0. if n=='east'else-175. for n in p.ORDER};return p
 def test_rejected_final_transition_does_not_commit_index_or_done(self):
  p=self.final_hold();original=p.geometry.check;calls=[0];old=p.previous.copy()
  def reject_candidates(*a,**k):
   result=original(*a,**k);calls[0]+=1
   return dict(result,safe=False)if 2<=calls[0]<=6 else result
  with patch.object(p.geometry,'check',side_effect=reject_candidates):action,r=p.command(0.)
  self.assertIsNone(r['failure']);self.assertEqual(r['advance_fraction'],0.);self.assertEqual(p.index,0);self.assertEqual(p.stage,'released_hold');self.assertFalse(p.done);self.assertFalse(p.prefix_complete);np.testing.assert_array_equal(action,old);p.acknowledge_step(0.,True);self.assertEqual(p.index,0);self.assertFalse(p.done)
 def test_failed_final_step_rolls_back_proposed_prefix_completion(self):
  p=self.final_hold();old=p.previous.copy();a,r=p.command(0.);self.assertIsNone(r['failure']);self.assertFalse(p.done);p.acknowledge_step(0.,False);self.assertEqual(p.index,0);self.assertFalse(p.done);self.assertFalse(p.prefix_complete);np.testing.assert_array_equal(p.previous,old)

if __name__=='__main__':unittest.main()
