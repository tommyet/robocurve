import unittest
import numpy as np
from closure_contacts import summarize,TARGETS,Reader
from types import SimpleNamespace
class Tests(unittest.TestCase):
 def test_force_family_sum_does_not_rely_on_filter_order(self):
  a=np.arange(6*len(TARGETS),dtype=float).reshape(1,2,len(TARGETS),3)/10
  x=summarize(a,['tip_left','tip_right']);y=summarize(a[:,:,::-1],['tip_left','tip_right'])
  np.testing.assert_allclose(x['family_normal_force_on_fingertips_w_N'],y['family_normal_force_on_fingertips_w_N'])
  self.assertFalse(x['individual_filter_column_order_native_verified'])
 def test_opposed_sensor_reactions_remain_opposed(self):
  a=np.zeros((1,2,len(TARGETS),3));a[0,0,0,1]=2.
  l=summarize(a,['tip_left','tip_right']);r=summarize(-a,['tip_right','tip_left'])
  self.assertLess(np.dot(l['family_normal_force_on_fingertips_w_N'],r['family_normal_force_on_fingertips_w_N']),0.)
 def test_balanced_clamp_has_nonzero_force_magnitudes_even_if_net_zero(self):
  a=np.zeros((1,2,len(TARGETS),3));a[0,0,0,0]=2.;a[0,1,0,0]=-2.
  r=summarize(a,['tip_left','tip_right']);self.assertEqual(r['family_normal_force_norm_N'],0.);self.assertEqual(r['family_sum_of_normal_force_magnitudes_N'],4.)
 def test_bad_shape_wrong_body_and_nonfinite_rejected(self):
  a=np.zeros((1,2,len(TARGETS),3))
  for value,names in [(a[:,:,:3],['tip_left','tip_right']),(a,['base','tip_left']),(a+np.nan,['tip_left','tip_right'])]:
   with self.assertRaises(ValueError):summarize(value,names)
class ReaderTests(unittest.TestCase):
 def make(self):
  sensors={side:SimpleNamespace(data=SimpleNamespace(force_matrix_w=np.zeros((1,2,len(TARGETS),3))),body_names=['tip_left','tip_right'],_timestamp=np.array([0.]),_timestamp_last_update=np.array([0.]))for side in ('left','right')}
  base=SimpleNamespace(scene={s+'_carton_contacts':v for s,v in sensors.items()},sim=SimpleNamespace(get_physics_dt=lambda:1/240))
  return Reader(base),sensors
 def test_repeated_pre_post_reads_do_not_create_new_measurements(self):
  r,s=self.make();a=r.read(0.,'pre_action');b=r.read(0.,'post_step');self.assertEqual(a['sample_id'],b['sample_id'])
  for x in s.values():x._timestamp[:]=.05;x._timestamp_last_update[:]=.05
  c=r.read(.05,'post_step');d=r.read(.05,'pre_action');self.assertEqual(c['sample_id'],a['sample_id']+1);self.assertEqual(c['sample_id'],d['sample_id']);self.assertTrue(d['clock_verified'])
 def test_request_time_cannot_make_stale_native_data_fresh(self):
  r,s=self.make();r.read(0.)
  with self.assertRaisesRegex(ValueError,'stale'):r.read(.05)
 def test_unupdated_unsynchronised_and_reset_clocks_fail(self):
  for mode in ('unupdated','unsync','reset'):
   r,s=self.make();r.read(0.)
   for x in s.values():x._timestamp[:]=.05;x._timestamp_last_update[:]=.05
   if mode=='unupdated':s['left']._timestamp_last_update[:]=0.
   elif mode=='unsync':s['right']._timestamp[:]=.04;s['right']._timestamp_last_update[:]=.04
   else:
    r.read(.05)
    for x in s.values():x._timestamp[:]=0.;x._timestamp_last_update[:]=0.
   with self.assertRaises(ValueError):r.read(.1 if mode=='reset'else .05)
