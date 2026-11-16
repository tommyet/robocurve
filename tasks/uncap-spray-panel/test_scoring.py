"""Outcome and exploit checks; synthetic states do not prove robot feasibility."""
import copy
import math
import unittest
from config import *
from scoring import SprayScorer,opposing_left_can_contacts,right_tcp_clear,cell_area_weights


def sample(**changes):
    s=dict(time=0.,can=CAN_START,cap=CAP_START,button_travel=0.,
           nozzle=(TARGET_X-.20,TARGET_CENTER[0],TARGET_CENTER[1]),axis=(1.,0.,0.),
           can_speed=0.,cap_speed=0.,upright=1.,cap_detached=False,hands_clear=False,
           hands=[dict(tcp=list(CAN_START)),dict(tcp=[0.,-.305,1.])],
           left_contact_bodies=['tip_left','tip_right'],left_can_contact_matrix=[[[0.,1.,0.]],[[0.,-1.,0.]]])
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

    def test_wrong_facing_is_invalid_not_fictional_painted_area(self):
        t=SprayScorer();s=sample(cap_detached=True,cap=(CAP_PAD[0],CAP_PAD[1],TOP+.017),button_travel=.003,axis=(-1.,0.,0.))
        t.update(s);self.tick(t,s,20)
        self.assertEqual(t.result()['off_target_mass_fraction_diagnostic'],1);self.assertEqual(t.result()['off_plaque_painted_area_m2'],0.);self.assertIsNotNone(t.invalid);self.assertFalse(any(t.dose))

    def test_far_spray_no_credit(self):
        t=SprayScorer();s=sample(cap_detached=True,cap=(CAP_PAD[0],CAP_PAD[1],TOP+.017),button_travel=.003,nozzle=(0.,0.,TARGET_CENTER[1]))
        t.update(s);self.tick(t,s,20)
        self.assertFalse(any(t.dose));self.assertEqual(t.result()['off_target_mass_fraction_diagnostic'],1);self.assertEqual(t.result()['off_plaque_painted_area_m2'],0.);self.assertIsNotNone(t.invalid)

    def test_cap_off_but_not_parked_zero(self):
        t=SprayScorer();s=sample(cap_detached=True,cap=(.3,.2,TOP+.02))
        t.update(s);self.assertEqual(t.value,0)

    def test_mass_clean_centre_spray_can_still_fail_visible_area_limit(self):
        t=SprayScorer();s=sample(cap_detached=True,cap=(CAP_PAD[0],CAP_PAD[1],TOP+.017),button_travel=.003,nozzle=(TARGET_X-.21,*TARGET_CENTER))
        t.update(s);self.tick(t,s,40)
        self.assertGreaterEqual(t.result()['coverage'],.9)
        self.assertGreater(t.result()['off_plaque_painted_area_m2'],MAX_OFF_PLAQUE_AREA_M2)
        self.assertLess(t.result()['off_target_mass_fraction_diagnostic'],.15)

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
        expected=sum(cell_area_weights()[i][0]for i,_,target in cells if not target)/PLAQUE_AREA_M2
        self.assertAlmostEqual(tracker.result()['coverage'],expected);self.assertGreater(expected,0.)

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

    def test_full_score_requires_nozzle_off_opposing_grip_and_right_clear(self):
        # Seed deposit only to exercise the end-state rubric, not to claim
        # that any physical policy created this coat.
        t=SprayScorer()
        for i,_,target in t.cells():
            if target:t.dose[i]=COAT_DOSE
        t.emitted=1.;t.off_target=.1
        s=sample(cap_detached=True,cap=(CAP_PAD[0],CAP_PAD[1],TOP+.017))
        t.update(s);self.assertEqual(t.value,.75)
        # Held finish can be away from the pad, with LEFT deliberately close.
        s['can']=(.30,-.08,.95);s['hands'][0]['tcp']=list(s['can'])
        s['hands_clear']=False;self.tick(t,s,21);self.assertEqual(t.value,1.)
        s['button_travel']=.0025;self.tick(t,s,1);self.assertLess(t.value,1.)

    def test_opposing_contact_gate_resolves_names_and_rejects_missing_nonfinite_or_parallel(self):
        good=sample();self.assertTrue(opposing_left_can_contacts(good))
        permuted={**good,'left_contact_bodies':['base','tip_right','tip_left'],
                  'left_can_contact_matrix':[[[0,0,0]],[[0,-2,0]],[[0,3,0]]]}
        self.assertTrue(opposing_left_can_contacts(permuted))
        for mode in ('missing','duplicate','shape','nan','one_contact','parallel','weak'):
            s=copy.deepcopy(good)
            if mode=='missing':del s['left_can_contact_matrix']
            if mode=='duplicate':s['left_contact_bodies']=['tip_left','tip_left']
            if mode=='shape':s['left_can_contact_matrix'][0].append([0,1,0])
            if mode=='nan':s['left_can_contact_matrix'][0][0][0]=math.nan
            if mode=='one_contact':s['left_can_contact_matrix'][1][0]=[0,0,0]
            if mode=='parallel':s['left_can_contact_matrix'][1][0]=[0,1,0]
            if mode=='weak':s['left_can_contact_matrix'][1][0]=[0,-.099,0]
            self.assertFalse(opposing_left_can_contacts(s),mode)

    def test_held_finish_continuity_and_native_safety_bounds(self):
        t=SprayScorer()
        for i,_,target in t.cells():
            if target:t.dose[i]=COAT_DOSE
        t.emitted=1.;t.off_target=.1
        s=sample(cap_detached=True,cap=(CAP_PAD[0],CAP_PAD[1],TOP+.017));t.update(s)
        self.tick(t,s,10);self.assertLess(t.value,1.)
        s['left_can_contact_matrix'][0][0]=[0,0,0];self.tick(t,s,1);self.assertEqual(t.finish_hold,0.)
        s['left_can_contact_matrix'][0][0]=[0,1,0];self.tick(t,s,21);self.assertEqual(t.value,1.)
        for mode in ('speed','tilt','button','right_near_cap','right_near_can'):
            x=copy.deepcopy(s)
            if mode=='speed':x['can_speed']=.02
            if mode=='tilt':x['upright']=math.cos(math.radians(10.1))
            if mode=='button':x['button_travel']=.0005
            if mode=='right_near_cap':x['hands'][1]['tcp']=list(x['cap'])
            if mode=='right_near_can':x['hands'][1]['tcp']=list(x['can'])
            self.tick(t,x,1);self.assertEqual(t.finish_hold,0.,mode);self.assertLess(t.value,1.,mode)

    def test_overspray_prevents_coating_credit(self):
        t=SprayScorer()
        for i,_,target in t.cells():
            if target:t.dose[i]=COAT_DOSE
        t.emitted=1.;t.off_target=.2
        for i,_,target in t.cells():
            if not target:t.dose[i]=VISIBLE_DOSE
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
        s['nozzle']=(TARGET_X-.18,*TARGET_CENTER)
        s['button_travel']=.0027;self.tick(t,s,16)
        self.assertGreaterEqual(t.result()['coverage'],.9)
        self.assertLess(t.result()['overspray'],.15)
        s.update(can=CAN_START,button_travel=0.,hands_clear=True)
        self.tick(t,s,21);self.assertEqual(t.value,1.)

if __name__=='__main__':unittest.main()
