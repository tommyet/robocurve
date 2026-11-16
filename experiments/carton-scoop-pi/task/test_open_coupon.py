import copy,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from coupon_support import load_snapshot,restore_once
from open_coupon import OpeningCoupon,load_route,controller_factory,contact_sensor_specs,CONTROLLERS
ROOT=Path(__file__).resolve().parents[1]

class Body:
 def __init__(self):self.calls=[];self.data=SimpleNamespace(joint_pos=np.zeros((1,8)))
 def write_root_pose_to_sim_index(self,**kw):self.calls.append(('pose',kw))
 def write_root_velocity_to_sim_index(self,**kw):self.calls.append(('velocity',kw))
 def write_joint_state_to_sim_index(self,**kw):self.calls.append(('joints',kw));self.data.joint_pos=kw['position'].copy()

def env(s):
 bodies={name:Body()for name in [*s['poses'],'cutter','left_robot','right_robot']};poses={**s['poses'],'cutter':s['cutter_pose']};calls=[]
 return SimpleNamespace(_base=SimpleNamespace(scene=bodies,sim=SimpleNamespace(forward=lambda:calls.append('forward')),arena_world=SimpleNamespace(get_pose_w=lambda n:np.array([poses[n]]))),_ids={side+'_robot':(list(range(6)),[6,7])for side in ('left','right')},_low=np.full(14,-10.),_high=np.full(14,10.)),calls

class OpenCouponTests(unittest.TestCase):
 def setUp(self):self.s=load_snapshot(ROOT/'start/snapshot.json');self.env,self.calls=env(self.s)
 def test_actual_postcut_row_is_exact_and_not_seeded_coverage(self):
  row=json.loads((ROOT/'start/source-row.json').read_text());self.assertEqual(self.s['source_time_s'],179.);self.assertTrue(self.s['unsealed_start']);self.assertEqual(self.s['poses'],row['poses']);self.assertEqual(self.s['held_action_14d'],row['action_14d']);self.assertEqual(len(self.s['native_owner_poses']),31)
  self.assertNotIn('coverage',self.s);self.assertNotIn('reference_grasp',self.s)
 def test_restores_only_once_actual_joints_zero_velocity_then_native_readback(self):
  report=restore_once(self.env,self.s,lambda v:np.array(v,dtype=np.float32));self.assertEqual(len(report['one_time_pose_writes']),15);self.assertEqual(self.calls,['forward'])
  for name in [*self.s['poses'],'cutter']:
   calls=self.env._base.scene[name].calls;self.assertEqual([v[0]for v in calls],['pose','velocity']);np.testing.assert_array_equal(calls[1][1]['root_velocity'],np.zeros((1,6)))
  with self.assertRaisesRegex(RuntimeError,'twice'):restore_once(self.env,self.s,np.asarray)
 def test_parked_knife_needs_no_opposing_grip_and_hold_is_exact(self):
  p=OpeningCoupon(self.env,self.s)
  for i in range(1,51):
   action,_=p.command((i-1)*.05);np.testing.assert_array_equal(action,self.s['held_action_14d'])
   p.observe(time=i*.05,crease_separation=1e-5,velocities={n:[0]*6 for n in [*self.s['poses'],'cutter']})
  self.assertTrue(p.safe_start_passed);self.assertIsNone(p.failure);self.assertFalse(p.done);self.assertEqual(len(p.events),1)
 def test_quiet_hold_checks_native_angular_velocity_and_never_invents_readings(self):
  p=OpeningCoupon(self.env,self.s);v={n:[0]*6 for n in [*self.s['poses'],'cutter']};v['north_bottom'][3]=.2
  for i in range(1,101):p.observe(time=i*.05,crease_separation=1e-5,velocities=v)
  self.assertFalse(p.safe_start_passed);self.assertIn('settle quietly',p.failure)
  q=OpeningCoupon(self.env,self.s);q.observe(time=.05,crease_separation=0,velocities={});self.assertIn('velocities',q.failure)
 def test_pose_jump_or_torn_anchor_fails_closed(self):
  for sep,jump,angle in [(.005,0,0),(0,.006,0),(0,0,.1)]:
   p=OpeningCoupon(self.env,self.s);p.observe(time=.05,crease_separation=sep,velocities={n:[0]*6 for n in [*self.s['poses'],'cutter']},first_step_translation=jump,first_step_rotation=angle);self.assertIsNotNone(p.failure)
 def test_empty_factory_and_route_review_hash_are_fail_closed(self):
  with self.assertRaisesRegex(ValueError,'no reviewed'):controller_factory(dict(controller='legacy_theta'),self.env,self.s)
  import hashlib
  route=dict(reviewed=True,controller='outer_scoop_future',active_hand='left',snapshot_sha256=hashlib.sha256((ROOT/'start/snapshot.json').read_bytes()).hexdigest(),phases=[dict(name='approach')])
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'route.json';p.write_text(json.dumps(route));self.assertEqual(load_route(p,ROOT/'start/snapshot.json'),route)
   for change in [dict(reviewed=False),dict(snapshot_sha256='wrong'),dict(active_hand='none'),dict(prepare_aperture_m=.1)]:
    bad={**route,**change};p.write_text(json.dumps(bad))
    with self.assertRaises(ValueError):load_route(p,ROOT/'start/snapshot.json')
 def test_three_exact_rigid_link_sensors_preserve_native_paths_and_all12filters(self):
  links={n:'/base/deep/'+n for n in ('gripper','tip_left','tip_right')};spec=contact_sensor_specs('right',links,list(self.s['poses']))
  self.assertEqual(len(spec),3)
  for name,value in spec.items():self.assertEqual(value['prim_path'],'{ENV_REGEX_NS}/RightArm'+links[name]);self.assertEqual(len(value['filter_prim_paths_expr']),12)
 def test_aperture_preparation_only_reviewed_route_smooth2s_and_idle_unchanged(self):
  class Controller:
   def __init__(self,*args):pass
  with patch.dict(CONTROLLERS,approved=Controller):
   route=dict(controller='approved',active_hand='left',prepare_aperture_m=.006);p=OpeningCoupon(self.env,self.s,route);previous=np.array(self.s['held_action_14d'])
   for t in np.arange(0,2.01,.05):
    action,_=p.command(float(t));np.testing.assert_array_equal(action[:6],previous[:6]);np.testing.assert_array_equal(action[7:],previous[7:]);self.assertLessEqual(abs(action[6]-previous[6]),.05+1e-12);previous=action
   self.assertAlmostEqual(action[6]*2*.04695,.006)
