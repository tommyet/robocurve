"""Feedback ordinary face-push closure PREFIX, CPU candidate not nativevalidated.

No model/scorer/force setters. No position PI. Allfour paths have finiteCPUgeometry certificates; nativecontact/dynamics
remainunvalidated. A completedprefix is NOT a fulltaskdemo.
"""
import copy,math
import numpy as np
from yam_arena import ik
from yam_arena.constants import FINGER_OPEN
from carton_scene import layout
from config import PRODUCTS,CELLS,BOARD
from roll_probe import Geometry
from face_push_geometry import FaceTargets,ROUTES,OPENING,FINGER,NORMAL_PRELOAD,LOOKAHEAD_DEG,RELEASE_ANGLE

class InitialForceGate:
 """Singleton selected-body contactpresence, never a pressure calibration."""
 def __init__(self):self.identity=None;self.target=None;self.streak=0
 def consume(self,packet,time,target,side,body,normal,geometric_contact):
  if packet.get('clock_verified')is not True or packet.get('native_filter_target_verified')is not True or packet.get('selected_target')!=target or abs(float(packet.get('requested_control_time_s',-1))-time)>1e-6:raise ValueError('unverified/stale singleton contact packet')
  d=packet['sides'][side];binding=d.get('target_binding',{});names=d['body_names'];a=np.asarray(d['normal_force_matrix_w'],float)
  if binding.get('native_verified')is not True or binding.get('target')!=target or d.get('individual_filter_column_order_native_verified')is not True or d.get('configured_target_family')!=[target]or len(names)!=2 or set(names)!={'tip_left','tip_right'}or a.shape!=(2,1,3)or not np.isfinite(a).all():raise ValueError('singleton target/body force binding mismatch')
  sid=packet.get('sample_id')
  if isinstance(sid,bool)or not isinstance(sid,(int,np.integer))or sid<1:raise ValueError('invalid native contact sample identity')
  identity=(target,int(sid));force=a[names.index(body),0];signed=float(force@np.asarray(normal));total=float(np.linalg.norm(a,axis=-1).sum())
  if total>4.:raise ValueError('selected flap contact force magnitude exceeded4N')
  if self.target!=target:self.target=target;self.identity=None;self.streak=0
  fresh=identity!=self.identity
  if self.identity is not None and sid<self.identity[1]:raise ValueError('native contact sample identity moved backwards')
  if fresh:self.streak=self.streak+1 if geometric_contact and signed>=.05 else 0;self.identity=identity
  return dict(signed_selected_pad_normal_force_N=signed,selected_flap_force_magnitude_sum_N=total,force_sample_identity=list(identity),fresh_force_sample=fresh,initial_force_streak=self.streak,initial_contact_verified=self.streak>=5)

