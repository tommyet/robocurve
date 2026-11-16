"""Pinned offline aiming keeps timing, jaws and online observation isolation."""
import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import aimed_demo as aimed
import recorded_demo
from test_recorded_demo import ObservationSpy,DenyAll,policy

class AimedTests(unittest.TestCase):
 def test_preserves_prefix_jaws_timing_and_bounds(self):
  a,m=aimed.load_dataset();old,_=recorded_demo.load_dataset()
  np.testing.assert_array_equal(a[:531],old[:531]);np.testing.assert_array_equal(a[:,[6,13]],old[:,[6,13]])
  self.assertFalse(a.flags.writeable);self.assertEqual(m['total_action_steps'],819);self.assertFalse(m['native_validated'])
  self.assertTrue(np.all(a>=m['action_lower']));self.assertTrue(np.all(a<=m['action_upper']))
 def test_all_clock_ticks_then40_holds(self):
  c=aimed.PlaybackClock()
  for i in range(819):
   a,stop=c.command(i/20);np.testing.assert_array_equal(a,c.actions[min(i,778)]);self.assertEqual(stop,i==818)
  with self.assertRaises(RuntimeError):c.command(819/20)
 def test_invalid_clock_and_no_alias(self):
  for t in [None,True,float('nan'),-.05,.0125,.05,120]:
   with self.assertRaises(ValueError):aimed.PlaybackClock().command(t)
  c=aimed.PlaybackClock();a,_=c.command(0);a[:]=999;self.assertFalse(np.any(c.command(0)[0]==999))
  with self.assertRaises(ValueError):c.command(.1)
 def test_hash_tamper_rejected(self):
  for name in ['aimed_demo_actions.jsonl','aimed_demo_metadata.json']:
   with tempfile.TemporaryDirectory()as d:
    p=Path(d)
    for n in ['aimed_demo_actions.jsonl','aimed_demo_metadata.json']:(p/n).write_bytes((Path(__file__).parent/n).read_bytes())
    (p/name).write_bytes((p/name).read_bytes()+b' ')
    with self.assertRaisesRegex(ValueError,'hash mismatch'):aimed.load_dataset(p)
 def test_online_only_clock_access(self):
  with patch.dict(sys.modules,policy()):
   p=aimed.AimedDemo();p.reset(DenyAll());obs=ObservationSpy(0);out=p.act(obs)
   self.assertEqual(obs.reads,['state_time']);np.testing.assert_array_equal(out.actions[0].data,p.clock.actions[0])
 def test_all_compiled_fk_offsets_and_orientations(self):
  from yam_arena import ik
  a,_=aimed.load_dataset();old,_=recorded_demo.load_dataset()
  for i in range(531,779):
   shift=np.array([.022,-.002,0])*ik.smoothstep((i-530)/80)
   for arm,base in [(0,np.array([0,.305,.75])),(1,np.array([0,-.305,.75]))]:
    sl=slice(arm*7,arm*7+6);p,R=ik.tcp_pose(old[i,sl],base);q,S=ik.tcp_pose(a[i,sl],base)
    np.testing.assert_allclose(q,p+shift,atol=2e-7,rtol=0);np.testing.assert_allclose(S,R,atol=2e-6,rtol=0)
if __name__=='__main__':unittest.main()
