"""Bounded N/S approach relief; actual finite geometry, no native proof."""
import json,time,argparse
from pathlib import Path
import numpy as np
from certify_face_routes import joint_path,task_path
from screen_open_straddle_push import OpenStraddleSearch,ik,READY,BASES
P=Path(__file__).parent

def run(angle=-175.,out=P/'relieved-entry-certificates.json'):
 routes=[r for r in json.loads((P/'face-push-rocked-gravity-release.json').read_text())['results']if r.get('success')and r['withdrawal']['safe']and r['flap']=='north']
 routes.extend(r for r in json.loads((P/'south-mirrored-seeds.json').read_text())if r.get('success')and r['withdrawal']['safe'])
 results=[];start=time.monotonic()
 for route in routes:
  name=route['flap'];side=0 if route['arm']=='left'else 1;s=OpenStraddleSearch();s.rock_deg=route.get('rock_deg',0.);closed=route['closed_prior']
  goal,R,w=s.point(name,angle,route['radius_m'],route['approach_yaw_deg'],route['lateral_offset_m'],roll=route['polarity']);normal=s.pose(name,angle)[1][:,2];hover=goal-R[:,2]*.040;seed=np.array(route['points'][0]['q'])
  # Preserve the verified contact IK branch when constructing the hover.
  hq,pe,re=ik.solve(hover,ik.matrix_to_quat_xyzw(R),seed,base_pos=BASES[route['arm']],iters=220,tol=1e-6)
  if pe>.0003 or re>.003:results.append(dict(flap=name,failure='hover_IK',pe=pe,re=re));continue
  standoff=np.array([.35,.22*(1 if side==0 else -1),1.0675]);sq,pe,re=ik.solve(standoff,ik.matrix_to_quat_xyzw(R),hq,base_pos=BASES[route['arm']],iters=220,tol=1e-6)
  if pe>.0003 or re>.003:results.append(dict(flap=name,failure='standoff_IK',pe=pe,re=re));continue
  jp=joint_path(s,np.asarray(READY,float),sq,side,name,angle,closed,-.04695,-.010,seconds=6.)
  tp=task_path(s,sq,hover+[0,0,.060],R,side,name,angle,closed,-.010,seconds=4.,contact=False)if jp['safe']else dict(safe=False)
  lower=task_path(s,np.array(tp['points'][-1]['q']),hover,R,side,name,angle,closed,-.010,seconds=2.,contact=False)if tp['safe']else dict(safe=False)
  prefix=dict(joint_path=jp,transfer=tp,lower=lower)
  if not lower['safe']:results.append(dict(flap=name,safe=False,failure='prefix',**prefix));continue
  for relief in(.002,.004,.006):
   normal_out=task_path(s,np.array(lower['points'][-1]['q']),hover+normal*relief,R,side,name,angle,closed,-.010,seconds=1.,contact=False)
   lateral=task_path(s,np.array(normal_out['points'][-1]['q']),goal+normal*relief,R,side,name,angle,closed,-.010,seconds=2.,contact=False)if normal_out['safe']else dict(safe=False)
   close=task_path(s,np.array(lateral['points'][-1]['q']),goal,R,side,name,angle,closed,-.010,seconds=1.,contact=True)if lateral['safe']else dict(safe=False)
   item=dict(flap=name,arm=route['arm'],relief_m=relief,safe=close['safe'],route=route,prefix=prefix,normal_out=normal_out,lateral=lateral,normal_close=close);results.append(item)
   out.write_text(json.dumps(dict(scope=__doc__,active_angle_deg=angle,elapsed_s=time.monotonic()-start,results=results),indent=2)+'\n');print(name,relief,[(n,v['safe'],v.get('reason'))for n,v in [('out',normal_out),('lateral',lateral),('close',close)]],flush=True)
   if item['safe']:break
 out.write_text(json.dumps(dict(scope=__doc__,active_angle_deg=angle,elapsed_s=time.monotonic()-start,results=results),indent=2)+'\n')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--active-angle',type=float,choices=(-175.,-174.5),default=-175.);parser.add_argument('--out',type=Path,default=P/'relieved-entry-certificates.json');args=parser.parse_args();run(args.active_angle,args.out)
