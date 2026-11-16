"""Released hold must guard fresh actual and issued state before final credit."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from yam_arena import ik
from yam_arena.constants import READY,FINGER_OPEN
from yam_arena.urdf import quat_xyzw_to_matrix
from config import CENTER
from carton_scene import layout
from robot import ClosureProbe
from check_roll_probe import nominal_poses
from roll_probe import BASES
from test_roll_probe import Tensor


def make_probe():
 poses=nominal_poses()
 for p in layout(top_angle=0.)[0]:poses[p['name']]=(np.array(p['pos'])+CENTER,quat_xyzw_to_matrix([*p['quat'][1:],p['quat'][0]]))
 ready=np.r_[READY,1.,READY,1.]
 world=SimpleNamespace(get_pose_w=lambda n:Tensor([[*poses[n][0],*ik.matrix_to_quat_xyzw(poses[n][1])]]))
 scene={s+'_robot':SimpleNamespace(data=SimpleNamespace(joint_pos=Tensor([[*READY,FINGER_OPEN,FINGER_OPEN]]))) for s in ('left','right')}
 env=SimpleNamespace(_ready=Tensor([ready]),_low=np.r_[ik.LOWER,0.,ik.LOWER,0.],_high=np.r_[ik.UPPER,1.,ik.UPPER,1.],_ids={s+'_robot':(list(range(6)),[6,7]) for s in ('left','right')},rig=SimpleNamespace(bases=BASES),_base=SimpleNamespace(arena_world=world,scene=scene))
 probe=ClosureProbe(env);probe.index=4;probe.stage='park';probe.started=0.;probe.closed_hold=.95
 return probe


class Tests(unittest.TestCase):
 def test_clear_final_hold_uses_real_all315_guards_before_completion(self):
  probe=make_probe();old=probe.previous.copy();action,r=probe.command(.05)
  self.assertEqual(len(probe.geometry.raw),315);self.assertIsNone(r['failure'])
  self.assertTrue(r['clearance_actual']['safe']);self.assertTrue(r['clearance_issued']['safe'])
  self.assertTrue(probe.done);self.assertAlmostEqual(probe.closed_hold,1.)
  np.testing.assert_array_equal(action,old)

 def test_new_actual_or_issued_collision_prevents_hold_credit_and_issuance(self):
  for failing in (1,2):
   with self.subTest(failing='actual' if failing==1 else 'issued'):
    probe=make_probe();old=probe.previous.copy();original=probe.geometry.check;calls=[0]
    def collision(*args,**kwargs):
     g=original(*args,**kwargs);calls[0]+=1
     # Inject ONLY the geometric failure signal to test hold control flow;
     # positive-state geometry above runs all315 real collision pieces.
     if calls[0]==failing:g=dict(g,safe=False,hard_gap_m=-.001,hard_pair=('left','tip_left','north_top'))
     return g
    with patch.object(probe.geometry,'check',side_effect=collision):action,r=probe.command(.05)
    self.assertIn('measured' if failing==1 else 'issued',r['failure']);self.assertTrue(r['not_issued'])
    self.assertFalse(probe.done);self.assertEqual(probe.closed_hold,.95)
    np.testing.assert_array_equal(action,old);np.testing.assert_array_equal(probe.previous,old)

if __name__=='__main__':unittest.main()
