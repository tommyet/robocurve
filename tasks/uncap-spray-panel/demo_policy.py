"""Measured-state side-grip demo; ordinary bounded 14D commands only.

No pose writes, forces, joint removal, deposit writes or scorer updates here.
The policy receives privileged simulation telemetry for planning, disclosed.
"""
from dataclasses import replace
import json
from pathlib import Path
import numpy as np
from yam_arena import ik
from yam_arena.constants import FINGER_OPEN
from yam_arena.urdf import axis_angle_matrix
from yam_arena.scripted import YamScriptedPolicy
from inspect_robots.types import Action,ActionChunk
from inspect_robots_yam.packing import pack
from config import *
import telemetry
from control_math import (grip_fraction,ramp_scalar,can_frame_ramp_translation,transport_can_reference,actual_face_tcp_target,GRASP_OFFSET,RELEASE_DISTANCE,RELEASE_SPEED,
                          RELEASE_DEADLINE,MEASURED_DWELL,calibrated_hand_target,grasp_drift,release_command_target,release_clearance,release_gate_frames,
                          minimum_future_seconds,press_contact_state,press_bias_step)

LEFT_PRELOAD_SPEED=.005
RIGHT_PRESS_SPEED=.010

_GRASP_PITCH=np.radians(15.)
LEFT_R=np.array([[0.,-np.sin(_GRASP_PITCH),np.cos(_GRASP_PITCH)],
                 [-1.,0.,0.],[0.,-np.cos(_GRASP_PITCH),-np.sin(_GRASP_PITCH)]])
RIGHT_R=np.array([[1.,0.,0.],[0.,0.,1.],[0.,-1.,0.]])
# A real lower-finger face from the pinned YAM collision meshes, at joint7=-28mm.
# This orientation makes that face horizontal; the spare jaw stays above it.
_FACE=json.loads(Path(__file__).with_name('press_face.json').read_text())
PRESS_POINT=np.array(_FACE['point_tcp'])
PRESS_R=np.array(_FACE['rotation_can_from_tcp'])
PRESS_FACE=np.array(_FACE['triangle_tcp'])


