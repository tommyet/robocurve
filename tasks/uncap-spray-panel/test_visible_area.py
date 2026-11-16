"""Visible-area rubric, analytic boundaries, emission domain and hold endpoints."""
import math,unittest
from config import *
from scoring import SprayScorer,cell_area_weights,circle_rectangle_area,supported_spray_domain
from test_scoring import sample

class AnalyticAreaTests(unittest.TestCase):
 def test_known_disk_rectangle_quadrant_and_tangency_areas(self):
  r=TARGET_RADIUS
  self.assertAlmostEqual(circle_rectangle_area(-r,r,-r,r,r),math.pi*r*r,places=15)
  self.assertAlmostEqual(circle_rectangle_area(0,r,0,r,r),math.pi*r*r/4,places=15)
  self.assertAlmostEqual(circle_rectangle_area(0,r,-r,r,r),math.pi*r*r/2,places=15)
  self.assertAlmostEqual(circle_rectangle_area(-.01,.01,-.01,.01,r),.0004,places=15)
  self.assertAlmostEqual(circle_rectangle_area(r,r+.01,-.01,.01,r),0.,places=15)
  self.assertAlmostEqual(circle_rectangle_area(.1,.11,.1,.11,r),0.,places=15)
 def test_grid_partitions_exact_plaque_area_and_every_cell(self):
  weights=cell_area_weights();self.assertEqual(len(weights),GRID*GRID)
  self.assertAlmostEqual(sum(a for a,b in weights),PLAQUE_AREA_M2,places=15)
  self.assertTrue(any(0<a<CELL*CELL for a,b in weights))
  for a,b in weights:self.assertGreaterEqual(a,0.);self.assertGreaterEqual(b,-1e-17);self.assertAlmostEqual(a+b,CELL*CELL,places=17)
 def test_boundary_cell_contributes_both_areas_and_one_visibility_threshold(self):
  t=SprayScorer();weights=cell_area_weights();boundary=next(i for i,(a,b)in enumerate(weights)if a>1e-8 and b>1e-8)
  t.dose[boundary]=math.nextafter(VISIBLE_DOSE,0.);self.assertEqual(t.result()['coverage'],0.);self.assertEqual(t.result()['off_plaque_painted_area_m2'],0.)
  t.dose[boundary]=VISIBLE_DOSE;result=t.result();a,b=weights[boundary]
  self.assertAlmostEqual(result['coverage'],a/PLAQUE_AREA_M2);self.assertAlmostEqual(result['off_plaque_painted_area_m2'],b)
  before=result.copy();t.dose[boundary]=100*COAT_DOSE;after=t.result();self.assertEqual(before['coverage'],after['coverage']);self.assertEqual(before['off_plaque_painted_area_m2'],after['off_plaque_painted_area_m2'])
 def test_area_does_not_depend_on_emission_history_and_limit_is_fixed(self):
  a=SprayScorer();b=SprayScorer();a.dose[0]=b.dose[0]=VISIBLE_DOSE;a.emitted=1;a.off_target=.99;b.emitted=100;b.off_target=.01
  self.assertEqual(a.area_metrics(),b.area_metrics());self.assertNotEqual(a.result()['off_target_mass_fraction_diagnostic'],b.result()['off_target_mass_fraction_diagnostic'])
  self.assertAlmostEqual(MAX_OFF_PLAQUE_AREA_M2*1e4,7.539822368615503)

class SprayDomainTests(unittest.TestCase):
 def check(self,axis=(1.,0.,0.),distance=.20,y=TARGET_CENTER[0],z=TARGET_CENTER[1]):return supported_spray_domain((TARGET_X-distance,y,z),axis)
 def test_normal_cone_entire_backing_and_range(self):
  s=self.check();self.assertTrue(s['valid'],s)
  expected=.20*math.tan(math.radians(SPRAY_HALF_ANGLE));self.assertAlmostEqual(s['footprint_yz_bounds_m'][0][0],TARGET_CENTER[0]-expected)
  self.assertAlmostEqual(s['ray_range_bounds_m'][0],.2);self.assertAlmostEqual(s['ray_range_bounds_m'][1],.2/math.cos(math.radians(SPRAY_HALF_ANGLE)))
 def test_grazing_backward_behind_board_range_and_missed_board_are_invalid(self):
  for axis in ((-1.,0,0),(0.,1.,0),(math.sin(math.radians(SPRAY_HALF_ANGLE)),math.cos(math.radians(SPRAY_HALF_ANGLE)),0)):
   self.assertFalse(self.check(axis=axis)['valid'])
  for d in (-.1,.1,.30):self.assertFalse(self.check(distance=d)['valid'])
  self.assertFalse(self.check(y=TARGET_CENTER[0]+BOARD_HALF)['valid'])
 def test_footprint_edge_containment_and_tilt_formula(self):
  h=.20*math.tan(math.radians(SPRAY_HALF_ANGLE));y=TARGET_CENTER[0]+BOARD_HALF-h
  self.assertTrue(self.check(y=y)['valid']);self.assertFalse(self.check(y=y+1e-6)['valid'])
  beta=math.radians(15.);s=self.check(axis=(math.cos(beta),math.sin(beta),0));self.assertTrue(s['valid'],s)
  low,high=s['footprint_yz_bounds_m'][0]
  self.assertAlmostEqual(low,TARGET_CENTER[0]+.20*math.tan(beta-math.radians(SPRAY_HALF_ANGLE)))
  self.assertAlmostEqual(high,TARGET_CENTER[0]+.20*math.tan(beta+math.radians(SPRAY_HALF_ANGLE)))
 def test_domain_is_checked_only_during_actual_emission(self):
  t=SprayScorer();state=sample(cap_detached=True,cap=(CAP_PAD[0],CAP_PAD[1],TOP+.017),axis=(-1.,0,0));t.update(state)
  state['time']=.05;t.update(state);self.assertIsNone(t.invalid)
  state['button_travel']=.003;state['time']=.1;t.update(state);self.assertIn('cone',t.invalid)

class HoldEndpointTests(unittest.TestCase):
 def test_first_qualifying_endpoint_has_zero_hold_and_twenty_intervals_required(self):
  t=SprayScorer()
  for i,_,inside in t.cells():
   if inside:t.dose[i]=VISIBLE_DOSE
  state=sample(cap_detached=True,cap=(CAP_PAD[0],CAP_PAD[1],TOP+.017),button_travel=.001)
  t.update(state);self.assertEqual(t.finish_hold,0.)
  state['button_travel']=0.;state['time']=.05;t.update(state);self.assertEqual(t.finish_hold,0.)
  for i in range(1,20):state['time']=.05+i*.05;t.update(state)
  self.assertAlmostEqual(t.finish_hold,.95);self.assertLess(t.value,1.)
  state['time']=1.05;t.update(state);self.assertAlmostEqual(t.finish_hold,1.);self.assertEqual(t.value,1.)

if __name__=='__main__':unittest.main()
