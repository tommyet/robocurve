"""Outcome and exploit checks; synthetic states do not prove robot feasibility."""
import copy
import math
import unittest
from config import *
from scoring import SprayScorer


def sample(**changes):
    s=dict(time=0.,can=CAN_START,cap=CAP_START,button_travel=0.,
           nozzle=(TARGET_X-.20,TARGET_CENTER[0],TARGET_CENTER[1]),axis=(1.,0.,0.),
           can_speed=0.,cap_speed=0.,upright=1.,cap_detached=False,hands_clear=False)
    s.update(changes)
    return s


class ScoringTests(unittest.TestCase):
    def tick(self,tracker,state,count):
        for _ in range(count):
            state['time']+=.05
            tracker.update(state)

    def test_start_zero(self):
        t=SprayScorer();t.update(sample());self.assertEqual(t.value,0)

    def test_cap_blocks_spray(self):
        t=SprayScorer();s=sample(button_travel=.003)
        t.update(s);self.tick(t,s,20)
        self.assertEqual(t.emitted,0);self.assertFalse(any(t.dose))

    def test_no_paint_without_press(self):
        t=SprayScorer();s=sample(cap_detached=True,cap=(CAP_PAD[0],CAP_PAD[1],TOP+.017))
        t.update(s);self.tick(t,s,20)
        self.assertEqual(t.value,.25);self.assertEqual(t.emitted,0)

    def test_wrong_facing_is_overspray(self):
        t=SprayScorer();s=sample(cap_detached=True,cap=(CAP_PAD[0],CAP_PAD[1],TOP+.017),button_travel=.003,axis=(-1.,0.,0.))
        t.update(s);self.tick(t,s,20)
        self.assertEqual(t.result()['overspray'],1);self.assertFalse(any(t.dose))

    def test_far_spray_no_credit(self):
        t=SprayScorer();s=sample(cap_detached=True,cap=(CAP_PAD[0],CAP_PAD[1],TOP+.017),button_travel=.003,nozzle=(0.,0.,TARGET_CENTER[1]))
        t.update(s);self.tick(t,s,20)
        self.assertFalse(any(t.dose));self.assertEqual(t.result()['overspray'],1)

    def test_cap_off_but_not_parked_zero(self):
        t=SprayScorer();s=sample(cap_detached=True,cap=(.3,.2,TOP+.02))
        t.update(s);self.assertEqual(t.value,0)

    def test_center_spray_coats_the_circle_and_preserves_overspray_accounting(self):
        t=SprayScorer();s=sample(cap_detached=True,cap=(CAP_PAD[0],CAP_PAD[1],TOP+.017),button_travel=.003)
        t.update(s);self.tick(t,s,40)
        self.assertGreaterEqual(t.result()['coverage'],.9)
        self.assertLess(t.result()['overspray'],.15)

    def test_circular_mask_uses_radius_not_square_and_has_fifty_two_sample_cells(self):
        cells=list(SprayScorer.cells());targets=[(p,t) for _,p,t in cells if t]
        self.assertEqual(len(targets),52)
        for _,p,target in cells:
            dy,dz=p[1]-TARGET_CENTER[0],p[2]-TARGET_CENTER[1]
            self.assertEqual(target,dy*dy+dz*dz<=TARGET_RADIUS**2)
        corners=[t for _,p,t in cells if .029<abs(p[1]-TARGET_CENTER[0])<.036 and .029<abs(p[2]-TARGET_CENTER[1])<.036]
        self.assertTrue(corners);self.assertFalse(any(corners))
        tracker=SprayScorer()
        for index,_,target in cells:
            if not target:tracker.dose[index]=COAT_DOSE*100
        self.assertEqual(tracker.result()['coverage'],0.)

    def test_budget_is_finite(self):
        t=SprayScorer();s=sample(cap_detached=True,cap=(CAP_PAD[0],CAP_PAD[1],TOP+.017),button_travel=.003)
        t.update(s);self.tick(t,s,300)
        self.assertAlmostEqual(t.spray_seconds,MAX_SPRAY_SECONDS)
        doses=copy.copy(t.dose);self.tick(t,s,20);self.assertEqual(doses,t.dose)

    def test_bad_clock_latches_invalid(self):
        t=SprayScorer();s=sample();t.update(s)
        s['time']=.1;t.update(s);self.assertIsNotNone(t.invalid)
        self.tick(t,s,10);self.assertEqual(t.value,0)

    def test_drop_invalidates_even_after_partial_credit(self):
        t=SprayScorer();s=sample(cap_detached=True,cap=(CAP_PAD[0],CAP_PAD[1],TOP+.017))
        t.update(s);self.assertEqual(t.value,.25)
        s['cap']=(.1,.1,TOP-.1);self.tick(t,s,1)
        self.assertEqual(t.value,0);self.assertIsNotNone(t.invalid)

    def test_nan_fails_closed(self):
        t=SprayScorer();t.update(sample(upright=math.nan))
        self.assertEqual(t.value,0);self.assertIsNotNone(t.invalid)

    def test_full_score_requires_release_and_park(self):
        # Seed deposit only to exercise the end-state rubric, not to claim
        # that any physical policy created this coat.
        t=SprayScorer()
        for i,_,target in t.cells():
            if target:t.dose[i]=COAT_DOSE
        t.emitted=1.;t.off_target=.1
        s=sample(cap_detached=True,cap=(CAP_PAD[0],CAP_PAD[1],TOP+.017))
        t.update(s);self.assertEqual(t.value,.75)
        s['hands_clear']=True;self.tick(t,s,21);self.assertEqual(t.value,1.)
        s['button_travel']=.0025;self.tick(t,s,1);self.assertLess(t.value,1.)

    def test_overspray_prevents_coating_credit(self):
        t=SprayScorer()
        for i,_,target in t.cells():
            if target:t.dose[i]=COAT_DOSE
        t.emitted=1.;t.off_target=.2
        t.update(sample(cap_detached=True,cap=(CAP_PAD[0],CAP_PAD[1],TOP+.017),hands_clear=True))
        self.assertEqual(t.value,.25)

    def test_hand_in_spray_blocks_target(self):
        t=SprayScorer();s=sample(cap_detached=True,cap=(CAP_PAD[0],CAP_PAD[1],TOP+.017),
                               button_travel=.003,hand_tcp=[(TARGET_X-.18,TARGET_CENTER[0],TARGET_CENTER[1])])
        t.update(s);self.tick(t,s,20)
        self.assertFalse(any(t.dose))

    def test_detent_release_without_removal_cannot_spray(self):
        t=SprayScorer();s=sample(cap_detached=True,button_travel=.003)
        t.update(s);self.tick(t,s,20)
        self.assertEqual(t.emitted,0.)

    def test_geometric_coating_path_then_release_can_reach_full_score(self):
        # A synthetic measured-state path checks the complete deposition and
        # release rubric. It is not a robot-feasibility demonstration.
        t=SprayScorer();s=sample(cap_detached=True,cap=(CAP_PAD[0],CAP_PAD[1],TOP+.017))
        t.update(s)
        s['can']=SPRAY_HELD_CAN
        s['nozzle']=(CAN_START[0]+.009,*TARGET_CENTER)
        s['button_travel']=.0027;self.tick(t,s,16)
        self.assertGreaterEqual(t.result()['coverage'],.9)
        self.assertLess(t.result()['overspray'],.15)
        s.update(can=CAN_START,button_travel=0.,hands_clear=True)
        self.tick(t,s,21);self.assertEqual(t.value,1.)

if __name__=='__main__':unittest.main()
