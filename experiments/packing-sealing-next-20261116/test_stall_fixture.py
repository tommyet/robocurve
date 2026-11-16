"""Independent final prestate315 guard, no geometry/IK mocks."""
import json,sys,unittest
from pathlib import Path
from types import SimpleNamespace
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tasks/pack-and-tape-carton'))
from robot import ClosureProbe
from test_roll_probe import Tensor
from roll_probe import BASES
from yam_arena import ik
from yam_arena.constants import READY
F=json.loads(Path(__file__).with_name('closure002-fixture-report.json').read_text())
def probe():
 f=F['prestate'];hands=f['hands'];ready=np.r_[READY,1.,READY,1.];scene={s+'_robot':SimpleNamespace(data=SimpleNamespace(joint_pos=Tensor([[*hands[i]['joints'],*hands[i]['finger_joints']]])))for i,s in enumerate(('left','right'))};env=SimpleNamespace(_ready=Tensor([ready]),_low=np.r_[ik.LOWER,0.,ik.LOWER,0.],_high=np.r_[ik.UPPER,1.,ik.UPPER,1.],_ids={s+'_robot':(list(range(6)),[6,7])for s in('left','right')},rig=SimpleNamespace(bases=BASES),_base=SimpleNamespace(arena_world=SimpleNamespace(get_pose_w=lambda n:Tensor([f['poses'][n]])),scene=scene));p=ClosureProbe(env);state=f['planner'].copy()
 for k in ('bias','startp','startr','contact_offset','rotation_offset'):
  if state.get(k)is not None:state[k]=np.asarray(state[k])
 p.restore_candidate(state);p.previous=np.asarray(f['previous_action']);p.last_time=F['command_time_s']-.05;return p
class StallTests(unittest.TestCase):
 def test_real_final_guard_blocks_only_intended_proxy_advance(self):
  p=probe();before=p.previous.copy();bias=p.bias.copy();angle=p.command_angle;_,r=p.command(F['command_time_s'])
  self.assertEqual(len(p.geometry.raw),315);self.assertIsNone(r['failure']);self.assertEqual(r['advance_fraction'],0)
  self.assertTrue(r['clearance_actual']['safe']);self.assertGreater(r['clearance_actual']['target_gap_m'],-.00003);self.assertTrue(r['clearance_previous']['safe'])
  for t in r['advance_trials']:
   c=t['clearance'];self.assertFalse(c['safe']);self.assertGreater(c['hard_gap_m'],.001);self.assertGreater(c['other_arm_gap_m'],.29);self.assertLess(c['target_gap_m'],-.001);self.assertEqual(tuple(c['target_pair']),('left','tip_left','east_top'))
  self.assertAlmostEqual(r['advance_trials'][-1]['clearance']['target_gap_m'],-.0010366073,places=8);np.testing.assert_array_equal(p.previous,before);np.testing.assert_array_equal(p.bias,bias);self.assertEqual(p.command_angle,angle)
 def test_observed_engagement_deadline_survives_rejected_advances(self):
  p=probe();_,r=p.command(p.started+3.01);self.assertIn('did not produce measured hinge motion',r['failure'])
if __name__=='__main__':unittest.main()
