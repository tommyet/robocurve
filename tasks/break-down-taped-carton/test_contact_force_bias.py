"""Plan-B math/conditional certificate; not native force-control validation."""
import unittest
from dataclasses import replace
import numpy as np
from yam_arena import ik
from yam_arena.constants import READY
from contact_force_bias import (force_target,contact_jacobian,contact_point,intended_proxy_certificate,
                                GuardEvidence,STIFFNESS,DAMPING,EFFORT,MAX_JOINT_SLEW_RAD,modeled_existing_effort,measured_force_summary)

class ForceBiasTests(unittest.TestCase):
 def setUp(self):self.q=np.array(READY);self.base=np.array([0.,.305,.75]);self.lever=np.array([.02,-.01,.025]);self.force=np.array([.3,-.2,.1])
 def target(self,force=None,**kw):return force_target(kw.pop('q',self.q),self.force if force is None else force,kw.pop('lever',self.lever),self.base,existing_effort_bound_nm=kw.pop('effort',np.zeros(6)),**kw)
 def test_virtual_work_central_difference(self):
  result=self.target();tau=np.array(result['bias_torque_Nm']);dq=np.array([.2,-.15,.1,.07,.05,-.1])*1e-5
  work=self.force@(contact_point(self.q+dq,self.lever,self.base)-contact_point(self.q-dq,self.lever,self.base))/2
  self.assertAlmostEqual(float(tau@dq),work,places=12)
  np.testing.assert_allclose(result['q_target'],self.q+tau/STIFFNESS,atol=1e-15)
 def test_zero_force_linear_force_and_repeat_does_not_accumulate_bias(self):
  zero=self.target(np.zeros(3));np.testing.assert_array_equal(zero['q_target'],self.q);np.testing.assert_array_equal(zero['bias_torque_Nm'],np.zeros(6))
  a=self.target();b=self.target(2*self.force);again=self.target()
  np.testing.assert_allclose(b['offset_rad'],2*np.array(a['offset_rad']),atol=1e-15);self.assertEqual(a['q_target'],again['q_target'])
 def test_offcentre_contact_includes_correct_rotational_lever(self):
  point=np.array(self.target()['bias_torque_Nm']);tcp=np.array(self.target(lever=np.zeros(3))['bias_torque_Nm'])
  p,R=ik.tcp_pose(self.q,self.base);moment=np.cross(R@self.lever,self.force);omega=[];eps=1e-5
  for i in range(6):
   d=np.zeros(6);d[i]=eps;_,rp=ik.tcp_pose(self.q+d,self.base);_,rm=ik.tcp_pose(self.q-d,self.base);skew=((rp-rm)/(2*eps))@R.T
   omega.append(np.array([skew[2,1],skew[0,2],skew[1,0]]))
  np.testing.assert_allclose(point-tcp,np.array(omega)@moment,atol=2e-11)
  self.assertGreater(np.linalg.norm(point-tcp),1e-4)
 def test_current_effort_model_sums_pd_damping_native_gravity_and_declared_margin(self):
  actual=self.q.copy();nominal=self.q+np.array([.01,-.02,.01,-.02,.01,-.01]);velocity=np.array([.01,-.02,.03,.04,-.05,.06]);gravity=np.array([1,-2,3,-.4,.5,-.6]);margin=np.full(6,.2)
  result=modeled_existing_effort(nominal,actual,velocity,gravity,declared_margin_nm=margin)
  expected=np.abs(STIFFNESS*(nominal-actual))+np.abs(DAMPING*velocity)+np.abs(gravity)+margin
  np.testing.assert_allclose(result['absolute_bound_Nm'],expected)
  self.assertIn('CURRENT',result['scope'])
  with self.assertRaises(ValueError):modeled_existing_effort(nominal,actual,velocity,[np.nan]*6,declared_margin_nm=margin)
  with self.assertRaises(ValueError):modeled_existing_effort(nominal,actual,velocity,gravity,declared_margin_nm=-margin)
 def test_force_summary_uses_opposing_reaction_sign_and_sum_not_cancelling_net(self):
  normals=np.array([[0,1,0],[0,-1,0.]])
  evidence=measured_force_summary([[[0,-2.1,0],[0,2.,0]],[[0,.3,0]]],normals)
  np.testing.assert_allclose(evidence['family_pair_norm_sums_N'],[4.1,.3])
  np.testing.assert_allclose(evidence['signed_resisting_normal_forces_N'],[.1,.3])
 def test_invalid_force_lever_joint_effort_and_augmented_bounds_rejected(self):
  for force in ([np.nan,0,0],[3.0001,0,0],[0,0]):
   with self.assertRaises(ValueError):self.target(force)
  for lever in ([.10001,0,0],[np.nan,0,0]):
   with self.assertRaises(ValueError):self.target(lever=lever)
  for q in (self.q+[np.nan,0,0,0,0,0],ik.UPPER+.001):
   with self.assertRaises(ValueError):self.target(q=q)
  with self.assertRaises(ValueError):self.target(effort=EFFORT-.49)
  q=self.q.copy();q[0]=ik.UPPER[0]-1e-9;jac=contact_jacobian(q,self.lever,self.base);f=jac[:,0]/np.linalg.norm(jac[:,0])
  with self.assertRaisesRegex(ValueError,'augmented target'):self.target(f,q=q)