class SingletonTests(unittest.TestCase):
 def make(self,target='east_top'):
  sensors={}
  for side,root in [('left','LeftArm'),('right','RightArm')]:
   sensors[side]=SimpleNamespace(data=SimpleNamespace(force_matrix_w=np.zeros((1,2,1,3))),body_names=['tip_left','tip_right'],_timestamp=np.array([0.]),_timestamp_last_update=np.array([0.]),contact_view=SimpleNamespace(sensor_count=2,filter_count=1,filter_paths=[['/World/envs/env_0/'+target]]*2,sensor_paths=['/World/envs/env_0/'+root+'/gripper/'+n for n in ['tip_left','tip_right']]))
  base=SimpleNamespace(scene={s+'_closure_'+target+'_contacts':v for s,v in sensors.items()},sim=SimpleNamespace(get_physics_dt=lambda:1/240))
  return Reader(base,target=target),sensors
 def test_selected_target_and_force_rows_verified(self):
  r,s=self.make();s['left'].data.force_matrix_w[0,1,0,2]=.08
  out=r.read(0.)
  self.assertEqual(out['selected_target'],'east_top');self.assertTrue(out['native_filter_target_verified'])
  left=out['sides']['left'];self.assertTrue(left['target_binding']['native_verified']);self.assertTrue(left['individual_filter_column_order_native_verified'])
  self.assertEqual(left['body_names'][1],'tip_right');self.assertEqual(left['normal_force_matrix_w'][1][0][2],.08)
 def test_wrong_missing_duplicate_and_reordered_bindings_fail(self):
  for mode in ('target','missing','duplicate','arm','order','empty_row','duplicate_column','count'):
   r,s=self.make();sensor=s['left']
   if mode=='target':sensor.contact_view.filter_paths=[['/World/envs/env_0/west_top']]
   elif mode=='missing':del sensor.contact_view
   elif mode=='duplicate':sensor.contact_view.sensor_paths=[sensor.contact_view.sensor_paths[0]]*2
   elif mode=='arm':sensor.contact_view.sensor_paths=[p.replace('LeftArm','RightArm') for p in sensor.contact_view.sensor_paths]
   elif mode=='order':sensor.contact_view.sensor_paths.reverse()
   elif mode=='empty_row':sensor.contact_view.filter_paths[1]=[]
   elif mode=='duplicate_column':sensor.contact_view.filter_paths[0]*=2
   else:sensor.contact_view.filter_count=2
   with self.subTest(mode=mode),self.assertRaises(ValueError):r.read(0.)
 def test_selected_sample_must_be_fresh(self):
  r,s=self.make();first=r.read(0.);self.assertEqual(first['sample_id'],r.read(0.)['sample_id'])
  with self.assertRaisesRegex(ValueError,'stale'):r.read(.05)
 def test_first_late_sample_requires_verified_anchor(self):
  r,s=self.make()
  with self.assertRaisesRegex(ValueError,'anchor'):r.read(20.)
 def test_family_anchor_cannot_make_stale_selected_sample_fresh(self):
  r,s=self.make();base=r.base
  for side in ('left','right'):base.scene[side+'_carton_contacts']=SimpleNamespace(data=SimpleNamespace(force_matrix_w=np.zeros((1,2,len(TARGETS),3))),body_names=['tip_left','tip_right'],_timestamp=np.array([0.]),_timestamp_last_update=np.array([0.]))
  parent=Reader(base);parent.read(0.)
  for side in ('left','right'):
   sensor=base.scene[side+'_carton_contacts'];sensor._timestamp[:]=.05;sensor._timestamp_last_update[:]=.05
  with self.assertRaisesRegex(ValueError,'family clock'):parent.read(.05,target='east_top')
 def test_each_target_has_its_own_clock_history(self):
  a,sa=self.make('east_top');b,sb=self.make('west_top')
  base=SimpleNamespace(scene={**a.base.scene,**b.base.scene},sim=a.base.sim)
  # Parent family data is independently diagnostic, not an acquisition signal.
  for side in ('left','right'):base.scene[side+'_carton_contacts']=SimpleNamespace(data=SimpleNamespace(force_matrix_w=np.zeros((1,2,len(TARGETS),3))),body_names=['tip_left','tip_right'],_timestamp=np.array([0.]),_timestamp_last_update=np.array([0.]))
  parent=Reader(base);east=parent.read(0.,target='east_top');west=parent.read(0.,target='west_top')
  self.assertEqual(east['sample_id'],1);self.assertEqual(west['sample_id'],1)
  for sensor in [*sa.values(),base.scene['left_carton_contacts'],base.scene['right_carton_contacts']]:sensor._timestamp[:]=.05;sensor._timestamp_last_update[:]=.05
  self.assertEqual(parent.read(.05,target='east_top')['sample_id'],2)
  for sensor in sb.values():sensor._timestamp[:]=.05;sensor._timestamp_last_update[:]=.05
  self.assertEqual(parent.read(.05,target='west_top')['sample_id'],2)
if __name__=='__main__':unittest.main()

