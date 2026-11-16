"""Compare conservative SAT certificates with full SAT on measured native states."""
import sys,json,time,argparse,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tasks/pack-and-tape-carton'))
from roll_probe import Geometry
from yam_arena.urdf import quat_xyzw_to_matrix
from yam_arena.constants import FINGER_OPEN
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();raw=(a.capture/'trajectory.jsonl').read_bytes();data=[json.loads(x)for x in raw.splitlines()];m=json.loads((a.capture/'capture-manifest.json').read_text());full=Geometry();fast=Geometry(fast_certificates=True);rows=[]
for index in (0,100,171,len(data)-1):
 r=data[index];poses={v['entity']:(np.array(r['native_body_world_poses'][path][:3]),quat_xyzw_to_matrix(r['native_body_world_poses'][path][3:]))for path,v in m['owners'].items()if v['kind']=='object'};qs=[np.array(h['joints'])for h in r['native_hands']];fs=[np.array(h['finger_joints'])for h in r['native_hands']];cases=[('actual',qs,fs)]
 if index==len(data)-1:
  for i,t in enumerate(r['robot_control']['advance_trials']):
   q=np.asarray(t['action_14d']);cases.append((f'candidate_{i}',[q[:6],q[7:13]],[[q[6]*FINGER_OPEN]*2,[q[13]*FINGER_OPEN]*2]))
 for label,q,f in cases:
  values=[];times=[]
  for geom in (full,fast):
   start=time.perf_counter();values.append(geom.check(q,f,poses,True,contact_targets={'east_top'},contact_side=0));times.append(time.perf_counter()-start)
  x,y=values
  if x['safe']!=y['safe']or y['hard_gap_m']>x['hard_gap_m']+1e-12 or y['target_gap_m']>x['target_gap_m']+1e-12 or y['other_arm_gap_m']!=x['other_arm_gap_m']:raise ValueError('guard classification/bound contract changed')
  rows.append(dict(row=index,case=label,full_seconds=times[0],fast_seconds=times[1],full=x,fast=y))
report=dict(scope='LOCAL CPU benchmark under concurrent work; not a native speed guarantee',trace_sha256=hashlib.sha256(raw).hexdigest(),all_classifications_equal=True,all_fast_bounds_conservative=True,cases=rows);a.out.write_text(json.dumps(report,indent=2)+'\n');print([(r['row'],r['case'],round(r['full_seconds'],4),round(r['fast_seconds'],4),r['full']['safe'])for r in rows])
