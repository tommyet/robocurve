"""Full315 finite sampled approach/postrelease/park for savedordinarypushroutes."""
import json,time
from pathlib import Path
import numpy as np
from screen_open_straddle_push import OpenStraddleSearch,ik,BASES,READY
P=Path(__file__).parent

def guard(s,q,f,side,name,angle,closed,contact,neighbor_angle=-175.):
 poses=s.poses_at(name,angle,closed)
 for other in('east','west','north','south'):
  if other!=name and other not in closed:poses[other+'_top']=s.pose(other,neighbor_angle)
 qs=[np.asarray(READY,dtype=np.float32).astype(float),np.asarray(READY,dtype=np.float32).astype(float)];qs[side]=q;fs=[[-.04695]*2,[-.04695]*2];fs[side]=[f]*2
 return s.g.check(qs,fs,poses,contact,contact_targets={name+'_top'},contact_side=side)

def joint_path(s,start,end,side,name,angle,closed,f0,f1,seconds=5.):
 previous=np.asarray(start,float);points=[]
 for t in np.arange(0,seconds+.001,.05):
  b=ik.smoothstep(t/seconds);q=(start+(end-start)*b).astype(np.float32).astype(float);f=f0+(f1-f0)*b
  if np.any(np.abs(q-previous)>.04+1e-12):return dict(safe=False,reason='jointspace_slew',time=t)
  for na in(-175.,-174.5):
   g=guard(s,q,f,side,name,angle,closed,False,na)
   if not g['safe']:return dict(safe=False,reason='jointspace_full315',time_s=t,neighbor_angle=na,guard=g)
  points.append(dict(t=t,q=q.tolist(),finger=f,guard=g));previous=q
 return dict(safe=True,points=points)

def task_path(s,startq,endp,endR,side,name,angle,closed,f,seconds=2.,contact=False):
 q=np.asarray(startq,float);startp,startR=ik.tcp_pose(q,BASES['left'if side==0 else'right']);points=[]
 for t in np.arange(0,seconds+.001,.05):
  b=ik.smoothstep(t/seconds);p=startp+(endp-startp)*b;R=ik.slerp_matrix(startR,endR,b);old=q.copy();q,pe,re=ik.solve(p,ik.matrix_to_quat_xyzw(R),q,base_pos=BASES['left'if side==0 else'right'],iters=160,tol=1e-6);q=q.astype(np.float32).astype(float)
  if pe>.0003 or re>.003:return dict(safe=False,reason='taskspace_IK',time_s=t,pe=pe,re=re)
  if np.any(np.abs(q-old)>.04+1e-12):return dict(safe=False,reason='taskspace_slew',time_s=t,maximum_delta=float(abs(q-old).max()))
  for na in(-175.,-174.5):
   g=guard(s,q,f,side,name,angle,closed,contact,na)
   if not g['safe']:return dict(safe=False,reason='taskspace_full315',time_s=t,neighbor_angle=na,guard=g)
  points.append(dict(t=t,q=q.tolist(),finger=f,guard=g));
 return dict(safe=True,points=points)

def certify(route):
 s=OpenStraddleSearch();s.rock_deg=route.get('rock_deg',0.);s.end_angle=route['release_angle_deg'];name=route['flap'];side=0 if route['arm']=='left' else 1;closed=route['closed_prior'];rad=route['radius_m'];yaw=route['approach_yaw_deg'];off=route['lateral_offset_m'];roll=route['polarity'];report=dict(flap=name,route=route,acquisition=[],postrelease=[],parks=[])
 for initial in(-175.,-160.):
  goal,R,w=s.point(name,initial,rad,yaw,off,roll=roll);seed=np.array(min(route['points'],key=lambda p:abs(p['angle_deg']-initial))['q']);hover=goal-R[:,2]*.040;hq,pe,re=ik.solve(hover,ik.matrix_to_quat_xyzw(R),seed,base_pos=BASES[route['arm']],iters=200,tol=1e-6)
  if pe>.0003 or re>.003:report['acquisition'].append(dict(initial_angle=initial,safe=False,reason='hover_IK',pe=pe,re=re));continue
  approach=joint_path(s,np.asarray(READY,float),hq,side,name,initial,closed,-.04695,-.010)
  if not approach['safe']:report['acquisition'].append(dict(initial_angle=initial,safe=False,approach=approach));continue
  entry=task_path(s,hq,goal,R,side,name,initial,closed,-.010,contact=True)
  report['acquisition'].append(dict(initial_angle=initial,safe=entry['safe'],approach=approach,entry=entry))
 for path in route['withdrawal']['paths']:
  q=np.asarray(path['path'][-1]['q']);initial=path['path'][-1]['angle_deg'];gravity=[]
  for angle in np.linspace(initial,0,int(np.ceil(abs(initial)/2))+1):
   g=guard(s,q,-.010,side,name,angle,closed,False)
   if not g['safe']:gravity.append(dict(angle=angle,safe=False,guard=g));break
   gravity.append(dict(angle=angle,safe=True,guard=g))
  post=dict(fall_rate_deg_s=path['fall_rate_deg_s'],safe=all(x['safe']for x in gravity),samples=gravity);report['postrelease'].append(post)
  if not post['safe']:continue
  park=joint_path(s,q,np.asarray(READY,float),side,name,0.,closed,-.010,-.04695)
  if not park['safe']:
   pp,RR=ik.tcp_pose(q,BASES[route['arm']]);lift=task_path(s,q,pp+[0,0,.060],RR,side,name,0.,closed,-.010,seconds=2.,contact=False)
   if lift['safe']:park2=joint_path(s,np.array(lift['points'][-1]['q']),np.asarray(READY,float),side,name,0.,closed,-.010,-.04695);park=dict(safe=park2['safe'],direct_failure=park,lift=lift,after_lift=park2)
   else:park=dict(safe=False,direct_failure=park,lift=lift)
  report['parks'].append(dict(fall_rate_deg_s=path['fall_rate_deg_s'],**park))
 report['safe']=len(report['acquisition'])==2 and all(x['safe']for x in report['acquisition'])and len(report['postrelease'])==4 and all(x['safe']for x in report['postrelease'])and len(report['parks'])==4 and all(x['safe']for x in report['parks']);return report
if __name__=='__main__':
 routes=[]
 for source in('face-push-gravity-release.json','face-push-rocked-gravity-release.json'):
  routes.extend(r for r in json.loads((P/source).read_text())['results']if r.get('success')and r['withdrawal']['safe'])
 results=[];start=time.monotonic()
 for route in routes:
  r=certify(route);results.append(r);(P/'full-face-route-certificates.json').write_text(json.dumps(dict(scope='Finite CPU geometry+IK only, CONDITIONEDonmeasuredinitialopenflapsettlinggate(-175..-174.5deg); no nativecontact/dynamicsproof. Initial160stillunmodified, robotwaitsnaturalsettle.',elapsed_s=time.monotonic()-start,results=results),indent=2)+'\n');print(route['flap'],'safe',r['safe'],'acq',[(x['initial_angle'],x['safe'],x.get('reason'),x.get('approach',{}).get('reason'),x.get('entry',{}).get('reason'))for x in r['acquisition']],'post',[x['safe']for x in r['postrelease']],'park',[x['safe']for x in r['parks']],flush=True)
