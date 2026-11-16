import sys,json,math
from pathlib import Path
import numpy as np
sys.path.insert(0,'/private/tmp/hair-holder-egress-cpu')
from audit import *
sys.path.insert(0,'/private/tmp/robocurve-hair-opposite/tasks/dry-long-hair')
from payload_gravity import target_offset
from yam_arena import ik
from yam_arena.constants import READY
rows=[json.loads(l) for l in (CAP/'trajectory.jsonl').open()];idx=next(i for i,r in enumerate(rows) if r['phase']=='lift_dryer');r=rows[idx-1];dryer=np.array(r['dryer_pose']);dR=quat_xyzw_to_matrix(dryer[3:]);cap=next(x for x in rows if x['robot_control'].get('payload_mass_kg') is not None);control=cap['robot_control'];a=control['arms'][0]
com_world=np.array(a['tcp'])+np.array(a['tcp_rotation'])@control['payload_com_tcp'];com_dryer=dR.T@(com_world-dryer[:3]);mass=control['payload_mass_kg'];seed0=np.array(a['arm_joints']);rng=np.random.default_rng(630);seeds=[seed0,np.array(READY),np.array([0,2,1,-1,0,0]),np.array([0,1,2,-1,0,0])]+[rng.uniform(ik.LOWER,ik.UPPER) for _ in range(6)]


def clear(p,R,pieces):
 best=(10.,None,None)
 for n,t in pieces:
  tri=t@R.T+p
  for label,h,size in holders:
   broad=np.maximum(tri.min((0,1))-h-size/2,h-size/2-tri.max((0,1))).max()
   if broad>best[0] and broad>.002:continue
   gap=boxgap(tri,h,size)
   if gap<best[0]:best=(gap,n,label)
 return best
out=[];pieces=geometry.pieces([-.013,-.013])
for z in (-.09,-.065):
 for sign in (1,-1):
  X=np.array([0.,sign,0.]);Z=np.array([1.,0.,0.]);R=np.column_stack((X,np.cross(Z,X),Z));contact=dryer[:3]+dR@np.array([-.019,0,z]);P=contact-R@np.array([0,0,.004]);com_tcp=R.T@(com_world-P);best=None
  for i,seed in enumerate(seeds):
   q,pe,re=ik.solve(P,ik.matrix_to_quat_xyzw(R),seed,base_pos=(0,.305,.75),iters=220,damping=.02,tol=1e-6)
   if best is None or pe+.1*re<best[1]+.1*best[2]:best=(q,pe,re,i)
   if pe<.0001 and re<.002:break
  q,pe,re,which=best;record={'grasp_local_z':z,'closing_Y_sign':sign,'target_tcp':P.tolist(),'rotation':R.tolist(),'initial_IK_error_m':pe,'initial_IK_error_rad':re,'seed':which,'mass_kg':mass,'com_tcp':com_tcp.tolist(),'points':[]}
  if pe<=.0005 and re<=.005:
   for lift in np.linspace(0,.10,21):
    p=P+[0,0,lift];q,pe,re=ik.solve(p,ik.matrix_to_quat_xyzw(R),q,base_pos=(0,.305,.75),iters=220,damping=.02,tol=1e-6);gap,n,label=clear(p,R,pieces)
    try:ff=target_offset(q,mass,com_tcp,(0,.305,.75));effective=q+ff;margin=float(np.degrees(np.minimum(effective-ik.LOWER,ik.UPPER-effective).min()));error=None
    except ValueError as e:ff=np.zeros(6);margin=-999.;error=str(e)
    record['points'].append({'lift_m':float(lift),'IK_error_m':pe,'IK_error_rad':re,'holder_gap_m':gap,'pair':[n,label],'q':q.tolist(),'payload_offset_rad':ff.tolist(),'compensated_joint_margin_deg':margin,'error':error})
   record['minimum_holder_gap_m']=min(x['holder_gap_m'] for x in record['points']);record['minimum_compensated_joint_margin_deg']=min(x['compensated_joint_margin_deg'] for x in record['points']);record['max_IK_error_m']=max(x['IK_error_m'] for x in record['points']);record['max_IK_error_rad']=max(x['IK_error_rad'] for x in record['points']);record['winner']=record['minimum_holder_gap_m']>=.0002 and record['minimum_compensated_joint_margin_deg']>=2 and record['max_IK_error_m']<=.0005 and record['max_IK_error_rad']<=.005
  else:record['winner']=False
  out.append(record);print(json.dumps({k:v for k,v in record.items() if k!='points'}),flush=True)
report={'scope':'Four static unacquired front-handle grasps and21point100mmvertical lifts; complete136handcollisionSTLs/7holderOBBs; nominal+payloadFFjointbounds. NO acquisition/release/reorient transition, fullarm/otherarm/head clearance, loaded friction, or native proof.','captured_native_start_time_s':r['time'],'payload_capture_row_s':cap['time'],'com_in_dryer_frame':com_dryer.tolist(),'actual_grasp_finger_joints_m':[-.013,-.013],'candidates':out,'winners':sum(x['winner'] for x in out)}
Path('/private/tmp/hair-front-regrasp-cpu/report.json').write_text(json.dumps(report,indent=2)+'\n')