class CertificateTests(unittest.TestCase):
 def inputs(self,mode='roll'):
  q=np.tile(READY,(2,1));force=np.array([[0,.3,0],[0,-.3,0.]]);base=np.array([[0,.305,.75],[0,-.305,.75]])
  qa=np.array([force_target(q[i],force[i],[0,0,.02],base[i],existing_effort_bound_nm=np.zeros(6))['q_target']for i in range(2)])
  guards=[GuardEvidence(1.,.001,.001,-.0001,True)]*2
  return dict(stage='contact' if mode=='acquire' else 'first_roll',stage_started_s=0.,previous_accepted_force_world=force.copy(),previous_force_was_accepted=[True,True],previous_accepted_time_s=[.95,.95],previous_accepted_ids=[19,19],expected_previous_accepted_ids=[19,19],q_nominal=q,q_augmented=qa,q_actual=q,previous_issued=q,force_world=force,contact_tcp=np.tile([0,0,.02],(2,1)),bases=base,push_normals_world=np.array([[0,1,0],[0,-1,0.]]),existing_effort_bound_nm=np.zeros((2,6)),effort_bound_time_s=1.,effort_bound_verified=True,nominal_guards=guards.copy(),augmented_guards=[replace(g,target_gap_m=-.005)for g in guards],actual_guards=guards.copy(),family_pair_norm_sums_N=[.3,.3],signed_resisting_normal_forces_N=[.2,.2],now_s=1.,force_time_s=1.,native_force_clock_verified=True)
 def test_valid_certificate_only_exempts_issued_intended_proxy(self):
  args=self.inputs();out=intended_proxy_certificate(**args)
  self.assertTrue(out['valid'],out);self.assertTrue(out['replaces_only_issued_intended_depth']);self.assertTrue(out['augmented_intended_proxy_exceeds2mm'])
  for label,field,value in [('actual_guards','target_gap_m',-.00060001),('nominal_guards','target_gap_m',-.00200001),('augmented_guards','hard_gap_m',.00019999),('augmented_guards','other_arm_gap_m',.00019999)]:
   bad=self.inputs();bad[label][0]=replace(bad[label][0],**{field:value});self.assertFalse(intended_proxy_certificate(**bad)['valid'],(label,field))
 def test_fresh_actual_force_clock_signed_normals_and_all_family_forces_required(self):
  for key,value in [('force_time_s',.95),('effort_bound_time_s',.95),('native_force_clock_verified',False),('effort_bound_verified',False),('signed_resisting_normal_forces_N',[.2,.1]),('signed_resisting_normal_forces_N',[.2,-.2]),('family_pair_norm_sums_N',[.3,4.0001]),('family_pair_norm_sums_N',[.1,.3])]:
   bad=self.inputs();bad[key]=value;self.assertFalse(intended_proxy_certificate(**bad)['valid'],key)
  for label in ('actual_guards','nominal_guards','augmented_guards'):
   for field,value in [('time_s',.95),('all_unrelated_checked',False),('target_gap_m',np.nan)]:
    bad=self.inputs();bad[label][0]=replace(bad[label][0],**{field:value});self.assertFalse(intended_proxy_certificate(**bad)['valid'],(label,field))
 def test_acquire_low_force_near_surface_without_roll_contact_evidence(self):
  good=self.inputs('acquire');good['signed_resisting_normal_forces_N']=[0,0];good['family_pair_norm_sums_N']=[0,0]
  self.assertTrue(intended_proxy_certificate(**good)['valid'])
  for field,value in [('target_gap_m',.00050001),('target_gap_m',-.00060001)]:
   bad=self.inputs('acquire');bad['actual_guards'][0]=replace(bad['actual_guards'][0],**{field:value});self.assertFalse(intended_proxy_certificate(**bad)['valid'])
  bad=self.inputs('acquire');bad['force_world']*=2
  bad['q_augmented']=np.array([force_target(bad['q_nominal'][i],bad['force_world'][i],bad['contact_tcp'][i],bad['bases'][i],existing_effort_bound_nm=bad['existing_effort_bound_nm'][i])['q_target']for i in range(2)])
  rejected=intended_proxy_certificate(**bad);self.assertFalse(rejected['valid']);self.assertIn('0.5N',rejected['reasons'][0])
 def test_second_roll_right_only_keeps_left_all_geometry_checks_and_zero_force(self):
  args=self.inputs();args['stage']='second_roll';args['force_world'][0]=0.;args['previous_accepted_force_world'][0]=0.;args['q_augmented'][0]=args['q_nominal'][0]
  args['signed_resisting_normal_forces_N']=[0.,.2];args['family_pair_norm_sums_N']=[0.,.3]
  for label in ('nominal_guards','augmented_guards','actual_guards'):args[label][0]=replace(args[label][0],intended_contact_enabled=False,target_gap_m=10.)
  good=intended_proxy_certificate(**args);self.assertTrue(good['valid'],good);self.assertEqual(good['active_contacts'],[False,True])
  bad={**args,'force_world':args['force_world'].copy()};bad['force_world'][0]=[0,.1,0];self.assertFalse(intended_proxy_certificate(**bad)['valid'])
  bad={**args,'augmented_guards':args['augmented_guards'].copy()};bad['augmented_guards'][0]=replace(bad['augmented_guards'][0],intended_contact_enabled=True);self.assertFalse(intended_proxy_certificate(**bad)['valid'])
  bad={**args,'augmented_guards':args['augmented_guards'].copy()};bad['augmented_guards'][0]=replace(bad['augmented_guards'][0],hard_gap_m=.0001);self.assertFalse(intended_proxy_certificate(**bad)['valid'])
 def release_inputs(self):
  args=self.inputs();args.update(brace_clear_started_s=.5,left_geometric_clear=False)
  args['force_world'][0]*=.5;args['signed_resisting_normal_forces_N']=[0.,.2];args['family_pair_norm_sums_N']=[0.,.3]
  self.reissue(args);return args
 def reissue(self,args):
  args['q_augmented']=np.array([force_target(args['q_nominal'][i],args['force_world'][i],args['contact_tcp'][i],args['bases'][i],existing_effort_bound_nm=args['existing_effort_bound_nm'][i])['q_target']for i in range(2)])
 def test_mixed_left_release_right_push_preserves_independent_force_and_provenance(self):
  args=self.release_inputs();out=intended_proxy_certificate(**args);self.assertTrue(out['valid'],out);self.assertEqual(out['roles'],['release','push']);self.assertEqual(out['release_decay_lambda_by_arm'],[.5,None])
  for multiplier in (2.1,-1.):
   bad=self.release_inputs();bad['force_world'][0]*=multiplier;self.reissue(bad);self.assertFalse(intended_proxy_certificate(**bad)['valid'])
  bad=self.release_inputs();bad['force_world'][0]=[.15,0,0];self.reissue(bad);self.assertFalse(intended_proxy_certificate(**bad)['valid'])
  for key,value in [('previous_force_was_accepted',[False,True]),('force_time_s',.95),('brace_clear_started_s',-1.),('brace_clear_started_s',0.),('previous_accepted_ids',[18,19]),('previous_accepted_time_s',[.9,.95])]:
   bad=self.release_inputs();bad[key]=value;self.assertFalse(intended_proxy_certificate(**bad)['valid'],key)
  bad=self.release_inputs();bad['actual_guards'][0]=replace(bad['actual_guards'][0],target_gap_m=-.0007);self.assertFalse(intended_proxy_certificate(**bad)['valid'])
 def test_zero_release_may_wait_past_deadline_then_becomes_inactive_only_after_measured_clear(self):
  good=self.release_inputs();good['brace_clear_started_s']=0.;good['force_world'][0]=0.;good['previous_accepted_force_world'][0]=0.;self.reissue(good)
  out=intended_proxy_certificate(**good);self.assertTrue(out['valid'],out);self.assertEqual(out['roles'],['release','push'])
  good['left_geometric_clear']=True
  self.assertFalse(intended_proxy_certificate(**good)['valid']) # old intended masks must be removed
  for label in ('nominal_guards','augmented_guards','actual_guards'):good[label][0]=replace(good[label][0],intended_contact_enabled=False,target_gap_m=10.)
  out=intended_proxy_certificate(**good);self.assertTrue(out['valid'],out);self.assertEqual(out['roles'],['inactive','push'])
  bad=self.release_inputs();bad['left_geometric_clear']=True # previous force nonzero: cannot skip release
  out=intended_proxy_certificate(**bad);self.assertTrue(out['valid'],out);self.assertEqual(out['roles'],['release','push'])
 def test_clear_first_and_finish_clear_release_right_without_requiring_contact(self):
  for stage in ('clear_first','finish_clear'):
   good=self.inputs();good.update(stage=stage,stage_started_s=.5);good['force_world'][0]=0.;good['previous_accepted_force_world'][0]=0.;good['force_world'][1]*=.5
   good['signed_resisting_normal_forces_N']=[0.,0.];good['family_pair_norm_sums_N']=[0.,0.]
   for label in ('nominal_guards','augmented_guards','actual_guards'):good[label][0]=replace(good[label][0],intended_contact_enabled=False,target_gap_m=10.)
   self.reissue(good);out=intended_proxy_certificate(**good);self.assertTrue(out['valid'],out);self.assertEqual(out['roles'],['inactive','release']);self.assertEqual(out['release_decay_lambda_by_arm'],[None,.5])
 def test_summed_pair_force_cannot_hide_cancelling_excess(self):
  bad=self.inputs();summary=measured_force_summary([[[0,-2.1,0],[0,2.,0]],[[0,.3,0]]],bad['push_normals_world']);bad.update(summary)
  out=intended_proxy_certificate(**{k:v for k,v in bad.items()if k!='sign_contract'});self.assertFalse(out['valid']);self.assertIn('4N',out['reasons'][0])
 def test_q_slew_effort_and_one_bias_semantics_cannot_be_skipped(self):
  for name in ('q_nominal','q_augmented','q_actual','previous_issued'):
   bad=self.inputs();bad[name]=bad[name].copy();bad[name][0,0]=np.nan;self.assertFalse(intended_proxy_certificate(**bad)['valid'],name)
  bad=self.inputs();bad['q_augmented']=bad['q_nominal']+2*(bad['q_augmented']-bad['q_nominal']);self.assertFalse(intended_proxy_certificate(**bad)['valid'])
  bad=self.inputs();bad['previous_issued']=bad['q_augmented'].copy();bad['previous_issued'][0,0]-=MAX_JOINT_SLEW_RAD+.0001;self.assertFalse(intended_proxy_certificate(**bad)['valid'])
  bad=self.inputs();bad['existing_effort_bound_nm']=np.tile(EFFORT-.49,(2,1));self.assertFalse(intended_proxy_certificate(**bad)['valid'])
  bad=self.inputs();bad['push_normals_world'][0]*=-1;self.assertFalse(intended_proxy_certificate(**bad)['valid'])

if __name__=='__main__':unittest.main()
