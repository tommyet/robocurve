"""Explicit above-box standoff to avoid joint-interpolation fingertip sweep."""
import json,time
from pathlib import Path
import numpy as np
from certify_face_routes import joint_path,task_path
from screen_open_straddle_push import OpenStraddleSearch,ik,READY,BASES
P=Path(__file__).parent;routes=[r for r in json.loads((P/'face-push-rocked-gravity-release.json').read_text())['results']if r.get('success')and r['withdrawal']['safe']and r['flap']=='north'];routes.extend(r for r in json.loads((P/'south-mirrored-seeds.json').read_text())if r.get('success')and r['withdrawal']['safe']);out=[];started=time.monotonic()
for route in routes:
 name=route['flap'];s=OpenStraddleSearch();s.rock_deg=route.get('rock_deg',0.);side=0 if route['arm']=='left' else 1;closed=route['closed_prior'];found=False;angle=-175.;goal,R,w=s.point(name,angle,route['radius_m'],route['approach_yaw_deg'],route['lateral_offset_m'],roll=route['polarity']);seed=np.array(route['points'][0]['q'])
 for d in(.040,.045,.050):
  if found:break
  hover=goal-R[:,2]*d;hq,pe,re=ik.solve(hover,ik.matrix_to_quat_xyzw(R),seed,base_pos=BASES[route['arm']],iters=220,tol=1e-6)
  if pe>.0003 or re>.003:out.append(dict(flap=name,distance=d,failure='hover_IK',pe=pe,re=re));continue
  for standoff in([.35,.22,1.0675],[.4,.22,1.0675],[.30,.30,1.0675],[.35,.15,1.12]):
   standoff=np.array(standoff);standoff[1]*=1 if side==0 else -1;sq,pe,re=ik.solve(standoff,ik.matrix_to_quat_xyzw(R),hq,base_pos=BASES[route['arm']],iters=220,tol=1e-6)
   if pe>.0003 or re>.003:out.append(dict(flap=name,distance=d,standoff=standoff.tolist(),failure='standoff_IK',pe=pe,re=re));continue
   jp=joint_path(s,np.asarray(READY,float),sq,side,name,angle,closed,-.04695,-.010,seconds=6.)
   if not jp['safe']:out.append(dict(flap=name,distance=d,standoff=standoff.tolist(),failure='standoff_freejointpath',detail=jp));continue
   tp=task_path(s,sq,hover+[0,0,.060],R,side,name,angle,closed,-.010,seconds=4.,contact=False)
   if not tp['safe']:out.append(dict(flap=name,distance=d,standoff=standoff.tolist(),failure='standoff_transfer',detail=tp));continue
   lower=task_path(s,np.array(tp['points'][-1]['q']),hover,R,side,name,angle,closed,-.010,seconds=2.,contact=False)
   if not lower['safe']:out.append(dict(flap=name,distance=d,standoff=standoff.tolist(),failure='side_lower',detail=lower));continue
   entry=task_path(s,np.array(lower['points'][-1]['q']),goal,R,side,name,angle,closed,-.010,seconds=2.,contact=True)
   item=dict(flap=name,distance=d,standoff=standoff.tolist(),safe=entry['safe'],joint_path=jp,transfer=tp,lower=lower,entry=entry);out.append(item);found=entry['safe'];print(name,d,standoff,'SAFE',found,flush=True)
   if found:break
  (P/'standoff-approach-certificates.json').write_text(json.dumps(dict(scope='CPU settled175stageonly; full315allstages, no nativeproof',elapsed_s=time.monotonic()-started,results=out),indent=2)+'\n');print(name,d,'completed',found,out[-1].get('failure'),flush=True)
