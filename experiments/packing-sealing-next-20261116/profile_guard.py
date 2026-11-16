"""CPU guard profiling on a measured native state; not physical validation."""
import cProfile,pstats,json,sys,time,io,argparse
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tasks/pack-and-tape-carton'))
from roll_probe import Geometry
from yam_arena.urdf import quat_xyzw_to_matrix
p=argparse.ArgumentParser();p.add_argument('capture',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
m=json.loads((a.capture/'capture-manifest.json').read_text());r=json.loads((a.capture/'trajectory.jsonl').read_text().splitlines()[-1]);poses={v['entity']:(np.array(r['native_body_world_poses'][path][:3]),quat_xyzw_to_matrix(r['native_body_world_poses'][path][3:]))for path,v in m['owners'].items()if v['kind']=='object'}
qs=[np.array(h['joints'])for h in r['native_hands']];fs=[np.array(h['finger_joints'])for h in r['native_hands']];g=Geometry();profile=cProfile.Profile();times=[]
profile.enable()
for _ in range(3):
 start=time.perf_counter();result=g.check(qs,fs,poses,True,contact_targets={'east_top'},contact_side=0);times.append(time.perf_counter()-start)
profile.disable();s=io.StringIO();pstats.Stats(profile,stream=s).sort_stats('cumtime').print_stats(18)
report=dict(scope='LOCAL CPU timing under concurrent local work, not native performance guarantee',samples=3,seconds=times,guard=result,top_functions=s.getvalue());a.out.write_text(json.dumps(report,indent=2)+'\n');print(report['seconds']);print(s.getvalue())
