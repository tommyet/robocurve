"""CPU sampled315-piece whole-arm check; no simulation/task mutation."""
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,'/private/tmp')
from pathlib import Path
import hashlib,json,math,time
import numpy as np
# Reuse corrected origin-RPY/mesh-scale loader, not the old gripper-only mesh.
exec(Path('/private/tmp/astra_carton009_arm_critical.py').read_text().split('RH=row')[0])
basepath=Path('/private/tmp/carton-open-coupon');row=json.loads((basepath/'start/source-row.json').read_text());route=json.loads(Path('/private/tmp/astra-outer-scoop-route-ready.json').read_text())
actual=next(h for h in row['native_hands']if h['side']=='left');right=next(h for h in row['native_hands']if h['side']=='right');q=np.array(row['action_14d'][:6]);fingers=np.array([-.003,-.003]);base=np.array([0,.305,.75])
cp=np.array(row['cutter_pose']);cr=quat_xyzw_to_matrix(cp[3:]);w0={n:(np.array(v[:3]),quat_xyzw_to_matrix(v[3:]))for n,v in row['poses'].items()}
for n,size,off in [('cutter_handle',(.1,.025,.025),(0,0,0)),('cutter_guard',(.02,.03,.02),(.052,0,.002)),('cutter_blade',(.014,.0005,.008),(.062,0,-.016))]:w0[n]=(cp[:3]+cr@off,cr);defs[n]={'size':size}
rightparts=worldparts(right['joints'],right['finger_joints'],np.array([0,-.305,.75]));olo=np.array([a.reshape(-1,3).min(0)for _,a in rightparts]);ohi=np.array([a.reshape(-1,3).max(0)for _,a in rightparts])
# Actual179s wall/flap/hinge frame, unchanged on initial approach. The target
# flap follows the sampled supported arc ONLY in this CPU certificate.
wallp,wallR=w0['north'];fp0,fr0=w0['north_bottom'];h=hinges['north_bottom'];hinge=fp0+fr0@h['anchor_b'];axis=wallR[:,0];angle0=row['angles_deg']['north_bottom_hinge'];Rtarget=np.array(route['support_R']);support=np.array(route['actual_STL_point_TCP'])
def pose_at(angle,contact=True):
 fr=axis_angle_matrix(axis,np.radians(angle-angle0))@fr0;fp=hinge-fr@h['anchor_b'];w=dict(w0);w['north_bottom']=(fp,fr);witness=fp-fr[:,1]*.0435-fr[:,2]*.0015-np.array([0,0,.0008]);tcp=witness-Rtarget@support
 if contact:tcp=tcp+np.array([0,0,.0008])
 return tcp,w
samples=[]
def add(phase,tcp,R,w,value):
 global q
 q,pe,re=ik.solve(tcp,ik.matrix_to_quat_xyzw(R),q,base_pos=base,iters=240)
 samples.append(dict(phase=phase,value=float(value),q=q.copy(),tcp=np.asarray(tcp),R=np.asarray(R),world=w,pe_m=pe,re_rad=re,fingers=fingers.copy()))
# Full opening->6mm closure at parked q before movement is also checked.
for f in np.linspace(0,1,9):samples.append(dict(phase='prepare_jaws',value=float(f),q=np.array(actual['joints']),tcp=np.array(actual['tcp']),R=np.array(actual['tcp_rotation']),world=w0,pe_m=0.,re_rad=0.,fingers=np.array(actual['finger_joints'])*(1-f)+fingers*f))
# Preserve first issued command exactly; start Cartesian interpolation at its
# FK, not by jumping to measured q and discarding free-space gravity preload.
p0,r0=ik.tcp_pose(q,base);first_tcp=p0.copy();firstR=r0.copy()
waypoints=[('raise_clear',np.array([p0[0],p0[1],.910]),r0),('above_aperture',np.array(route['waypoints'][2]['tcp']),Rtarget),('scoop_staging',np.array(route['waypoints'][3]['tcp']),Rtarget),('inside_descend',np.array(route['continue_existing_waypoints_world'][0]),Rtarget),('underedge_insert',np.array(route['continue_existing_waypoints_world'][1]),Rtarget)]
for name,p1,r1 in waypoints:
 count=max(3,math.ceil(np.linalg.norm(p1-p0)/.002)+1,math.ceil(np.linalg.norm(ik._rot_error(r1,r0))/np.radians(1))+1)
 for f in np.linspace(0,1,count):add(name,p0+f*(p1-p0),ik.slerp_matrix(r0,r1,float(f)),w0,f)
 p0,r0=p1,r1
