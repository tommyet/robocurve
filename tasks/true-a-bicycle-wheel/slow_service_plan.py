"""Complete slow service candidate; ordinary robot joint commands only.

Extends the380-action first-quarter diagnostic to six quarters. Native
engagement, full repair and released revolution remain to be demonstrated.
"""
import argparse,hashlib,json,numpy as np
from pathlib import Path
from motion_plan import Compiler,compile_plan,TOOL_TCP,GRIP
from plan_turns import nominal_nipple,rz
from yam_arena import ik,station,YAM_URDF
from yam_arena.constants import READY,SHOULDER,WRIST,GRIPPER,FINGER_OPEN
CLEAR=.045
PARK_X=.23
PARK_Z=.88
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--clock-deg',type=float,default=55.)
args=parser.parse_args();OUT=args.out
CLOCK=float(args.clock_deg)
def rx(a):
 c,s=np.cos(a),np.sin(a);return np.array(((1,0,0),(0,c,-s),(0,s,c)))
c=Compiler();pickup=compile_plan('pickup');c.frames=pickup['frames'];c.audit=pickup['kinematic_audit']
a=np.array(c.frames[-1]['action14']);c.q={'left':a[:6].copy(),'right':a[7:13].copy()};c.opening={'left':a[6],'right':a[13]}
# Frozen empirical grip calibration from the final native036 pickup frame.
# This does not use live object state, move an object, or change contact forces.
TOOL_TCP=np.array((-2.36035952e-05,-.195750892,.0106086037))
GRIP=np.array(((.9999836762514792,.00561312443021827,.0010677381268720367),
 (.0055498403802689295,-.998625086422048,.052126155050139976),
 (.0013588606735889215,-.05211937837972152,-.9986399370618928)))
c.tool_tcp=TOOL_TCP.copy();c.grip=GRIP.copy()

for frame in c.frames:frame['nominal_wheel_clocking_deg']=CLOCK
clock=CLOCK;origin=np.array((.35,0,1.005));current_clock=clock
left_p,left_R=ik.tcp_pose(c.q['left'],station.BASES['left'])
def segment(*args,**kwargs):
 before=len(c.frames);c.segment(*args,**kwargs)
 for frame in c.frames[before:]:frame['nominal_wheel_clocking_deg']=current_clock
 print(args[0],len(c.frames),flush=True)
def tcp(center,R):return center+R@TOOL_TCP,R@GRIP
# A specified alternative IK seed is only a CPU branch search. Joint commands
# still interpolate continuously from the actual previous commanded q.
def joint_branch(label,seconds,center,R,seed):
 p,RR=tcp(center,R);q,pe,re=ik.solve(p,ik.matrix_to_quat_xyzw(RR),np.array(seed),station.BASES['right'],iters=500,damping=.008,tol=1e-7)
 if pe>.0001 or re>.001:raise ValueError((label,pe,re))
 q0=c.q['right'].copy();count=round(seconds*20)
 for k in range(1,count+1):
  c.q['right']=q0+ik.smoothstep(k/count)*(q-q0)
  c.frames.append(dict(stage=label,nominal_wheel_clocking_deg=current_clock,action14=np.r_[c.q['left'],c.opening['left'],c.q['right'],c.opening['right']].tolist()))
 c.audit.append(dict(stage=label,seconds=seconds,interpolation='joint branch',max_position_error_m=pe,max_rotation_error_rad=re))
 print(label,len(c.frames),flush=True)
