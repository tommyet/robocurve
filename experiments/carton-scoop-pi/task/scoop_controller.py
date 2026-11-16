"""Privileged UNSCORED north-flap presentation; ordinary14D targets only."""
import numpy as np
from capture import array
from config import TOP
from crease import physical_bottom_angle
from scene import layout
from yam_arena import ik
from yam_arena.constants import FINGER_OPEN
from yam_arena.urdf import quat_xyzw_to_matrix,axis_angle_matrix
from fast_safety import ScoopSafety
from joint_position_pi import JointPositionPI

CONTACT_PHASES=('contact_acquire','supported_arc')


def bounded_path_step(fraction,dt,length,angle,speed,angular_speed=.35,allowed=True):
 if not np.isfinite([fraction,dt,length,angle,speed,angular_speed]).all()or not 0<=fraction<=1 or not 0<=dt<=.05 or min(length,angle)<0 or min(speed,angular_speed)<=0:raise ValueError('invalid bounded path state')
 return min(1.,fraction+dt/max(length/speed,angle/angular_speed,.05))if allowed else fraction


def limit_reference(previous_point,previous_R,point,R,dt,speed,angular_speed=.35):
 """Keep Cartesian stage handoffs continuous at the existing speed limits."""
 if not np.isfinite([dt,speed,angular_speed]).all()or not 0<=dt<=.05 or min(speed,angular_speed)<=0:raise ValueError('invalid reference limit')
 delta=np.asarray(point)-previous_point;length=np.linalg.norm(delta)
 point=np.asarray(previous_point)+delta*min(1.,speed*dt/length)if length>0 else np.asarray(previous_point).copy()
 angle=np.linalg.norm(ik._rot_error(R,previous_R));rotation=ik.slerp_matrix(previous_R,R,min(1.,angular_speed*dt/angle))if angle>0 else np.asarray(previous_R).copy()
 return point,rotation


