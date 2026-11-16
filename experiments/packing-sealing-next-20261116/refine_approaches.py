"""Explicit highhover/sideentry candidates; no contactmask during freeapproach."""
import json,time
from pathlib import Path
import numpy as np
from certify_face_routes import joint_path,task_path
from screen_open_straddle_push import OpenStraddleSearch,ik,READY,BASES
P=Path(__file__).parent
routes=[]
for source in('face-push-gravity-release.json','face-push-rocked-gravity-release.json'):
 routes.extend(r for r in json.loads((P/source).read_text())['results']if r.get('success')and r['withdrawal']['safe'])
results=[];started=time.monotonic()
for route in routes:
 name=route['flap'];s=OpenStraddleSearch();s.rock_deg=route.get('rock_deg',0.);side=0 if route['arm']=='left' else 1;closed=route['closed_prior'];allinitial=[]
 for initial in(-175.,-174.5):
  goal,R,w=s.point(name,initial,route['radius_m'],route['approach_yaw_deg'],route['lateral_offset_m'],roll=route['polarity']);seed=np.array(min(route['points'],key=lambda p:abs(p['angle_deg']-initial))['q']);attempts=[];found=False
  for distance in(.025,.030,.040,.020):
   if found:break
   hover=goal-R[:,2]*distance;hq,pe,re=ik.solve(hover,ik.matrix_to_quat_xyzw(R),seed,base_pos=BASES[route['arm']],iters=200,tol=1e-6)
   if pe>.0003 or re>.003:attempts.append(dict(distance=distance,failure='hover_IK',pe=pe,re=re));continue
   for height in(.060,.040,.080,0.):
    high=hover+[0,0,height];highq,pe,re=ik.solve(high,ik.matrix_to_quat_xyzw(R),hq,base_pos=BASES[route['arm']],iters=200,tol=1e-6)
    if pe>.0003 or re>.003:attempts.append(dict(distance=distance,height=height,failure='highhover_IK',pe=pe,re=re));continue
    approach=joint_path(s,np.asarray(READY,float),highq,side,name,initial,closed,-.04695,-.010,seconds=6.)
    if not approach['safe']:attempts.append(dict(distance=distance,height=height,failure='freeapproach',detail=approach));continue
    lower=task_path(s,highq,hover,R,side,name,initial,closed,-.010,seconds=2.,contact=False)
    if not lower['safe']:attempts.append(dict(distance=distance,height=height,failure='lower_to_side',detail=lower));continue
    entry=task_path(s,np.array(lower['points'][-1]['q']),goal,R,side,name,initial,closed,-.010,seconds=2.,contact=True)
    if not entry['safe']:attempts.append(dict(distance=distance,height=height,failure='enter_from_side',detail=entry));continue
    found=True;attempts.append(dict(distance=distance,height=height,safe=True,approach=approach,lower=lower,entry=entry));break
  item=dict(flap=name,arm=route['arm'],initial_angle_deg=initial,safe=found,attempts=attempts);allinitial.append(item);results.append(item);(P/'refined-approach-certificates.json').write_text(json.dumps(dict(scope='CPU finitefull315paths CONDITIONEDONinitialmeasuredsettle−175..−174.5; nativeunproved',elapsed_s=time.monotonic()-started,results=results),indent=2)+'\n');print(name,initial,found,attempts[-1].get('distance'),attempts[-1].get('height'),attempts[-1].get('failure'),flush=True)
