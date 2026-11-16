import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('budget',Path(__file__).with_name('brev_gpu_budget.py'));budget=importlib.util.module_from_spec(spec);spec.loader.exec_module(budget)
class Tests(unittest.TestCase):
 def test_counts_boot_idle_and_shutdown_in_same_window(self):
  config=dict(instance='vm',start_epoch=1000,deadline_epoch=8200,stop_epoch=7600)
  self.assertEqual(budget.status(config,1300)['elapsed_minutes'],5)
  self.assertFalse(budget.status(config,7599)['stop_due']);self.assertTrue(budget.status(config,7600)['stop_due']);self.assertEqual(budget.status(config,8201)['remaining_minutes'],0)
 def test_provider_stop_ack_is_not_stopped(self):
  self.assertFalse(budget.is_stopped('vm STOPPING NOTREADY -','vm'));self.assertTrue(budget.is_stopped('\x1b[32mvm STOPPED\x1b[0m NOTREADY -','vm'));self.assertFalse(budget.is_stopped('different-vm STOPPED','vm'))
if __name__=='__main__':unittest.main()