class FacePushClosureProbe:
 ORDER=('east','west','north','south')
 PLAN=('index','stage','started','startq','startg','startp','startr','highq','hoverp','contactp','contactr','command_angle','withdraw_started_angle','parkq','prefix_complete','done','arrival_count','fold_entry_time','fold_entry_angle','last_preload','hold_previous_qualified','standoffq','highp')
 def __init__(self,env,max_flaps=4):
  if isinstance(max_flaps,(bool,np.bool_))or not isinstance(max_flaps,(int,np.integer))or max_flaps not in(1,2,3,4):raise ValueError('bounded prefix_flaps mustbe1..4')
  self.env=env;self.prefix_flaps=max_flaps;self.previous=self.array(env._ready).reshape(-1).astype(np.float32).astype(float);self.geometry=Geometry(fast_certificates=True);parts,hinges=layout();self.parts={p['name']:p for p in parts};self.hinges={h['a']:h for h in hinges if h['b'].endswith('_top')};self.targets=FaceTargets(self.geometry,self.parts,self.hinges,self.pose);self.index=0;self.stage='settle_open';self.started=0.;self.last_time=None;self.last_angles=None;self.settle_count=0;self.failure=None;self.done=False;self.prefix_complete=False;self.pending=None;self.force_gate=InitialForceGate();self.arrival_count=0;self.closed_hold=0.;self.motion_origin=None;self.last_progress_time=None;self.progress_angle=None;self.contact_loss_since=None;self.force_loss_since=None;self.last_preload=0.;self.hold_previous_qualified=False
 @staticmethod
 def array(value):
  value=value.torch if hasattr(value,'torch')else value
  return np.asarray(value.detach().cpu().numpy()if hasattr(value,'detach')else value)
 def pose(self,name):
  from yam_arena.urdf import quat_xyzw_to_matrix
  a=self.array(self.env._base.arena_world.get_pose_w(name))[0]
  if a.shape!=(7,)or not np.isfinite(a).all():raise ValueError('invalid native object pose')
  return a[:3],quat_xyzw_to_matrix(a[3:])
 def angle(self,name):
  _,wr=self.pose(name);_,fr=self.pose(name+'_top');R=wr.T@fr;return float(np.degrees(np.arctan2(R[2,1],R[1,1])))
 @property
 def active_target(self):return self.ORDER[self.index]+'_top'if self.index<4 else None
 def measured(self):
  result=[]
  for side in('left','right'):
   ids,fids=self.env._ids[side+'_robot'];a=self.array(self.env._base.scene[side+'_robot'].data.joint_pos)[0];q=a[ids];f=a[fids]
   if q.shape!=(6,)or f.shape!=(2,)or not np.isfinite(a).all():raise ValueError('invalid native arm readback')
   result.append((q,f,*ik.tcp_pose(q,self.env.rig.bases[side])))
  return result
 def snapshot(self):return {k:copy.deepcopy(getattr(self,k))for k in self.PLAN if hasattr(self,k)}
 def restore(self,state):
  for k in self.PLAN:
   if k not in state and hasattr(self,k):delattr(self,k)
  for k,v in state.items():setattr(self,k,copy.deepcopy(v))
 def change(self,stage,time,m,side):
  self.stage=stage;self.started=time;self.startq=m[side][0].copy();self.startg=float(np.clip(m[side][1].mean()/FINGER_OPEN,0,1));self.startp=m[side][2].copy();self.startr=m[side][3].copy();self.arrival_count=0;self.hold_previous_qualified=False
 def full_guard(self,action,m,poses,contact,name,side,actual=False):
  if actual:return self.geometry.check([v[0]for v in m],[v[1]for v in m],poses,contact,contact_targets={name+'_top'},contact_side=side)
  a=np.asarray(action,float)
  if a.shape!=(14,)or not np.isfinite(a).all()or np.any(a<self.env._low)or np.any(a>self.env._high):return dict(safe=False,reason='nonfinite_or_bounds')
  return self.geometry.check([a[:6],a[7:13]],[[FINGER_OPEN*a[6]]*2,[FINGER_OPEN*a[13]]*2],poses,contact,contact_targets={name+'_top'},contact_side=side)
 def acknowledge_step(self,time,success):
  if self.pending is None:raise RuntimeError('no proposed command to acknowledge')
  if not math.isfinite(time)or abs(time-self.pending['time'])>1e-9:raise ValueError('acknowledgement clock mismatch')
  p=self.pending;self.pending=None
  if success:
   self.previous=p['action'].copy();self.done=p['done_on_success'];self.prefix_complete=p['prefix_on_success'];p['report'].update(step_acknowledged=True,prefix_complete=self.prefix_complete,full_task_completed=False)
   if p['before']['stage']!='fold'and self.stage=='fold':
    self.motion_origin=self.fold_entry_angle;self.progress_angle=self.fold_entry_angle;self.last_progress_time=self.fold_entry_time;self.contact_loss_since=None;self.force_loss_since=None
  else:self.restore(p['before']);self.failure='native env.step failed; proposed command not accepted'
 def command(self,time):
  if self.pending is not None:raise RuntimeError('previous command needs successful/failed env.step ACK')
  if isinstance(time,(bool,np.bool_))or not math.isfinite(time)or time<0 or(self.last_time is not None and abs(time-self.last_time-.05)>1e-6):raise ValueError('fresh20Hz controller clock required')
  dt=.05 if self.last_time is None else time-self.last_time;self.last_time=time
  report=dict(controller='face_push_prefix_CPU_candidate',full_task_completed=False,phase=self.stage,selected_target=self.active_target,flaps_completed=self.index,prefix_complete=self.prefix_complete,failure=self.failure)
  if self.failure:return self.previous.copy(),report
  before=self.snapshot()
  try:
   angles={n:self.angle(n)for n in self.ORDER};vel={n:0. if self.last_angles is None else(angles[n]-self.last_angles[n])/dt for n in self.ORDER};self.last_angles=angles.copy();m=self.measured();name=self.ORDER[min(self.index,3)];d=ROUTES[name];side=0 if d['side']=='left' else 1;age=time-self.started;stage_before=self.stage;contact=stage_before in('normal_close','acquire','fold','withdraw')or(stage_before=='enter'and d['relief']==0.);target=None;rotation=None;g=OPENING;normal_law={};out=self.previous.copy();witness=None;force={};names=[*self.parts,*[p[0]for p in PRODUCTS],'roll','cutter',*[f'tape_{i}'for i in range(CELLS)]];poses={n:self.pose(n)for n in names}
   if any(abs(angles[n])>1. for n in self.ORDER[:self.index]):raise ValueError('released prior flap reopened')
   if self.index<4 and not d['enabled']and self.stage!='prefix_complete':raise ValueError(name+' acquisition route is not CPU-validated/enabled')
   if self.stage=='settle_open':
    stable=all(-175.1<=angles[n]<=-174.5 and abs(vel[n])<=.5 for n in self.ORDER[self.index:]);self.settle_count=self.settle_count+1 if stable else 0
    if age>8.:raise ValueError('open flaps did not naturally settle within8s')
    if self.settle_count>=5:
     p,R,w=self.targets.target(name,angles[name]);self.contactp=p;self.contactr=R;relief=np.asarray(w['face_normal_world'])*d['relief'];self.hoverp=p-R[:,2]*d['hover'];hq,pe,re=ik.solve(self.hoverp,ik.matrix_to_quat_xyzw(R),np.asarray(d['seed']),base_pos=self.env.rig.bases[d['side']],iters=220,tol=1e-6)
     if pe>.0003 or re>.003:raise ValueError('reviewed sidehover IK unavailable')
     self.highp=self.hoverp+[0,0,d['high']];q,pe,re=ik.solve(self.highp,ik.matrix_to_quat_xyzw(R),hq,base_pos=self.env.rig.bases[d['side']],iters=220,tol=1e-6)
     if pe>.0003 or re>.003:raise ValueError('reviewed highhover IK unavailable')
     self.highq=q
     if d['standoff']is not None:
      sq,spe,sre=ik.solve(np.asarray(d['standoff']),ik.matrix_to_quat_xyzw(R),hq,base_pos=self.env.rig.bases[d['side']],iters=220,tol=1e-6)
      if spe>.0003 or sre>.003:raise ValueError('reviewed aboveboxstandoff IK unavailable')
      self.standoffq=sq
     self.change('approach_high',time,m,side)
   elif self.stage=='approach_high':
    goalq=self.highq if d['standoff']is None else self.standoffq;b=ik.smoothstep(age/6.);out[7*side:7*side+6]=self.startq+b*(goalq-self.startq);g=self.startg+(OPENING-self.startg)*b
    if age>=6 and np.max(abs(m[side][0]-goalq))<.025 and abs(m[side][1].mean()-FINGER)<.001:self.change('lower_side'if d['standoff']is None else'transfer_high',time,m,side)
    if age>12:raise ValueError('highhover measured arrival timed out')
   elif self.stage in('transfer_high','lower_side','relieve','enter','normal_close'):
    p,R,witness=self.targets.target(name,angles[name]);relief=np.asarray(witness['face_normal_world'])*d['relief'];goal=p-R[:,2]*d['hover']+[0,0,d['high']]if self.stage=='transfer_high'else p-R[:,2]*d['hover']if self.stage=='lower_side'else p+relief-R[:,2]*d['hover']if self.stage=='relieve'else p+relief if self.stage=='enter'else p;duration=4. if self.stage=='transfer_high'else 1. if self.stage in('relieve','normal_close')else 2.;b=ik.smoothstep(age/duration);target=self.startp+b*(goal-self.startp);rotation=ik.slerp_matrix(self.startr,R,b);arrived=np.linalg.norm(m[side][2]-goal)<.002 and np.linalg.norm(ik._rot_error(R,m[side][3]))<.04 and abs(m[side][1].mean()-FINGER)<.001;self.arrival_count=self.arrival_count+1 if age>=duration and arrived else 0
    if self.arrival_count>=5:
     nextstage={'transfer_high':'lower_side','lower_side':'relieve'if d['relief']else'enter','relieve':'enter','enter':'normal_close'if d['relief']else'acquire','normal_close':'acquire'}[self.stage];self.change(nextstage,time,m,side)
    if age>8:raise ValueError('measured sideentry arrival timed out')
   elif self.stage in('acquire','fold'):
    _,_,witness=self.targets.target(name,angles[name]);gap=self.targets.measured_gap(name,d['side'],m[side][0],m[side][1],witness['body']);geom=abs(gap)<=.001 and abs(m[side][1].mean()-FINGER)<.001;reader=getattr(self.env,'_closure_contact_reader',None)
    if reader is None:raise ValueError('verified singleton contact reader required')
    packet=reader.read(time,phase='pre_action',target=name+'_top');force=self.force_gate.consume(packet,time,name+'_top',d['side'],witness['body'],witness['face_normal_world'],geom)
    if self.stage=='acquire':
     preload=NORMAL_PRELOAD*ik.smoothstep(age/1.5);target,rotation,witness=self.targets.target(name,angles[name],preload)
     if force['initial_contact_verified']and age>=1.5:
      self.command_angle=angles[name];self.fold_entry_angle=angles[name];self.fold_entry_time=time;self.last_preload=preload;self.change('fold',time,m,side)
     if age>5.:raise ValueError('selected innerpad did not acquire5fresh.05Ncontacts')
    else:
     if angles[name]>=self.progress_angle+.5:self.progress_angle=angles[name];self.last_progress_time=time
     if age>3 and angles[name]<self.motion_origin+2.:raise ValueError('measured hinge motion below2deg within3s of forceacquisition')
     if time-self.last_progress_time>5:raise ValueError('measured hinge stopped progressing')
     self.contact_loss_since=time if not geom and self.contact_loss_since is None else self.contact_loss_since if not geom else None
     lost=angles[name]<-100 and force['signed_selected_pad_normal_force_N']<.02;self.force_loss_since=time if lost and self.force_loss_since is None else self.force_loss_since if lost else None
     if(self.contact_loss_since is not None and time-self.contact_loss_since>.5)or(self.force_loss_since is not None and time-self.force_loss_since>.5):raise ValueError('earlyloaded face contact was lost')
     normal_law=self.targets.normal_reference(name,angles[name],m[side][0],self.env.rig.bases[d['side']],witness,force['signed_selected_pad_normal_force_N']);depth=normal_law['total_normal_depth_reference_m'];lookahead=min(LOOKAHEAD_DEG,float(np.degrees(.5*depth/d['radius'])));self.command_angle=min(RELEASE_ANGLE,angles[name]+lookahead,max(angles[name],self.command_angle)+5.*dt);basep,rotation,nextw=self.targets.target(name,self.command_angle);actualfp,actualfr=self.pose(name+'_top');futurecontact=basep+rotation@np.asarray(nextw['support_tcp']);lookdepth=max(0.,BOARD/2-float((futurecontact-actualfp)@actualfr[:,2]));wanted=max(0.,depth-lookdepth);self.last_preload=float(np.clip(wanted,max(0.,self.last_preload-.00005),min(NORMAL_PRELOAD,self.last_preload+.00005)));target=basep+np.asarray(witness['push_world'])*self.last_preload;witness=nextw;normal_law.update(applied_extra_normal_preload_m=self.last_preload,lookahead_normal_depth_m=lookdepth,applied_total_normal_depth_m=lookdepth+self.last_preload,applied_angular_lookahead_deg=self.command_angle-angles[name])
     if angles[name]>=RELEASE_ANGLE:
      if angles[name]>-69. or abs(vel[name])>15.:raise ValueError('release state outside verified moving-flap envelope')
      self.withdraw_started_angle=angles[name];self.change('withdraw',time,m,side)
     if age>45:raise ValueError('facepush motion deadline')
   elif self.stage=='withdraw':
    if angles[name]<-70.5 or angles[name]>self.withdraw_started_angle+15.*min(age,1.)+.5 or abs(vel[name])>15.:raise ValueError('moving flap exceeded withdrawal envelope')
    p,R,witness=self.targets.target(name,angles[name]);target=p-R[:,2]*(.04*ik.smoothstep(age));rotation=R
    if age>=1 and np.linalg.norm(m[side][2]-target)<.003:self.closed_hold=0.;self.change('gravity_settle',time,m,side)
    if age>2.:raise ValueError('lateralwithdraw measured arrival timed out')
   elif self.stage=='gravity_settle':
    qualified=abs(angles[name])<=1. and abs(vel[name])<=1.;self.closed_hold=self.closed_hold+dt if qualified and self.hold_previous_qualified else 0.;self.hold_previous_qualified=qualified
    if self.closed_hold>=1.:self.parkq=self.env._ready.detach().cpu().numpy().reshape(-1)[7*side:7*side+6].copy();self.change('park',time,m,side)
    if age>22.:raise ValueError('released flap did not naturally close andsettle')
   elif self.stage=='park':
    b=ik.smoothstep(age/5.);out[7*side:7*side+6]=self.startq+b*(self.parkq-self.startq);g=self.startg+(1.-self.startg)*b
    if age>=5 and np.max(abs(m[side][0]-self.parkq))<.025 and np.mean(m[side][1])/FINGER_OPEN>.9:self.closed_hold=0.;self.change('released_hold',time,m,side)
    if age>12.:raise ValueError('measured park arrival timed out')
   elif self.stage=='released_hold':
    qualified=all(abs(angles[n])<=1 and abs(vel[n])<=1 for n in self.ORDER[:self.index+1]);self.closed_hold=self.closed_hold+dt if qualified and self.hold_previous_qualified else 0.;self.hold_previous_qualified=qualified
    if self.closed_hold>=2.:
     self.index+=1
     if self.index>=self.prefix_flaps:self.prefix_complete=True;self.done=True;self.stage='prefix_complete'
     else:self.settle_count=0;self.change('settle_open',time,m,side)
    if age>8.:raise ValueError('released closed hold did not persist')
   elif self.stage!='prefix_complete':raise ValueError('unsupported facepush phase')
   if target is not None:
    q,pe,re=ik.solve(target,ik.matrix_to_quat_xyzw(rotation),m[side][0],base_pos=self.env.rig.bases[d['side']],iters=160,tol=1e-6)
    if pe>.0003 or re>.003:raise ValueError('live facepush IK unavailable')
    out[7*side:7*side+6]=q
   if stage_before not in('settle_open','gravity_settle','released_hold','prefix_complete'):out[7*side+6]=g
   delta=np.array([.04]*6+[.05]+[.04]*6+[.05]);out=np.clip(out,self.previous-delta,self.previous+delta);out=np.clip(out,self.env._low,self.env._high).astype(np.float32).astype(float)
   for j in range(14):
    if abs(out[j]-self.previous[j])>delta[j]:out[j]=float(np.nextafter(np.float32(out[j]),np.float32(self.previous[j])))
   if np.any(abs(out-self.previous)>delta):raise ValueError('float32 target slew exceeded')

   if np.any(out<self.env._low)or np.any(out>self.env._high):raise ValueError('float32 canonical target exceeds jointbound')
   actual=self.full_guard(out,m,poses,contact,name,side,actual=True)
   if not actual['safe']:raise ValueError('measured full315 clearance rejected')
   proposed=self.snapshot();accepted=None;trials=[];fraction=0.
   for alpha in(1.,.5,.25,.125,.0625):
    candidate=(self.previous+alpha*(out-self.previous)).astype(np.float32).astype(float)
    if np.any(abs(candidate-self.previous)>delta):raise ValueError('float32 line-search slew exceeded')
    cg=self.full_guard(candidate,m,poses,contact,name,side);trials.append(dict(fraction=alpha,clearance=cg))
    if cg['safe']:accepted=candidate;fraction=alpha;break
   if accepted is None:
    oldguard=self.full_guard(self.previous,m,poses,contact,name,side)
    if not oldguard['safe']:raise ValueError('no admissible command and fresh previous hold unsafe')
    accepted=self.previous.copy();self.restore(before)
   elif fraction<1.:self.restore(before)
   done_on_success=self.done;prefix_on_success=self.prefix_complete;self.done=before['done'];self.prefix_complete=before['prefix_complete'];report.update(phase=name+':'+stage_before,selected_target=name+'_top',flap_angles_deg=angles,flap_angular_velocity_deg_s=vel,active_arm=d['side'],pad_witness=witness,force=force,normal_force_reference=normal_law,normal_preload_cap_m=NORMAL_PRELOAD,angular_lookahead_deg=LOOKAHEAD_DEG,advance_fraction=fraction,clearance_actual=actual,advance_trials=trials,proposed_stage=proposed['stage'],planner_transition_accepted=fraction==1.,flaps_completed=self.index,prefix_complete=self.prefix_complete,full_task_completed=False,failure=None)
   self.pending=dict(time=time,action=accepted.copy(),before=before,done_on_success=done_on_success,prefix_on_success=prefix_on_success,report=report)
   return accepted.copy(),report
  except(ValueError,KeyError,IndexError,TypeError,AttributeError)as error:
   self.restore(before);self.failure=str(error);self.pending=None;report.update(failure=self.failure,not_issued=True,full_task_completed=False);return self.previous.copy(),report
