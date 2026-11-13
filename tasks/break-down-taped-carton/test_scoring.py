import unittest
from model import BladeCoverage,CUT_PATHS
from scoring import BreakdownScorer


def state(**changes):
    s=dict(time=0.,blade_tip_local=(0.,0.,-.001),blade_alignment=1.,cutter_held=False,
           bottom_angles=[0.]*4,top_angles=[160.]*4,crease_separation=0.,
           min_height=0.,max_height=.25,carton_speed=0.,cutter_parked=False,hands_clear=False)
    s.update(changes);return s


def cut_all(t,s):
    for _,a,b in CUT_PATHS:
        s.update(cutter_held=False);s['time']+=.05;t.update(s)
        for step in range(111):
            s.update(cutter_held=True,blade_tip_local=tuple(x+(y-x)*step/110 for x,y in zip(a,b)))
            s['time']+=.05;t.update(s)


class Tests(unittest.TestCase):
    def test_start(self):
        t=BreakdownScorer();t.update(state());self.assertEqual(t.value,0.)

    def test_three_cut_paths_required(self):
        t=BreakdownScorer();s=state();t.update(s);cut_all(t,s)
        self.assertTrue(t.coverage.complete);self.assertEqual(t.value,.25)

    def test_forced_open_latches_failure(self):
        t=BreakdownScorer();s=state(bottom_angles=[20.,0.,0.,0.]);t.update(s)
        s['bottom_angles']=[0.]*4;cut_all(t,s)
        self.assertEqual(t.value,0.);self.assertIn('sealed',t.invalid)

    def test_knife_must_be_held(self):
        c=BladeCoverage()
        for i in range(101):c.update((-.11+i*.0022,0.,0.),1.,False,.05)
        self.assertFalse(c.cut)

    def test_teleported_knife_cannot_cut(self):
        c=BladeCoverage();c.update((-.11,0.,0.),1.,True,.05)
        c.update((.11,0.,0.),1.,True,.05);self.assertFalse(c.cut)

    def test_wrong_depth_no_cut(self):
        c=BladeCoverage()
        for i in range(101):c.update((-.11+i*.0022,0.,.01),1.,True,.05)
        self.assertFalse(c.cut)

    def test_wrong_blade_orientation_no_cut(self):
        c=BladeCoverage()
        for i in range(101):c.update((-.11+i*.0022,0.,0.),.5,True,.05)
        self.assertFalse(c.cut)

    def test_full_score_requires_eight_flaps_and_flat_released_hold(self):
        t=BreakdownScorer();s=state();t.update(s);cut_all(t,s)
        s.update(bottom_angles=[160.]*4,min_height=.002,max_height=.022,
                 cutter_held=False,cutter_parked=True,hands_clear=True)
        for _ in range(21):s['time']+=.05;t.update(s)
        self.assertEqual(t.value,1.)
        s['top_angles'][0]=100.;s['time']+=.05;t.update(s)
        self.assertEqual(t.value,.5)

    def test_destroying_carton_never_counts(self):
        t=BreakdownScorer();s=state();t.update(s);cut_all(t,s)
        s.update(bottom_angles=[160.]*4,crease_separation=.02,min_height=0.,max_height=.02,
                 cutter_parked=True,hands_clear=True)
        for _ in range(21):s['time']+=.05;t.update(s)
        self.assertEqual(t.value,0.)

    def test_flat_bounding_box_alone_is_not_success(self):
        t=BreakdownScorer();t.update(state(max_height=.02,cutter_parked=True,hands_clear=True))
        self.assertEqual(t.value,0.)

if __name__=='__main__':unittest.main()
