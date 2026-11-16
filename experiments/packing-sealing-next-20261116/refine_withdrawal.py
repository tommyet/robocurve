"""Reuse independently guarded pusharcs; test shorter/slower ordinary exit."""
import json,time
from pathlib import Path
from screen_gravity_release import withdrawal
from screen_open_straddle_push import OpenStraddleSearch
P=Path(__file__).parent
sources=['face-push-gravity-release.json','face-push-rocked-gravity-release.json'];routes=[]
for source in sources:
 if(P/source).exists():routes.extend(x for x in json.loads((P/source).read_text())['results']if x.get('success'))
results=[];started=time.monotonic();found=set()
for route in sorted(routes,key=lambda x:({'north':0,'south':1,'east':2,'west':3}[x['flap']],x['radius_m'])):
 if route['flap']in found:continue
 s=OpenStraddleSearch();s.end_angle=route['release_angle_deg'];s.rock_deg=route.get('rock_deg',0.)
 for distance,duration in[(.030,1.),(.030,1.25),(.035,1.25),(.040,1.5),(.025,1.)]:
  s.withdraw_distance=distance;s.withdraw_duration=duration;r=withdrawal(s,route);item=dict(flap=route['flap'],arm=route['arm'],source_route=route,withdraw_distance_m=distance,withdraw_duration_s=duration,withdrawal=r);results.append(item);(P/'refined-withdrawals.json').write_text(json.dumps(dict(elapsed_s=time.monotonic()-started,results=results),indent=2)+'\n');print(route['flap'],route['arm'],route['lateral_offset_m'],distance,duration,r.get('safe'),r.get('reason'),r.get('time_s'),flush=True)
  if r['safe']:found.add(route['flap']);break
