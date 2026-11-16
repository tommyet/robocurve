"""Invalid diagnostic requests must fail before creating output or launching Isaac."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

class RunCliTests(unittest.TestCase):
 def test_invalid_budget_or_controller_mode_does_not_create_run(self):
  script=Path(__file__).with_name('run.py')
  with tempfile.TemporaryDirectory() as directory:
   for args,reason in [(['--max-steps','0'],'--max-steps must'),(['--max-steps','3601'],'--max-steps must'),(['--mode','closure-probe','--closure-controller','face-push','--max-steps','6001'],'--max-steps must'),(['--closure-controller','face-push'],'requires --mode closure-probe'),(['--closure-flaps','1'],'--closure-flaps requires'),(['--closure-flaps','0'],'invalid choice')]:
    destination=Path(directory)/'never-created'
    result=subprocess.run([sys.executable,str(script),'--out',str(destination),*args],capture_output=True,text=True)
    with self.subTest(args=args):
     self.assertEqual(result.returncode,2)
     self.assertIn(reason,result.stderr)
     self.assertFalse(destination.exists())

if __name__=='__main__':unittest.main()
