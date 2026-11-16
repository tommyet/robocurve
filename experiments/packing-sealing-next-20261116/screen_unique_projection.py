"""Compare exact vertex deduplication against the unchanged SAT on native scenes."""
import sys,inspect,json,time,argparse
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tasks/pack-and-tape-carton'))
import roll_probe
from yam_arena.urdf import quat_xyzw_to_matrix
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
original=roll_probe.box_gap;namespace={'np':np};exec(inspect.getsource(original).replace('flat=v.reshape(-1,3)','flat=np.unique(v.reshape(-1,3),axis=0)'),namespace);dedup=namespace['box_gap'];g=roll_probe.Geometry();m=json.loads((a.capture/'capture-manifest.json').read_text());data=[json.loads(s)for s in (a.capture/'trajectory.jsonl').read_text().splitlines()];reports=[];pairs=[]
for row_index in (0,100,171,len(data)-1):
 r=data[row_index];poses={v['entity']:(np.array(r['native_body_world_poses'][path][:3]),quat_xyzw_to_matrix(r['native_body_world_poses'][path][3:]))for path,v in m['owners'].items()if v['kind']=='object'};qs=[np.array(h['joints'])for h in r['native_hands']];fs=[np.array(h['finger_joints'])for h in r['native_hands']]
 def traced(tri,p,R,size):
  x=original(tri,p,R,size);start=time.perf_counter();y=dedup(tri,p,R,size);duration=time.perf_counter()-start
  pairs.append(dict(triangles=len(tri),vertices=len(np.unique(tri.reshape(-1,3),axis=0)),original=x,dedup=y,difference=y-x,dedup_seconds=duration))
  if abs(x-y)>1e-12:raise ValueError('SAT dedup changed separation')
  return x
 roll_probe.box_gap=traced;g.check(qs,fs,poses,True,contact_targets={'east_top'},contact_side=0)
 elapsed=[];results=[]
 for fn in (original,dedup):
  roll_probe.box_gap=fn;start=time.perf_counter();results.append(g.check(qs,fs,poses,True,contact_targets={'east_top'},contact_side=0));elapsed.append(time.perf_counter()-start)
 if results[0]!=results[1]:raise ValueError('whole guard result changed')
 reports.append(dict(row=row_index,original_seconds=elapsed[0],dedup_seconds=elapsed[1],exact_guard_equal=True))
roll_probe.box_gap=original;result=dict(scope='Experimental CPU deduplicated SAT projection; no production/runtime change',cases=reports,near_pair_count=len(pairs),max_gap_difference=max(abs(x['difference'])for x in pairs),pairs=pairs);a.out.write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items()if k!='pairs'})
