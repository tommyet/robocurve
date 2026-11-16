"""Counterfactual area screen only: translated historical measured poses.

No native simulation, new grasp dynamics or feasibility demonstration occurs.
"""
import argparse,copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];TASK=ROOT/'tasks/uncap-spray-panel';sys.path.insert(0,str(TASK))
from scoring import SprayScorer
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
raw=(a.capture/'trajectory.jsonl').read_bytes();trace_hash=hashlib.sha256(raw).hexdigest()
if trace_hash!='5e471c1f9f3d183865c19e04f4f2dd39375f101185b18abc6279627f78f2353c':raise ValueError('historical source trace changed')
rows=[json.loads(x)for x in raw.splitlines()];results=[]
for dy in [-.004,-.002,0.]:
 for dz in [-.002,0.,.002]:
  offset=[.022,dy,dz];tracker=SprayScorer()
  for row in rows:
   s=copy.deepcopy(row)
   for field in ('nozzle','can'):s[field]=[v+d for v,d in zip(s[field],offset)]
   for position in s.get('hand_tcp',[]):
    for i,d in enumerate(offset):position[i]+=d
   for hand in s.get('hands',[]):hand['tcp']=[v+d for v,d in zip(hand['tcp'],offset)]
   tracker.update(s)
  metrics=tracker.result();results.append(dict(offset_world_m=offset,coverage=metrics['coverage'],outside_cm2=metrics['off_plaque_painted_area_cm2'],invalid=metrics['invalid']))
report=dict(scope='COUNTERFACTUAL area-only screen: translated historical observed states, not new native proof; can/grasp dynamics unknown',trace_sha256=trace_hash,scorer_sha256=hashlib.sha256((TASK/'scoring.py').read_bytes()).hexdigest(),config_sha256=hashlib.sha256((TASK/'config.py').read_bytes()).hexdigest(),results=results,min_coverage=min(x['coverage']for x in results),max_outside_cm2=max(x['outside_cm2']for x in results),all_area_pass=all(x['coverage']>=.9 and x['outside_cm2']<=7.539822368615503 and x['invalid']is None for x in results))
a.out.write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items()if k!='results'})
