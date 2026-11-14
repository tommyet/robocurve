"""Measured surface dryness, structural integrity and released finish."""
import math
from config import MAX_TEMPERATURE
class HairScorer:
 def __init__(self):self.value=0.;self.time=None;self.invalid=None;self.hold=0.;self.operated=False
 def update(self,s):
  dt=0. if self.time is None else s['time']-self.time;self.time=s['time']
  nums=[s['time'],s['root_separation'],s['min_height'],s['dry_fraction'],s['worst_remaining_water_fraction'],s['max_temperature_C'],s['dryer_speed']]
  if not all(math.isfinite(v) for v in nums):self.invalid='nonfinite measured state'
  if not 0<=dt<=.051:self.invalid='missing control samples'
  if s['root_separation']>.005:self.invalid='detached hair or broken lock'
  if s['min_height']<-.03:self.invalid='dropped dryer or hair'
  if s['max_temperature_C']>MAX_TEMPERATURE:self.invalid='task temperature limit exceeded'
  self.operated|=s['power_on'] and s['water_removed_step_kg']>0.
  ready=(s['worst_remaining_water_fraction']<=.10 and not s['power_on'] and s['dryer_parked'] and s['dryer_speed']<.02 and s['hands_clear'])
  self.hold=self.hold+dt if ready else 0.
  self.value=0. if self.invalid else 1. if self.hold>=1. else .75 if s['dry_fraction']>=.9 else .5 if s['dry_fraction']>=.5 else .25 if self.operated else 0.
  return {'score':self.value,'invalid':self.invalid,'release_hold_s':self.hold}
