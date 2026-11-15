"""Exact command provenance and adversarial observation-isolation contracts."""
import builtins,hashlib,importlib.util,json,sys,tempfile,subprocess,unittest
from pathlib import Path
from types import ModuleType,SimpleNamespace
from unittest.mock import patch
import numpy as np
import recorded_demo as recorded
ROOT=Path(__file__).parent

class ObservationSpy:
 def __init__(self,t):object.__setattr__(self,'t',t);object.__setattr__(self,'reads',[])
 def __getattribute__(self,name):
  if name=='state_time':object.__getattribute__(self,'reads').append(name);return object.__getattribute__(self,'t')
  if name=='reads':return object.__getattribute__(self,name)
  raise AssertionError('forbidden observation access: '+name)
class DenyAll:
 def __getattribute__(self,name):raise AssertionError('forbidden scene/object access: '+name)

def policy():
 modules={n:ModuleType(n)for n in ('inspect_robots','inspect_robots.policy','inspect_robots.types','inspect_robots_yam','inspect_robots_yam.config')}
 modules['inspect_robots.policy'].PolicyInfo=SimpleNamespace;modules['inspect_robots_yam.config'].action_box=lambda low,high:(low,high)
 modules['inspect_robots.types'].Action=SimpleNamespace;modules['inspect_robots.types'].ActionChunk=SimpleNamespace
 return modules

class RecordedDemoTests(unittest.TestCase):
 def test_exact_source_actions_and_mapping_no_fk_or_target_reconstruction(self):
  actions,m=recorded.load_dataset();raw=(ROOT/'recorded_demo_actions.jsonl').read_bytes();rows=[json.loads(x)for x in raw.splitlines()]
  self.assertEqual(hashlib.sha256(raw).hexdigest(),recorded.DATA_SHA256);self.assertEqual(m['teacher_trace_sha256'],recorded.TRACE_SHA256);self.assertEqual(len(rows)-1,779)
  for i,row in enumerate(rows[1:]):self.assertEqual(row['t'],i);np.testing.assert_array_equal(actions[i],row['action'])
  np.testing.assert_array_equal(actions[0][:3],[-.0034353976994346033,.9982577151508708,.9975993017279551])
  self.assertEqual(m['last_action_index'],778);self.assertAlmostEqual(779/20,38.95);self.assertAlmostEqual(m['total_action_steps']/20,40.95)
 def test_779_original_commands_then_exact40_hold_steps_stop_without_edit(self):
  clock=recorded.PlaybackClock()
  for i in range(819):
   command,stop=clock.command(i/20);np.testing.assert_array_equal(command,clock.actions[min(i,778)]);self.assertEqual(stop,i==818)
  self.assertEqual(sum(i>=779 for i in range(819)),40)
  with self.assertRaises(RuntimeError):clock.command(819/20)
  clock.reset();np.testing.assert_array_equal(clock.command(0)[0],clock.actions[0])
 def test_duplicate_observation_does_not_skip_commands_and_arrays_do_not_alias(self):
  p=recorded.PlaybackClock();a,_=p.command(0);b,_=p.command(0);np.testing.assert_array_equal(a,b);a[:]=99
  np.testing.assert_array_equal(p.command(0)[0],b);np.testing.assert_array_equal(p.command(.05)[0],p.actions[1]);self.assertFalse(p.actions.flags.writeable)
 def test_clock_guards_fail_before_output_for_missing_reversed_or_skipped_time(self):
  for t in [None,True,float('nan'),float('inf'),-.05,.0125,.05,120,999]:
   with self.assertRaises((ValueError,TypeError)):recorded.PlaybackClock().command(t)
  p=recorded.PlaybackClock();p.command(0)
  with self.assertRaises(ValueError):p.command(.10)
  p.command(.05)
  with self.assertRaises(ValueError):p.command(0)
 def test_dataset_and_metadata_tampering_rejected(self):
  for name in ('recorded_demo_actions.jsonl','recorded_demo_metadata.json'):
   with tempfile.TemporaryDirectory()as d:
    p=Path(d)
    for n in ('recorded_demo_actions.jsonl','recorded_demo_metadata.json'):(p/n).write_bytes((ROOT/n).read_bytes())
    (p/name).write_bytes((p/name).read_bytes()+b' ')
    with self.assertRaisesRegex(ValueError,'hash mismatch'):recorded.load_dataset(p)
 def test_real_policy_transport_reads_only_clock_never_scene_teacher_or_telemetry(self):
  modules=policy();original_import=builtins.__import__
  def guarded(name,*args,**kwargs):
   if name.split('.')[0]in ('telemetry','demo_policy','yam_arena'):raise AssertionError('forbidden privileged/teacher import: '+name)
   return original_import(name,*args,**kwargs)
  with patch.dict(sys.modules,modules),patch('builtins.__import__',guarded):
   p=recorded.RecordedDemo();p.reset(DenyAll())
   for i in range(819):
    obs=ObservationSpy(i/20);chunk=p.act(obs);self.assertEqual(obs.reads,['state_time']);np.testing.assert_array_equal(chunk.actions[0].data,p.clock.actions[min(i,778)]);self.assertEqual(chunk.control_hz,20.)
   self.assertTrue(chunk.actions[0].meta['request_stop'])
 def test_cli_rejects_physics_stage_and_solver_mismatch_before_runtime(self):
  for extra in [[],['--physics-hz','960','--stage','press'],['--physics-hz','960','--body-solver-32-8']]:
   with tempfile.TemporaryDirectory()as d:
    out=Path(d)/'not-created';r=subprocess.run([sys.executable,str(ROOT/'run.py'),'--policy','recorded-demo','--no-video','--log-dir',str(out),*extra],capture_output=True,text=True);self.assertEqual(r.returncode,2);self.assertIn('recorded-demo requires',r.stderr);self.assertFalse(out.exists())
 def test_cli_valid_recorded_no_video_passes_validation_without_teacher_import(self):
  # Stop at runtime import; the subprocess has no inspect_robots installed.
  with tempfile.TemporaryDirectory()as d:
   out=Path(d)/'prepared';r=subprocess.run([sys.executable,str(ROOT/'run.py'),'--policy','recorded-demo','--no-video','--physics-hz','960','--log-dir',str(out)],capture_output=True,text=True)
   self.assertNotEqual(r.returncode,2);self.assertTrue(out.exists());sources=json.loads((out/'source-sha256.json').read_text());self.assertEqual(sources['recorded_demo_actions.jsonl'],recorded.DATA_SHA256);self.assertNotIn('demo_policy.py',r.stderr)
