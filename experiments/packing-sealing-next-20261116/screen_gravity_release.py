"""Openinnerpad push only pastvertical, then finitechecked withdraw; no nativeproof."""
import json,time,argparse
from pathlib import Path
import numpy as np
from screen_open_straddle_push import OpenStraddleSearch,ik,BASES,READY

def withdrawal(s,route):
 name=route['flap'];arm=route['arm'];side=0 if arm=='left' else 1;radius=route['radius_m'];yaw=route['approach_yaw_deg'];offset=route['lateral_offset_m'];roll=route['polarity'];closed=route['closed_prior'];release=s.end_angle;results=[]
 # Conservativegridtime, parameterizedangularfallrates. Handtracksobservedflap
 # rotation while translatingoutwardthroughrim. Allactual issuedstatesneednative.
 for speed in(0.,5.,10.,15.):
  q=np.array(route['points'][-1]['q']);qs=[np.array(READY,float),np.array(READY,float)];qs[side]=q;fs=[[-.04695]*2,[-.04695]*2];fs[side]=s.fingers;path=[]
  duration=getattr(s,'withdraw_duration',1.);distance=getattr(s,'withdraw_distance',.040)
  for t in np.arange(0.,duration+.0001,.05):
   angle=release+speed*t;d=distance*ik.smoothstep(t/duration);p,R,w=s.point(name,angle,radius,yaw,offset,roll=roll);p=p-R[:,2]*d;previous=q.copy();q,pe,re=ik.solve(p,ik.matrix_to_quat_xyzw(R),q,base_pos=BASES[arm],iters=160,tol=1e-6)
   if pe>.0003 or re>.003:return dict(safe=False,reason='withdraw_IK',fall_rate_deg_s=speed,time_s=t,angle=angle,position_error_m=pe,rotation_error_rad=re)
   q=q.astype(np.float32).astype(float)
   if np.any(np.abs(q-previous)>.04+1e-12):return dict(safe=False,reason='withdraw_20Hz_joint_slew',fall_rate_deg_s=speed,time_s=t,maximum_joint_delta_rad=float(np.max(np.abs(q-previous))))
   qs[side]=q;g=s.g.check(qs,fs,s.poses_at(name,angle,closed),True,contact_targets={name+'_top'},contact_side=side)
   if not g['safe']:return dict(safe=False,reason='coupled_withdraw_full315_guard',fall_rate_deg_s=speed,time_s=t,angle=angle,withdraw_distance_m=d,guard=g)
   path.append(dict(time_s=t,angle_deg=angle,distance_m=d,q=q.tolist(),guard=g))
  results.append(dict(fall_rate_deg_s=speed,path=path))
 return dict(safe=True,scope='Finite4fallrates×21timesteps only; notcontinuousproof/native dynamics; ordinaryIK/315guards preserved',paths=results)

def run(out,flaps):
 results=[];started=time.monotonic();s=OpenStraddleSearch();s.end_angle=-70.
 for name in flaps:
  closed=[]if name=='east'else['east']if name=='west'else['east','west']if name=='north'else['east','west','north'];width=s.parts[name+'_top']['size'][0];found=False
  for radius in(.075,.065,.055,.045):
   if found:break
   for inset in(.014,.020,.010,.030):
    if found:break
    for sign,yaw,roll,arm in[(-1,90.,180.,'left'),(1,270.,0.,'right'),(-1,90.,0.,'left'),(1,270.,180.,'right')]:
     r=s.candidate(name,arm,radius,yaw,sign*(width/2-inset),closed,roll=roll);r['release_angle_deg']=s.end_angle
     if r.get('success'):r['withdrawal']=withdrawal(s,r)
     results.append(r);out.write_text(json.dumps(dict(scope='CPU pushpastvertical+gravityreleaseplanning only, no native/runtimeproof',elapsed_s=time.monotonic()-started,results=results),indent=2)+'\n');print(name,arm,radius,inset,r.get('failure','ARC_PASS'),r.get('angle'),r.get('withdrawal',{}).get('reason',r.get('withdrawal',{}).get('safe')),flush=True)
     if r.get('success')and r['withdrawal']['safe']:found=True;break
 return results
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--flaps',nargs='+',default=['east','west','north','south']);a=p.parse_args();run(a.out,a.flaps)
