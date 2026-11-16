"""The revised limit is predeclared and applies to both model and demo."""
import subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).parent
class Tests(unittest.TestCase):
 def test_model_and_demo_reject_old_budget_before_runtime(self):
  for policy in ['dream','aimed-demo']:
   with tempfile.TemporaryDirectory()as folder:
    out=Path(folder)/'not-created';r=subprocess.run([sys.executable,str(ROOT/'run.py'),'--policy',policy,'--physics-hz','960','--max-steps','1201','--log-dir',str(out)],capture_output=True,text=True)
    self.assertEqual(r.returncode,2);self.assertIn('1..1200',r.stderr);self.assertFalse(out.exists())
if __name__=='__main__':unittest.main()
