"""Prevent a new GPU window from resetting an already consumed allowance."""
import datetime,importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('budget',Path(__file__).with_name('brev_gpu_budget.py'));budget=importlib.util.module_from_spec(spec);spec.loader.exec_module(budget)
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
 def ledger(self,name,start=1000,minutes=32.650599185625715):
  p=self.root/name;p.mkdir();(p/'window.json').write_text(json.dumps({'instance':'vm','start_epoch':start}));(p/'status.json').write_text(json.dumps({'instance':'vm','provider_state':'STOPPED','stopped_utc':budget.utc(start+60*minutes),'total_window_minutes':minutes}));return p
 def test_subtracts_prior_and_refuses_overspend_before_arming(self):
  p=self.ledger('prior');x=budget.aggregate_allowance('vm',60,[p]);self.assertAlmostEqual(x['remaining_minutes'],27.349400814,places=7)
  out=self.root/'new'
  with self.assertRaisesRegex(ValueError,'exceeds aggregate'):budget.arm(out,'vm',28,4,60,[p])
  self.assertFalse(out.exists())
 def test_rejects_unverified_or_inconsistent_prior(self):
  p=self.ledger('prior');f=p/'status.json';original=json.loads(f.read_text())
  for change in [{'provider_state':'STOPPING'},{'instance':'other'},{'total_window_minutes':1},{'total_window_minutes':float('nan')},{'stopped_utc':'2026-11-16T16:26:32'}]:
   f.write_text(json.dumps(dict(original,**change)))
   with self.assertRaises(ValueError):budget.aggregate_allowance('vm',60,[p])
 def test_rejects_duplicate_and_overlapping_windows(self):
  a=self.ledger('a');b=self.ledger('b',start=1100)
  for windows in [[a,a],[a,b]]:
   with self.assertRaises(ValueError):budget.aggregate_allowance('vm',60,windows)
 def test_keeps_disjoint_windows_and_exhausted_budget(self):
  a=self.ledger('a',minutes=10);b=self.ledger('b',start=1700,minutes=20)
  self.assertEqual(budget.aggregate_allowance('vm',25,[a,b])['remaining_minutes'],0)
  self.assertEqual(budget.aggregate_allowance('vm',60,[a,b])['remaining_minutes'],30)
if __name__=='__main__':unittest.main()