seed=[1.0487518124666668,2.29124567728882,2.56356940373194,-1.0798518756170759,-.5188898080705516,1.9842609236286477]
try:
 for spoke in (0,2):
  center,n=nominal_nipple(spoke,np.deg2rad(45),np.deg2rad(current_clock));R0=n[:,[1,2,0]]@np.diag((1.,-1.,-1.))@rz(np.pi);R1=R0@rz(np.pi/2)
  pre=center-.010*R0[:,1];clear=pre-np.array((CLEAR,0,0))
  if spoke==0:
   parked=np.array((PARK_X,-.005,PARK_Z))
   segment('Move wrench to front workspace',.6,{'right':tcp(parked,np.eye(3))})
   segment('Orient the wrench in front of wheel',1.5,tool_path=lambda u:(parked,ik.slerp_matrix(np.eye(3),R0,u)))
  joint_branch(f'Clear approach nipple {spoke}',1.2,clear,R0,seed)
  segment(f'Approach nipple {spoke}',.6,{'right':tcp(pre,R0)})
  segment(f'Approach nipple {spoke} settle',1.5)
  for turn in range(3):
   prefix=f'Nipple {spoke} quarter {turn+1}'
   segment(prefix+' insert',1.5,{'right':tcp(center,R0)})
   segment(prefix+' insertion settle',1.5)
   segment(prefix+' tighten',4.,tool_path=lambda u,p=center,R=R0:(p,R@rz(u*np.pi/2)))
   segment(prefix+' tightening settle',1.)
   withdrawn=center-.010*R1[:,1]
   segment(prefix+' disengage',1.,{'right':tcp(withdrawn,R1)})
   front=withdrawn-np.array((CLEAR,0,0))
   segment(prefix+' clear front',.5,{'right':tcp(front,R1)})
   segment(prefix+' reset angle',.7,tool_path=lambda u,p=front:(p,ik.slerp_matrix(R1,R0,u)))
   segment(prefix+' return mouth',.6,{'right':tcp(clear,R0)})
   if turn<2:segment(prefix+' return plane',.6,{'right':tcp(pre,R0)})
  if spoke==0:
   # Move the rim and hand as a single ordinary rigid grasp trajectory. No
   # simulation pose setter or privileged state enters these action commands.
   begin=len(c.frames);q0=c.q['left'].copy();p0,Rold=left_p.copy(),left_R.copy()
   count=30
   for k in range(1,count+1):
    u=ik.smoothstep(k/count);rot=rx(-np.deg2rad(22.5)*u);p=origin+rot@(p0-origin);R=rot@Rold
    q,pe,re=ik.solve(p,ik.matrix_to_quat_xyzw(R),c.q['left'],station.BASES['left'],iters=300,damping=.008,tol=1e-7)
    if pe>.0001 or re>.001:raise ValueError(('index',k,pe,re))
    c.q['left']=q;c.frames.append(dict(stage='Index wheel by one spoke pair',nominal_wheel_clocking_deg=CLOCK-22.5*u,action14=np.r_[q,c.opening['left'],c.q['right'],c.opening['right']].tolist()))
   current_clock=CLOCK-22.5;left_p=p;left_R=R
   c.audit.append(dict(stage='Index wheel by one spoke pair',seconds=1.5,interpolation='Cartesian rim arc'))
 plan=dict(pickup);plan.update(wheel_clocking_deg=CLOCK,requested_stage='repair_candidate',frames=c.frames,kinematic_audit=c.audit,action_count=len(c.frames),seconds=len(c.frames)/20,limitations=['Offline candidate. No grasp or contact proof.','Released final revolution not yet included.'])
 actions=np.asarray([np.r_[READY,1.,READY,1.]]+[f['action14'] for f in c.frames]);limits=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2);plan['max_speed_fraction']=float(np.max(np.abs(np.diff(actions,axis=0))/limits));plan['compile_success']=True
except Exception as e:
 plan=dict(pickup);plan.update(wheel_clocking_deg=CLOCK,requested_stage='repair_candidate',frames=c.frames,kinematic_audit=c.audit,action_count=len(c.frames),seconds=len(c.frames)/20,compile_success=False,error=str(e))
plan['held_grasp_calibration']={'source':'Native036 final pickup, fixed ordinary FK/native tool observation', 'applies_from_step':83,'tcp_position_in_tool_m':TOOL_TCP.tolist(),'tcp_rotation_in_tool':GRIP.tolist(),'limitation':'One empirical grasp; load-dependent slip still requires native verification.'}
plan['source_sha256']['slow_service_plan.py']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps({k:plan.get(k) for k in ('compile_success','error','action_count','max_speed_fraction')}))