class SprayDemo(YamScriptedPolicy):
    def __init__(self,cap_only=False,press_only=False):
        super().__init__();self.info=replace(self.info,name='spray_feedback_demo')
        self.cap_only=cap_only
        self.press_only=press_only

    def reset(self,scene):self.started=False

    def initialize(self):
        self.started=True;self.index=-1;self.failure=None;self.moves=[]
        self.episode_t0=float(telemetry.latest['time'])
        self.press_depth=.0027;self.grasp_calibrated=False;self.holding_can=False;self.press_enabled=True
        self.contact_time=0.;self.press_grip=grip_fraction(-.028,FINGER_OPEN)
        self.targets=[];self.q=[]
        self.position_bias=[np.zeros(3),np.zeros(3)]
        self.left_preload=0.;self.left_preload_target=0.
        self.release_state=None;self.release_path=None;self.release_frames=0;self.release_gap=None
        self.follow_can_pose=None
        self.face_witness_previous=None;self.face_diagnostics={}
        self.last_actions=[np.r_[h['joints'],h['opening']] for h in telemetry.latest['hands']]
        self.rotation_bias=[np.zeros(3),np.zeros(3)]
        for h in telemetry.latest['hands']:
            self.targets.append([np.array(h['tcp']),np.array(h['rotation']),h['opening']])
            self.q.append(np.array(h['joints']))
        can=np.array(telemetry.latest['can']);cap=np.array(telemetry.latest['cap'])
        left=can+GRASP_OFFSET
        self.grip=grip_fraction(-.021,FINGER_OPEN);cap_grip=grip_fraction(-.025,FINGER_OPEN)
        self.hold_grip=grip_fraction(-.018,FINGER_OPEN)
        def move(label,seconds,L=None,R=None,check=None,follow=False,aim=None):
            self.moves.append(dict(label=label,seconds=seconds,L=L,R=R,check=check,follow=follow,aim=aim))
        def lp(p,g):return (np.array(p),LEFT_R,g)
        def rp(p,g):return (np.array(p),RIGHT_R,g)
        move('brace_approach',2.,L=lp(left+(-.060,0.,.015),1.))
        move('brace_enter',2.,L=lp(left,1.))
        move('brace_grip',1.5,L=lp(left,self.grip))
        move('cap_approach',2.,R=rp(cap+(0.,-.10,.0),1.))
        move('cap_enter',2.,R=rp(cap,1.))
        move('cap_grip',1.5,R=rp(cap,cap_grip))
        move('cap_pull',3.,R=rp(cap+(0.,0.,.065),cap_grip),check='detached')
        park=np.array((CAP_PAD[0],CAP_PAD[1],TOP+.022))
        move('cap_carry',3.,R=rp(park+(0.,0.,.065),cap_grip))
        move('cap_lower',2.,R=rp(park,cap_grip))
        move('cap_release',1.,R=rp(park,1.))
        move('cap_retreat',2.,R=rp(park+(-.04,.02,.08),1.),check='parked')
        if self.cap_only:
            move('diagnostic_hold',1.)
            return
        can_center=np.array(SPRAY_TRANSIT_CAN)
        move('can_lift',2.,L=lp(can_center+GRASP_OFFSET,self.hold_grip))
        move('press_approach',2.,R=(can_center+(0.,-.08,.14),PRESS_R,self.press_grip))
        move('press_hover',1.5,follow='hover')
        # One stationary plaque, using the previously exercised first-sector hold.
        p=np.array(SPRAY_HELD_CAN)+GRASP_OFFSET
        move('coat_position_0',1.8,L=lp(p,self.hold_grip),follow='hover')
        move('coat_aim_0',1.2,follow='hover',aim=TARGET_CENTER)
        move('coat_shot_0',8.,follow='press',aim=TARGET_CENTER)
        move('coat_unpress_0',RELEASE_DEADLINE,follow='release')
        move('finish_coating',.3,check='coat')
        move('press_retreat',2.,R=rp(can_center+(0.,-.09,.07),1.))
        move('finish_hold',6.)
        if self.press_only:self.moves=self.moves[:3]+self.moves[11:]

    def next(self,now):
        if self.failure:return
        self.index+=1;self.t0=now
        self.starts=[(p.copy(),r.copy(),g) for p,r,g in self.targets]
        if self.index>=len(self.moves):return
        step=self.moves[self.index]
        if step['follow'] not in ('hover','press'):
            self.follow_can_pose=None;self.face_witness_previous=None;self.face_diagnostics={}
        if step['label'].startswith('coat_shot'):
            self.left_preload_target=.014
            self.contact_time=0.
        if step['label'].startswith('coat_unpress'):
            s=telemetry.latest;hand=s['hands'][1]
            start=np.array(hand['tcp']);rotation=np.array(hand['rotation'])
            axis=np.array(s['can_rotation'])[:,2]
            self.release_state=(start.copy(),rotation.copy(),axis.copy());self.release_frames=0
            commandp,commandR=ik.tcp_pose(self.q[1],self._bases['right'])
            goal=start+RELEASE_DISTANCE*axis
            try:_,_,duration=release_command_target(commandp,goal,0.)
            except ValueError as error:self.failure=str(error);return
            deadline=duration+.014/LEFT_PRELOAD_SPEED+.5
            future=self.moves[self.index+1:]
            reserve=minimum_future_seconds(future)+(len(future)+1)*self._dt
            if deadline>RELEASE_DEADLINE or now-self.episode_t0+deadline+reserve>120.:
                self.failure='release command path cannot fit the remaining 120 second episode budget';return
            step['seconds']=deadline
            self.release_path=dict(start=commandp.copy(),rotation=commandR.copy(),goal=goal.copy(),
                                   goal_rotation=rotation.copy(),duration=duration,initial_q=self.q[1].copy(),
                                   can_pose=(np.array(s['can']).copy(),np.array(s['can_rotation']).copy()))
            # The already-issued motor command is the path anchor. Do not
            # reinterpret its load deflection as a larger Cartesian integral.
            self.position_bias[1][:]=0.;self.rotation_bias[1][:]=0.
        if step['label']=='can_lift' and not self.grasp_calibrated:
            s=telemetry.latest;can_rot=np.array(s['can_rotation'])
            hand=s['hands'][0];offset=can_rot.T@(np.array(hand['tcp'])-np.array(s['can']))
            hold_rotation=can_rot.T@np.array(hand['rotation'])
            self.grasp_offset=offset.copy();self.grasp_rotation=hold_rotation.copy()
            for future in self.moves[self.index:]:
                if future['L'] is not None:
                    p,r,g=future['L'];future['L']=(calibrated_hand_target(p,offset),hold_rotation,g)
            self.grasp_calibrated=True
            self.holding_can=True
        if isinstance(step['R'],str) and step['R']=='unpress':
            p=np.array(telemetry.latest['can'])+np.array((0.,-.006,.12))
            step['R']=(p,RIGHT_R,0.)
        telemetry.events.append(dict(time=now,event='phase',phase=step['label']))

    def act(self,observation):
        if not self.started:self.initialize()
        now=float(observation.state_time);s=telemetry.latest
        if now-self.episode_t0>=120.:
            self.failure=self.failure or '120 second episode limit reached before next action'
            telemetry.command=dict(phase='episode_limit',errors={},failure=self.failure,left_command_finger_joint_m=float(self.last_actions[0][6]*FINGER_OPEN))
            return ActionChunk(actions=[Action(data=pack(*self.last_actions),meta={'request_stop':True})],control_hz=1/self._dt)
        if self.index<0:self.next(now)
        if abs(s['time']-now)>.075:raise RuntimeError('stale demo telemetry')
        if self.grasp_calibrated and self.holding_can:
            hand=s['hands'][0]
            self.failure=self.failure or grasp_drift(s['can'],s['can_rotation'],hand['tcp'],hand['rotation'],self.grasp_offset,self.grasp_rotation)
        finished=False
        if self.index<len(self.moves):
            step=self.moves[self.index];elapsed=now-self.t0
            finished=elapsed>=step['seconds']
            if step['label']=='finish_hold':
                finished=s['metrics']['score']==1.
                if elapsed>=step['seconds'] and not finished:
                    self.failure=self.failure or 'final measured parking conditions did not settle before hold deadline'
            if step['follow']=='release':
                start,rotation,axis=self.release_state;hand=s['hands'][1]
                axis=np.array(s['can_rotation'])@self.release_path['can_pose'][1].T@axis
                self.release_gap=release_clearance(hand['tcp'],hand['rotation'],PRESS_FACE,hand['finger_joints'][0],s['button'],np.array(s['can_rotation'])[:,2],axis)
                self.release_frames=release_gate_frames(s['button_travel'],self.release_gap,self.release_frames)
                path_end=elapsed>=self.release_path['duration']
                if path_end:self.left_preload_target=0.
                finished=self.release_frames>=5 and path_end and self.left_preload<=1e-9
                if elapsed>=step['seconds'] and not finished:self.failure=self.failure or 'button release/20 mm face clearance/preload settle timed out'
            if step['label'].startswith('coat_shot'):
                n=np.array(s['nozzle']);a=np.array(s['axis'])
                if a[0]>.5:
                    hit=n+a*((TARGET_X-n[0])/a[0])
                    if s['button_travel']>=PRESS_TRAVEL and max(abs(np.array(step['aim'])-hit[1:]))<.012:
                        self.contact_time+=self._dt
                finished=finished or (elapsed>=1. and self.contact_time>=MEASURED_DWELL)
                if elapsed>=step['seconds'] and self.contact_time<MEASURED_DWELL:self.failure=self.failure or 'insufficient measured spray contact'
        if finished and not self.failure:
            check=self.moves[self.index]['check']
            if check=='detached' and not s['cap_detached']:self.failure='cap pull failed'
            if check=='parked' and not s['metrics']['cap_removed']:self.failure='cap was not removed'
            if check=='coat' and s['metrics']['coverage']<.9:self.failure='coverage below 90%'
            if not self.failure:self.next(now)
        phase='done' if self.index>=len(self.moves) else self.moves[self.index]['label']
        if not self.failure and phase in ('finish_hold','done'):
            # Both hands have already retreated. Keep the previous valid motor
            # targets while the free can settles; do not wind up Cartesian IK
            # around an intentionally stationary, already-clear retreat pose.
            telemetry.command=dict(phase=phase,errors={},failure=None,holding_final_joint_command=True,
                                   left_command_finger_joint_m=float(self.last_actions[0][6]*FINGER_OPEN))
            return ActionChunk(actions=[Action(data=pack(*self.last_actions),meta={'request_stop':True} if phase=='done' else {})],control_hz=1/self._dt)
        self.left_preload=ramp_scalar(self.left_preload,self.left_preload_target,LEFT_PRELOAD_SPEED,self._dt)
        if not self.failure and self.index<len(self.moves):
            step=self.moves[self.index];f=ik.smoothstep(min(1.,(now-self.t0+self._dt)/step['seconds']))
            for i,key in enumerate(('L','R')):
                goal=step[key]
                if goal is not None:
                    p0,r0,g0=self.starts[i];p,r,g=goal
                    self.targets[i]=[p0+f*(p-p0),ik.slerp_matrix(r0,r,f),g0+f*(g-g0)]
            if step['follow']=='release':
                path=self.release_path
                p,fraction,_=release_command_target(path['start'],path['goal'],now-self.t0)
                r=ik.slerp_matrix(path['rotation'],path['goal_rotation'],fraction)
                try:p,r=transport_can_reference(p,r,path['can_pose'],(s['can'],s['can_rotation']))
                except ValueError as error:self.failure=str(error)
                self.targets[1]=[p,r,self.press_grip]
            elif step['follow']:
                # Press a physically moving piston with the other arm. The
                # target follows the measured can, not a changed button pose.
                can=np.array(s['can']);rot=np.array(s['can_rotation'])
                aim_error=None
                if step['aim'] is not None and s['axis'][0]>.5:
                    nozzle=np.array(s['nozzle']);axis=np.array(s['axis'])
                    hit=nozzle+axis*((TARGET_X-nozzle[0])/axis[0])
                    aim_error=np.array(step['aim'])-hit[1:]
                    correction=np.clip(.05*aim_error,-.000175,.000175)
                    self.targets[0][0]+=np.array((0.,*correction))
                    if max(abs(aim_error))>.014:self.press_enabled=False
                    elif max(abs(aim_error))<.008:self.press_enabled=True
                # Keep the physical load stable during an aimed dwell. Releasing
                # whenever load deflection moved the ray caused an on/off
                # oscillation; aim feedback can now settle under that same load.
                pressing=step['follow']=='press'
                if pressing:
                    travel_error=.0027-s['button_travel']
                    self.press_depth=float(np.clip(self.press_depth+.20*travel_error,0.,.006))
                height=.082-self.press_depth if pressing else .105
                point=PRESS_POINT.copy()
                finger=s['hands'][1].get('finger_joints',[-.028,-.028])[0]
                point[0]+=finger-(-.028)
                # Command the actual horizontal face onto the actuator's top,
                # accounting for finger spring deflection instead of guessing
                # a contact height from the generic TCP marker.
                actualR=np.array(s['hands'][1]['rotation'])
                try:target=actual_face_tcp_target(can,rot,height,actualR,point)
                except ValueError as error:self.failure=str(error);target=self.targets[1][0]
                witness=rot.T@(np.array(s['hands'][1]['tcp'])+actualR@point-can)
                face_normal=np.cross(PRESS_FACE[1]-PRESS_FACE[0],PRESS_FACE[2]-PRESS_FACE[0])
                face_normal=actualR@(face_normal/np.linalg.norm(face_normal))
                face_angle=float(np.degrees(np.arccos(np.clip(abs(face_normal@rot[:,2]),0.,1.))))
                velocity=None
                if self.face_witness_previous is not None:
                    previous_time,previous_witness=self.face_witness_previous;dt=float(s['time'])-previous_time
                    if dt>0:velocity=((witness[:2]-previous_witness[:2])/dt).tolist()
                self.face_witness_previous=(float(s['time']),witness.copy())
                self.face_diagnostics=dict(selected_face_plane_angle_deg=face_angle,can_relative_witness_m=witness.tolist(),
                    witness_tangential_velocity_can_m_s=velocity,
                    witness_velocity_scope='20 Hz finite-difference selected mesh-point proxy; not contact center or friction force')
                speed=RIGHT_PRESS_SPEED if pressing else .100
                try:position=can_frame_ramp_translation(self.targets[1][0],target,self.follow_can_pose,(can,rot),speed,self._dt)
                except ValueError as error:
                    self.failure=str(error);position=self.targets[1][0]
                self.follow_can_pose=(can.copy(),rot.copy())
                self.targets[1]=[np.asarray(position),rot@PRESS_R,self.press_grip]
        actions=[];errors={};press_contact=None
        pressing=self.index<len(self.moves) and self.moves[self.index]['follow']=='press'
        if pressing and not self.failure:
            try:press_contact=press_contact_state(s,PRESS_POINT)
            except ValueError as error:self.failure=str(error)
        if self.failure:
            telemetry.command=dict(phase=phase,errors={},failure=self.failure,release_clearance_m=self.release_gap,release_frames=self.release_frames,
                                   left_command_finger_joint_m=float(self.last_actions[0][6]*FINGER_OPEN))
            return ActionChunk(actions=[Action(data=pack(*self.last_actions),meta={'request_stop':True})],control_hz=1/self._dt)
        for i,side in enumerate(('left','right')):
            p,r,g=self.targets[i]
            hand=s['hands'][i]
            error=p-np.array(hand['tcp'])
            rotation_error=ik._rot_error(r,np.array(hand['rotation']))
            # Slow outer-loop compensation for measured PD deflection under
            # gravity and button load; hardware force/velocity limits unchanged.
            bound=.05 if i==0 else .020
            gain=.16 if i==0 else .08
            releasing=i==1 and self.index<len(self.moves) and self.moves[self.index]['follow']=='release'
            if not releasing:
                if i==1 and pressing:self.position_bias[i]=press_bias_step(self.position_bias[i],error,self._dt,press_contact)
                else:self.position_bias[i]=np.clip(self.position_bias[i]+gain*error,-bound,bound)
                self.rotation_bias[i]=np.clip(self.rotation_bias[i]+.04*rotation_error,-.12,.12)
            rv=self.rotation_bias[i];angle=np.linalg.norm(rv)
            compensated=(axis_angle_matrix(rv/angle,angle)@r if angle>1e-9 else r)
            applied_bias=self.position_bias[i].copy()
            if i==0:applied_bias[2]=np.clip(applied_bias[2]+self.left_preload,-bound,bound)
            if releasing and now-self.t0<=1e-12:q=self.release_path['initial_q'].copy();pe=re=0.
            else:q,pe,re=ik.solve(p+applied_bias,ik.matrix_to_quat_xyzw(compensated),self.q[i],base_pos=self._bases[side],iters=90)
            early=phase.startswith(('brace_','cap_')) or phase=='can_lift'
            limit=.015 if early else .005;angle_limit=.12 if early else .05
            if not np.isfinite(np.r_[q,pe,re]).all() or pe>limit or re>angle_limit:
                self.failure=f'{side} {phase} IK exceeds {limit*1000:g} mm / {angle_limit:g} rad bounds'
                telemetry.command=dict(phase=phase,errors=errors,failure=self.failure,left_command_finger_joint_m=float(self.last_actions[0][6]*FINGER_OPEN))
                return ActionChunk(actions=[Action(data=pack(*self.last_actions),meta={'request_stop':True})],control_hz=1/self._dt)
            self.q[i]=q;errors[side]=dict(position=pe,rotation=re,
                                         tracking_position=float(np.linalg.norm(error)),tracking_rotation=float(np.linalg.norm(rotation_error)),
                                         position_bias=self.position_bias[i].tolist(),applied_position_bias=applied_bias.tolist())
            actions.append(np.r_[q,np.clip(g,0.,1.)])
        telemetry.command=dict(phase=phase,errors=errors,failure=self.failure,commanded_depression=self.press_depth,measured_contact_time=self.contact_time,
                               left_preload_m=self.left_preload,left_preload_target_m=self.left_preload_target,right_press_speed_m_s=RIGHT_PRESS_SPEED,
                               release_clearance_m=self.release_gap,release_frames=self.release_frames,**self.face_diagnostics)
        telemetry.command['press_contact']=press_contact
        telemetry.command['left_command_finger_joint_m']=float(actions[0][6]*FINGER_OPEN)
        if self.release_path is not None:
            telemetry.command.update(release_path_duration_s=self.release_path['duration'],release_deadline_s=self.moves[self.index]['seconds'] if self.index<len(self.moves) and self.moves[self.index]['follow']=='release' else None)
        self.last_actions=[a.copy() for a in actions]
        meta={'request_stop':True} if self.failure or self.index>=len(self.moves) else {}
        return ActionChunk(actions=[Action(data=pack(*actions),meta=meta)],control_hz=1/self._dt)


def register_policy(cap_only=False,press_only=False):
    from inspect_robots.registry import register
    register('policy','spray_feedback_demo')(lambda:SprayDemo(cap_only,press_only))
    return 'spray_feedback_demo'
