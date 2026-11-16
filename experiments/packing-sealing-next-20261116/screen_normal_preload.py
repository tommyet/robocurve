"""Bounded ordinary normaltarget preload+0.1deglookahead; no forceclaim/PI."""
import json,time
from pathlib import Path
import numpy as np
from screen_open_straddle_push import OpenStraddleSearch,ik,READY,BASES
P=Path(__file__).parent;routes=[]
for source in('face-push-gravity-release.json','face-push-rocked-gravity-release.json'):
 routes.extend(r for r in json.loads((P/source).read_text())['results']if r.get('success')and r['withdrawal']['safe'])
results=[];start=time.monotonic()
for route in routes:
 s=OpenStraddleSearch();s.rock_deg=route.get('rock_deg',0.);side=0 if route['arm']=='left' else 1;qs=[np.array(READY,float),np.array(READY,float)];fs=[[-.04695]*2,[-.04695]*2];fs[side]=s.fingers;items=[]
 for point in route['points']:
  a=point['angle_deg'];future=min(-70.,a+.1);p,R,w=s.point(route['flap'],future,route['radius_m'],route['approach_yaw_deg'],route['lateral_offset_m'],roll=route['polarity']);_,fr=s.pose(route['flap'],a);p=p-fr[:,2]*.00065;q,pe,re=ik.solve(p,ik.matrix_to_quat_xyzw(R),np.array(point['q']),base_pos=BASES[route['arm']],iters=160,tol=1e-6);q=q.astype(np.float32).astype(float);qs[side]=q;g=s.g.check(qs,fs,s.poses_at(route['flap'],a,route['closed_prior']),True,contact_targets={route['flap']+'_top'},contact_side=side);items.append(dict(angle=a,guard=g,pe=pe,re=re,q=q.tolist()))
 item=dict(flap=route['flap'],normal_preload_m=.00065,angular_lookahead_deg=.1,safe=all(x['guard']['safe']and x['pe']<=.0003 and x['re']<=.003 for x in items),points=items);results.append(item);(P/'normal-preload-screen.json').write_text(json.dumps(dict(scope='FiniteCPUordinaryqtargetpreloadscreen, same1mmissuedguard/all315geometry; no forceproof',elapsed_s=time.monotonic()-start,results=results),indent=2)+'\n');print(route['flap'],item['safe'],[(x['angle'],x['guard'])for x in items if not x['guard']['safe']],flush=True)