for f in np.linspace(0,1,5):add('contact_acquire',p0+[0,0,.0008*f],Rtarget,w0,f)
for angle in np.linspace(angle0,-30,int(math.ceil(-30-angle0))+1):
 pp,ww=pose_at(float(angle));add('supported_arc_contact',pp,Rtarget,ww,angle)
results=[];start=time.monotonic()
for index,s in enumerate(samples):
 wp=worldparts(s['q'],s['fingers'],base);hard=(10.,None,None);target=(10.,None,None)
 for link,a in wp:
  gap=float(a[:,:,2].min()-TOP)
  if gap<hard[0]:hard=(gap,link,'table')
  for name,(pp,rr)in s['world'].items():
   gap=separation(a,pp,rr,defs[name]['size'])
   if name=='north_bottom' and link in ('gripper','tip_left','tip_right'):
    if gap<target[0]:target=(gap,link,name)
   elif gap<hard[0]:hard=(gap,link,name)
 lo=np.array([a.reshape(-1,3).min(0)for _,a in wp]);hi=np.array([a.reshape(-1,3).max(0)for _,a in wp]);gaps=np.max(np.maximum(lo[:,None,:]-ohi[None,:,:],olo[None,:,:]-hi[:,None,:]),axis=2);ii,jj=np.unravel_index(np.argmin(gaps),gaps.shape)
 result=dict(phase=s['phase'],value=s['value'],pe_m=s['pe_m'],re_rad=s['re_rad'],hard_min=hard,target_hand_min=target,otherarm_AABB_min_m=float(gaps[ii,jj]),unresolved_otherarm_pairs=int((gaps<0).sum()),closest_otherarm_links=[wp[ii][0],rightparts[jj][0]])
 results.append(result)
 if hard[0]<0 or target[0]<-1e-5 or gaps[ii,jj]<0:print('FLAG',result,flush=True)
print('SAMPLES',len(samples),'pieces',len(raw),'hard',min(r['hard_min']for r in results),'target',min(r['target_hand_min']for r in results),'otherarm',min(r['otherarm_AABB_min_m']for r in results),flush=True)
summary=dict(samples=len(samples),pieces_per_arm=len(raw),hard_min=min(r['hard_min']for r in results),target_hand_min=min(r['target_hand_min']for r in results),otherarm_AABB_min_m=min(r['otherarm_AABB_min_m']for r in results),max_ik_error_m=max(r['pe_m']for r in results),max_ik_rotation_rad=max(r['re_rad']for r in results),passed=all(r['hard_min'][0]>=.0002 and r['target_hand_min'][0]>=-1e-5 and r['otherarm_AABB_min_m']>=.0002 and r['pe_m']<.0001 and r['re_rad']<.002 for r in results))
serialize=[]
for s in samples:serialize.append({k:(v.tolist()if isinstance(v,np.ndarray)else v)for k,v in s.items()if k!='world'})
out=basepath/'review/fullarm-report.json';out.write_text(json.dumps(dict(summary=summary,source_trace_sha256=hashlib.sha256(Path('/private/tmp/carton-cut011-no-video/trajectory.jsonl').read_bytes()).hexdigest(),route_ready_sha256=hashlib.sha256(Path('/private/tmp/astra-outer-scoop-route-ready.json').read_bytes()).hexdigest(),source_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),first_unbiased_command_tcp=first_tcp.tolist(),first_unbiased_command_R=firstR.tolist(),samples=serialize,results=results,scope='CPUdiscrete315correctedcollisionpiecesperarm vs12panels/table/parkedcutter3boxes; otherarmALLpieceAABBpositiveseparation. CommandcontinuousFK(lastissuedq)approach repair + nominalfixedR0.8mmcontacttranslation/partialarc to−30. No continuous/servoerror/nativecontact/frictionproof. Targethandcontactonlyexcludedfromhardmetrics; targetminimumreported.',elapsed_cpu_s=time.monotonic()-start),indent=2)+'\n');print('PASS',summary['passed'],'SHA',hashlib.sha256(out.read_bytes()).hexdigest(),flush=True)
