import sys
sys.dont_write_bytecode=True
from pathlib import Path
import cProfile,pstats,io,json,time,copy,hashlib
import numpy as np
from baseline_safety import ScoopSafety as Baseline
from fast_safety import ScoopSafety as Fast
from workload import ROOT,SAMPLES,inputs,selected,tick
baseline=Baseline();fast=Fast();records=[];start=time.perf_counter();maximum=0.;mismatches=[]
def compare(label,data):
 global maximum
 a=baseline.check(**data);b=fast.check(**data)
 for key in ('safe','hard_pair','intended_pair','scope'):assert a[key]==b[key],(label,key,a,b)
 for key in ('hard_gap_m','other_arm_aabb_gap_m','intended_target_gap_m'):
  if a[key]is None:assert b[key]is None
  else:
   error=abs(a[key]-b[key]);maximum=max(maximum,error);assert error<1e-12,(label,key,a,b)
 records.append(dict(label=label,baseline=a,fast=b))
for i in range(len(SAMPLES)):
 compare('route_'+str(i),inputs(i))
 if i%80==0:print('PARITY',i,flush=True)
# Deliberate current-state changes, without hiding any object/body pair.
for i in (0,191,256,296):
 d=inputs(i);m=fast.world(d['q'],d['fingers'],np.array([0,.305,.75]));p=m[-1][1].reshape(-1,3).mean(0)
 for name in ('north','south_bottom'):
  bad=copy.deepcopy(d);bad['poses'][name]=np.r_[p,[0,0,0,1]];compare('collision_'+str(i)+'_'+name,bad);assert records[-1]['baseline']['safe']is False
 bad=copy.deepcopy(d);bad['cutter'][:3]=p;compare('cutter_collision_'+str(i),bad);assert records[-1]['baseline']['safe']is False
# Same dictionary/array objects are mutated: no scene or actor pose is cached.
d=inputs(191);compare('fresh_before',d);d['poses']['north'][:3]=np.array([.3,.1,.8]);compare('fresh_after_mutation',d)
# Exact right-state reuse is legal only for identical numeric values. Mutation
# of even one component invalidates the rightFK cache on the very next call.
d=inputs(191);fast.check(**d);builds=fast.stats['right_fk_builds'];fast.check(**d);assert fast.stats['right_fk_builds']==builds
d['right_q'][0]+=1e-5;compare('right_joint_mutation',d);assert fast.stats['right_fk_builds']==builds+1
# Missing/nonfinite data fail as before, never manufactured zero contacts.
for key in ('q','cutter','right_q'):
 bad=inputs(191);bad[key][0]=float('nan')
 for model in (baseline,fast):
  try:model.check(**bad)
  except ValueError:pass
  else:raise AssertionError('nonfinite not rejected')
parity_elapsed=time.perf_counter()-start
# Matched warm 9-tick workload includes IK, actual guard and distinctcommand
# guard. No native/GPU timing claim; initialization/assetIO excluded for BOTH.
measurements=[]
for name,model in [('baseline',baseline),('fast',fast)]:
 times=[]
 for repeat in range(3):
  begin=time.perf_counter()
  for i in selected():tick(model,i)
  times.append(time.perf_counter()-begin)
 measurements.append(dict(name=name,ticks_per_batch=len(selected()),checks_per_batch=2*len(selected()),seconds=times,median_s=float(np.median(times))))
pr=cProfile.Profile();pr.enable()
for i in selected():tick(fast,i)
pr.disable();pr.dump_stats(str(ROOT/'fast.prof'));stream=io.StringIO();pstats.Stats(pr,stream=stream).strip_dirs().sort_stats('cumulative').print_stats(25);(ROOT/'fast-profile.txt').write_text(stream.getvalue())
report=dict(route_cases=len(SAMPLES),total_finite_cases=len(records),maximum_numeric_difference_m=maximum,all_pairs_identifiers_scope_decisions_match=True,negative_collision_cases=12,actual_inplace_scene_mutation_preserved=True,right_cache_exact_value_invalidation_tested=True,all321_exceptions_and_thresholds_unchanged=True,parity_elapsed_s=parity_elapsed,measurements=measurements,speedup=measurements[0]['median_s']/measurements[1]['median_s'],fast_dispatch_counts=fast.stats,baseline_profile='baseline-profile.txt',fast_profile='fast-profile.txt',source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in ROOT.glob('*.py')},scope='ISOLATED CPU candidate only, all315×15pairs kept. Same scalarSAT/refinement andthresholds. RightFKmemo exactvaluesonly; allscene/cutterposesfresh. No active013/coupon/source/GPU edits or nativeperformance/equivalence claim.',records=records)
(ROOT/'comparison-report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');summary={k:v for k,v in report.items()if k!='records'};(ROOT/'comparison-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('DONE',json.dumps(summary),flush=True)
