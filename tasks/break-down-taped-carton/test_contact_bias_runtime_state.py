"""CPU bookkeeping/conditional math only; guards below are synthetic fixtures."""
import unittest
from dataclasses import replace
import numpy as np
from yam_arena.constants import READY
from contact_force_bias import GuardEvidence,force_target
from contact_bias_runtime_state import ForceLedger,StickyReleaseEvents,canonical_target

class Tests(unittest.TestCase):
 def setUp(self):
  self.nominal=np.r_[READY,.255,READY,.255];self.ledger=ForceLedger(self.nominal)
 def seed(self):
  guards=[GuardEvidence(0.,.001,.001,0.,True)]*2
  emitted=self.ledger.queue_ordinary_zero(0.,self.nominal,actual_guards=guards,nominal_guards=guards,issued_guards=guards,measurement_clock_verified=True,effort_readback_verified=True)
  self.assertIsNone(self.ledger.accepted);self.ledger.acknowledge_successful_step(0.,emitted)
 def context(self):
  from test_contact_force_bias import CertificateTests
  ctx=CertificateTests().inputs('acquire');ctx['now_s']=ctx['force_time_s']=ctx['effort_bound_time_s']=.05
  for label in ('nominal_guards','actual_guards','augmented_guards'):ctx[label]=[replace(g,time_s=.05) for g in ctx[label]]
  return ctx
 def test_nominal_and_augmented_stay_separate_no_double_force(self):
  self.seed();ctx=self.context();issued=self.ledger.queue_certified(.05,self.nominal,ctx)
  self.assertIsNotNone(self.ledger.pending);np.testing.assert_array_equal(self.ledger.accepted.nominal,self.nominal)
  self.ledger.acknowledge_successful_step(.05,issued)
  np.testing.assert_array_equal(self.ledger.accepted.nominal,self.nominal);self.assertGreater(np.max(abs(self.ledger.accepted.issued-self.nominal)),1e-7)
  again=canonical_target(self.ledger.accepted.nominal,ctx['force_world'],ctx['contact_tcp'],ctx['bases'],ctx['existing_effort_bound_nm'])
  np.testing.assert_array_equal(again,self.ledger.accepted.issued)
 def test_failed_or_missing_step_never_creates_accepted_force_ids(self):
  self.seed();ids=self.ledger.accepted.ids;issued=self.ledger.queue_certified(.05,self.nominal,self.context())
  self.assertEqual(self.ledger.accepted.ids,ids)
  with self.assertRaisesRegex(ValueError,'ACK'):self.ledger.queue_certified(.1,self.nominal,self.context())
  wrong=issued.copy();wrong[0]=np.nextafter(wrong[0],np.float32(np.inf))
  with self.assertRaisesRegex(ValueError,'bits'):self.ledger.acknowledge_successful_step(.05,wrong)
  with self.assertRaisesRegex(ValueError,'time'):self.ledger.acknowledge_successful_step(.1,issued)
  self.assertEqual(self.ledger.accepted.ids,ids);self.ledger.acknowledge_successful_step(.05,issued);self.assertEqual(self.ledger.accepted.ids,(2,2))
 def test_caller_cannot_forge_accepted_ids_or_skip_certificate(self):
  self.seed();ctx=self.context();ctx['previous_accepted_ids']=[999,999];ctx['expected_previous_accepted_ids']=[999,999]
  issued=self.ledger.queue_certified(.05,self.nominal,ctx);self.ledger.acknowledge_successful_step(.05,issued);self.assertEqual(self.ledger.accepted.ids,(2,2))
  ctx=self.context();ctx['force_time_s']=.01
  with self.assertRaises(ValueError):self.ledger.queue_certified(.1,self.nominal,ctx)
 def test_ordinary_zero_never_uses_an_intended_proxy_exception(self):
  g=[GuardEvidence(0.,.001,.001,-.0021,True)]*2
  with self.assertRaisesRegex(ValueError,'ordinary guard'):self.ledger.queue_ordinary_zero(0.,self.nominal,actual_guards=g,nominal_guards=g,issued_guards=g,measurement_clock_verified=True,effort_readback_verified=True)
  self.seed();issued=self.ledger.queue_certified(.05,self.nominal,self.context());self.ledger.acknowledge_successful_step(.05,issued)
  g=[GuardEvidence(.1,.001,.001,0.,True)]*2
  with self.assertRaisesRegex(ValueError,'certified release'):self.ledger.queue_ordinary_zero(.1,self.nominal,actual_guards=g,nominal_guards=g,issued_guards=g,measurement_clock_verified=True,effort_readback_verified=True)
 def test_nominal_backtrack_recomputes_bias_and_actual_float32_bits(self):
  ctx=self.context();a=canonical_target(self.nominal,ctx['force_world'],ctx['contact_tcp'],ctx['bases'],ctx['existing_effort_bound_nm'])
  shifted=self.nominal.copy();shifted[1]+=.01
  b=canonical_target(shifted,.5*ctx['force_world'],ctx['contact_tcp'],ctx['bases'],ctx['existing_effort_bound_nm'])
  for i in (0,1):
   expected=np.array(force_target(shifted[i*7:i*7+6],.5*ctx['force_world'][i],ctx['contact_tcp'][i],ctx['bases'][i],existing_effort_bound_nm=ctx['existing_effort_bound_nm'][i])['q_target'],dtype=np.float32).astype(float)
   np.testing.assert_array_equal(b[i*7:i*7+6],expected)
  self.assertFalse(np.array_equal(b,(a+shifted)/2))
 def test_sticky_observed_events_do_not_restart_on_planner_retry(self):
  e=StickyReleaseEvents();e.observe(2.,stage='first_roll',stage_started_s=0.,angle_deg=26.,com_beyond_support_m=0.)
  e.observe(2.5,stage='first_roll',stage_started_s=0.,angle_deg=46.,com_beyond_support_m=.004)
  for t in (2.55,2.6,2.65):e.observe(t,stage='first_roll',stage_started_s=0.,angle_deg=46.,com_beyond_support_m=.004)
  self.assertEqual(e.left_start,2.);self.assertEqual(e.right_first_start,2.5)
  prior=np.array([.2,-.3,.1]);f=e.decay_exact_world(prior,2.45,2.55,e.right_first_start)
  self.assertGreater(np.linalg.norm(f),0);self.assertLess(np.linalg.norm(f),np.linalg.norm(prior));np.testing.assert_allclose(np.cross(f,prior),0.,atol=1e-15)
  np.testing.assert_array_equal(e.decay_exact_world(prior,2.45,3.5,e.right_first_start),np.zeros(3))
  # LEFT decay is independent: it is already zero while RIGHT still releases.
  np.testing.assert_array_equal(e.decay_exact_world(prior,2.45,3.1,e.left_start),np.zeros(3))

if __name__=='__main__':unittest.main()