class OuterNorthScoop:
 """Measured safety/angle gates; no policy pose writes, wrench or scorer access."""
 def __init__(self,env,snapshot,route):
  self.env=env;self.snapshot=snapshot;self.route=route;self.previous=None;self.failure=None;self.done=False;self.phase=0;self.motion=None;self.last_time=None;self.stable=0;self.last_advance=0.;self.contact_since=None;self.last_angle=None;self.initial_angle=None;self.last_angle_progress=0.;self.command_angle=None
  if route.get('active_hand')!='left' or route.get('target_flap')!='north_bottom':raise ValueError('only reviewedleft/northcoupon supported')
  self.R=np.array(route['support_R'],dtype=float);self.point=np.array(route['support_point_tcp'],dtype=float)
  if self.R.shape!=(3,3)or self.point.shape!=(3,)or not np.isfinite(self.R).all()or not np.isfinite(self.point).all()or not np.allclose(self.R.T@self.R,np.eye(3),atol=1e-6,rtol=0.):raise ValueError('invalid reviewed support frame')
  self.safety=ScoopSafety();self.hinge=next(h for h in layout()[1]if h['b']=='north_bottom')
 def begin(self,issued):
  if self.previous is not None:raise RuntimeError('scoop start cannot be rebased')
  issued=np.asarray(issued,dtype=float)
  if issued.shape!=(14,)or not np.isfinite(issued).all():raise ValueError('finite14Dissuedcommand required')
  self.previous=issued.copy();self.nominal=issued.copy();self.pi=JointPositionPI(ik.LOWER,ik.UPPER);self.pi.begin(issued[:6],0.);p,R=ik.tcp_pose(issued[:6],self.env.rig.bases['left'])
  # The exact first arm command is retained; its FK is the free-approach start.
  lift=float(self.route.get('contact_acquire_lift_m',.0008))
  if not np.isfinite(lift) or not 0.<lift<=.006:raise ValueError('unreviewed contact acquisition stroke')
  self.waypoints=[('raise_clear',np.array([p[0],p[1],.910]),R,.020),
   ('above_aperture',np.array(self.route['above_aperture']),self.R,.020),
   ('scoop_staging',np.array(self.route['staging']),self.R,.020),
   ('inside_descend',np.array(self.route['inside']),self.R,.005),
   ('underedge_insert',np.array(self.route['insert']),self.R,.005),
   ('contact_acquire',np.array(self.route['insert'])+[0,0,lift],self.R,.001)]
  self.first_pose=(p,R)
 def state(self):
  data={}
  for side in ('left','right'):
   ids,fids=self.env._ids[side+'_robot'];native=array(self.env._base.scene[side+'_robot'].data.joint_pos)[0];q=native[ids];f=native[fids];p,R=ik.tcp_pose(q,self.env.rig.bases[side]);data[side]=(q,f,p,R)
  poses={}
  for n in [p['name']for p in layout()[0]]+['cutter']:
   pose=array(self.env._base.arena_world.get_pose_w(n))[0]
   if pose.shape!=(7,)or not np.isfinite(pose).all():raise ValueError('missing/nonfinite native panel/cutter pose')
   poses[n]=pose
  cutter=poses.pop('cutter')
  observer=getattr(self.env._base,'_carton_angle_observer',None)
  if observer is None or observer.tracker.failure:raise ValueError('continuous diagnostic angle history unavailable')
  angle=float(observer.tracker.angles[0])
  contacts=[]
  for link in ('gripper','tip_left','tip_right'):
   v=array(self.env._base.scene['open_contact_'+link].data.force_matrix_w)
   if v.shape!=(1,1,12,3)or not np.isfinite(v).all():raise ValueError('native singlebody12filtercontact data missing/nonfinite')
   contacts.append(v[0,0])
  forces=np.array(contacts);target_index=[p['name']for p in layout()[0]].index('north_bottom')
  target_force=float(np.linalg.norm(forces[2,target_index]));mask=np.ones((3,12),dtype=bool);mask[2,target_index]=False;otherforce=float(np.linalg.norm(forces,axis=2)[mask].max())
  return data,poses,cutter,angle,target_force,otherforce
 def stop(self,reason,**details):self.failure=reason;return self.previous.copy(),[dict(phase='failed',failure=reason,**details)]
 def command(self,time):
  if self.previous is None:raise RuntimeError('begin(previous14D) required')
  if self.failure or self.done:return self.previous.copy(),[dict(phase='partial_scoop_complete'if self.done else'failed',failure=self.failure,partial_only=True)]
  if not np.isfinite(time)or time<0 or (self.last_time is not None and (time<self.last_time or time-self.last_time>.051)):return self.stop('missing/nonmonotonic diagnosticclock')
  dt=0. if self.last_time is None else min(.05,time-self.last_time);first=self.last_time is None;self.last_time=time
  try:data,poses,cutter,angle,target_force,otherforce=self.state()
  except (ValueError,KeyError,IndexError,TypeError,AttributeError)as error:return self.stop(str(error))
  qa,fingers,tcp,Ractual=data['left'];rq,rf,_,_=data['right'];contact=self.phase>=5
  actual=self.safety.check(qa,fingers,poses,cutter,rq,rf,contact=contact)
  if not actual['safe']:return self.stop('actualnon-targetgeometry below0.2mm: '+str(actual))
  if target_force>1. or otherforce>.1:return self.stop('diagnosticforcebound exceeded')
  if not contact and target_force>.02:return self.stop('targetcontact beforeacquisitionphase')
  if time>220.:return self.stop('bounded220sdiagnosticcontroller budget')
  if np.linalg.norm(cutter[:3]-np.array(self.snapshot['cutter_pose'][:3]))>.002:return self.stop('parkedcutter displaced')
  if self.initial_angle is None:self.initial_angle=angle;self.last_angle=angle;self.last_angle_progress=time
  if first:
   proposal=self.pi.propose(self.nominal[:6],qa,time)
   resolution=self.pi.resolve(proposal,guard_safe=bool(actual['safe']))
   if not resolution.accepted:return self.stop('PI initial handoff rejected')
   self.last_advance=time
   return self.previous.copy(),[dict(phase='ordinary_command_handoff',failure=None,actual_safety=actual,angle_deg=angle)]
  if self.phase<6:
   name,goal,Rgoal,speed=self.waypoints[self.phase]
   if self.motion is None:
    start,Rstart=ik.tcp_pose(self.nominal[:6],self.env.rig.bases['left']);self.motion=dict(start=start,Rstart=Rstart,fraction=0.)
   m=self.motion;fraction=m['fraction'];point=m['start']+fraction*(goal-m['start']);rotation=ik.slerp_matrix(m['Rstart'],Rgoal,fraction)
   err=float(np.linalg.norm(point-tcp));rot_error=float(np.linalg.norm(ik._rot_error(rotation,Ractual)))
   allowed=err<=.002 and rot_error<=np.radians(1.)
   updated=bounded_path_step(fraction,dt,float(np.linalg.norm(goal-m['start'])),float(np.linalg.norm(ik._rot_error(Rgoal,m['Rstart']))),speed,allowed=allowed)
   point=m['start']+updated*(goal-m['start']);rotation=ik.slerp_matrix(m['Rstart'],Rgoal,updated)
  else:
   name='supported_arc';rotation=self.R
   if self.command_angle is None:self.command_angle=angle
   if self.command_angle-angle>=2.:return self.stop('measuredflaplead reached2degrees')
   if target_force<.02:
    self.contact_since=time if self.contact_since is None else self.contact_since
    if time-self.contact_since>1.:return self.stop('supportedcontact lost')
    updated=self.command_angle
   else:
    self.contact_since=None;updated=min(-30.,angle+1.8,self.command_angle+np.degrees(.005/.087)*dt)
   wp,fp=poses['north'],poses['north_bottom'];wr,fr=quat_xyzw_to_matrix(wp[3:]),quat_xyzw_to_matrix(fp[3:]);axis=wr[:,0];hinge=fp[:3]+fr@np.array(self.hinge['anchor_b']);future=axis_angle_matrix(axis,np.radians(updated-angle))@fr;center=hinge-future@np.array(self.hinge['anchor_b']);witness=center-future[:,1]*.0435-future[:,2]*.0015
   local=self.point.copy();local[0]+=-fingers[1]-.003;point=witness-self.R@local
   if angle>self.last_angle+.1:self.last_angle=angle;self.last_angle_progress=time
   if time-self.last_angle_progress>5.:return self.stop('no measuredflapangularprogress for5s')
   err=float(np.linalg.norm(point-tcp));rot_error=float(np.linalg.norm(ik._rot_error(rotation,Ractual)))
   if angle>=-30. and angle-self.initial_angle>=40.:
    self.stable+=1
    if self.stable>=5:self.done=True
   else:self.stable=0
  previous_point,previous_R=ik.tcp_pose(self.nominal[:6],self.env.rig.bases['left'])
  point,rotation=limit_reference(previous_point,previous_R,point,rotation,dt,.005 if self.phase>=6 else speed)
  q,pe,re=ik.solve(point,ik.matrix_to_quat_xyzw(rotation),self.nominal[:6],base_pos=self.env.rig.bases['left'],iters=800 if contact else 240,tol=1e-6 if contact else 1e-4)
  if pe>(.000002 if contact else.0001)or re>.002:return self.stop('reviewedtargetIK residual')
  out=self.nominal.copy();out[:6]=q;out[6]=.003/abs(FINGER_OPEN)
  out=np.clip(out,self.nominal-np.array([.04]*6+[.05]+[.04]*6+[.05]),self.nominal+np.array([.04]*6+[.05]+[.04]*6+[.05]));out=np.clip(out,self.env._low,self.env._high)
  nominal_out=out.copy()
  proposal=self.pi.propose(nominal_out[:6],qa,time)
  out[:6]=proposal.command
  predicted=self.safety.check(out[:6],fingers,poses,cutter,rq,rf,contact=contact)
  resolution=self.pi.resolve(proposal,guard_safe=bool(actual['safe'] and predicted['safe']))
  if not resolution.accepted:return self.stop('augmented command rejected before stepping: '+str(predicted),rejected_command_14d=out.tolist(),nominal_candidate_14d=nominal_out.tolist(),proposed_bias_rad=list(proposal.proposed_bias),command_safety=predicted,actual_safety=actual,desired_tcp=point.tolist(),desired_R=rotation.tolist(),pi_committed=False)
  path_accepted=resolution.path_dt_s>0.
  if path_accepted:self.nominal=nominal_out
  self.previous=out
  if not path_accepted:
   if self.phase<6:updated=fraction
   else:updated=self.command_angle
  if self.phase<6:
   if updated>fraction+1e-12:self.last_advance=time
   m['fraction']=updated
   settled=updated>=1.-1e-12 and np.linalg.norm(goal-tcp)<=.001 and np.linalg.norm(ik._rot_error(Rgoal,Ractual))<=np.radians(1.)
   if name=='contact_acquire':settled=settled and target_force>=.02
   self.stable=self.stable+1 if settled else 0
   if self.stable>=5:
    self.phase+=1;self.motion=None;self.stable=0;self.last_advance=time
    if self.phase==6:self.last_angle_progress=time;self.last_angle=angle;self.command_angle=angle;self.contact_since=None
   if time-self.last_advance>8.:return self.stop('no accepted motion progress for8s')
  else:self.command_angle=updated
  return out.copy(),[dict(phase=name,angle_deg=angle,target_force_N=target_force,max_non_target_hand_force_N=otherforce,actual_safety=actual,command_safety=predicted,desired_tcp=point.tolist(),actual_tcp=tcp.tolist(),ik_error_m=pe,ik_rotation_rad=re,phase_fraction=updated if self.phase<6 else None,command_angle_deg=self.command_angle,partial_only=True,pi_bias_rad=self.pi.bias.tolist(),nominal_joints=self.nominal[:6].tolist(),pi_path_accepted=path_accepted,failure=self.failure)]
