"""Regression tests for causal cuts and scoring loopholes."""
import unittest
from copy import deepcopy
from config import *
from scoring import UnboxScorer

def sample(t=0.,x=None):
    return dict(time=t,tip=[SEAM[0] if x is None else x,0.,LID_Z],
                cutter=dict(pos=list(CUTTER_START),speed=0.),
                item=dict(pos=[*CENTER,TOP+.023],speed=0.),held=True,
                blade_down=1.,flap_angles=[0.,0.],item_released=False)

def cut_all(tracker):
    for i in range(211): tracker.update(sample(i*.05,SEAM[0]+i*.001))

class TapeTests(unittest.TestCase):
    def test_initial_zero(self):
        t=UnboxScorer(); t.update(sample()); self.assertEqual(t.value,0)
    def test_complete_sweep(self):
        t=UnboxScorer(); cut_all(t); self.assertEqual(sum(t.cut),21); self.assertEqual(t.value,.25)
    def test_stationary_tip_not_cut(self):
        t=UnboxScorer()
        for i in range(100): t.update(sample(i*.05))
        self.assertEqual(sum(t.cut),0)
    def test_unheld_wrong_height_wrong_orientation(self):
        for mode in ['held','height','orientation']:
            t=UnboxScorer()
            for i in range(211):
                s=sample(i*.05,SEAM[0]+i*.001)
                if mode=='held': s['held']=False
                if mode=='height': s['tip'][2]+=.02
                if mode=='orientation': s['blade_down']=0
                t.update(s)
            self.assertEqual(sum(t.cut),0)
    def test_jump_cannot_cut(self):
        t=UnboxScorer(); t.update(sample()); t.update(sample(.05,SEAM[1])); self.assertFalse(any(t.cut))
    def test_air_jump_cannot_bridge(self):
        t=UnboxScorer(); t.update(sample())
        s=sample(.05,SEAM[1]); s['tip'][2]+=.1; t.update(s)
        t.update(sample(.1,SEAM[1])); self.assertFalse(any(t.cut))
    def test_reverse_sweep(self):
        t=UnboxScorer()
        for i in range(211): t.update(sample(i*.05,SEAM[1]-i*.001))
        self.assertEqual(t.value,.25)
    def test_forcing_sealed_flap_invalidates(self):
        t=UnboxScorer(); s=sample(); s['flap_angles']=[45,0]; t.update(s)
        cut_all(t); self.assertTrue(t.invalid); self.assertEqual(t.value,0)
    def test_full_score_requires_placement_return_release_and_hold(self):
        t=UnboxScorer(); cut_all(t)
        s=sample(11); s['flap_angles']=[100,100]; s['held']=False
        t.update(s); self.assertEqual(t.value,.5)
        s['item']['pos']=[*DESTINATION,TOP+.022]; s['item_released']=True
        t.update(s); self.assertEqual(t.value,.5)
        s['time']=12.01; t.update(s); self.assertEqual(t.value,1)
        s['item']['pos'][2]=TOP-.1; s['time']=12.1; t.update(s); self.assertEqual(t.value,0)
    def test_closed_flaps_no_full_score(self):
        t=UnboxScorer(); cut_all(t)
        s=sample(11); s['held']=False; s['flap_angles']=[100,100]; t.update(s)
        s['flap_angles']=[0,0]; s['item']['pos']=[*DESTINATION,TOP+.022];s['item_released']=True
        for i in range(40): s['time']=12+i*.05;t.update(s)
        self.assertEqual(t.value,.5)

if __name__=='__main__': unittest.main()
