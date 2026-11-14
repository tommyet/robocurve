"""Measured-state side-grip demo; ordinary bounded 14D commands only.

No pose writes, forces, joint removal, deposit writes or scorer updates here.
The policy receives privileged simulation telemetry for planning, disclosed.
"""
from dataclasses import replace
import numpy as np
from yam_arena import ik
from yam_arena.constants import FINGER_OPEN
from yam_arena.urdf import axis_angle_matrix
from yam_arena.scripted import YamScriptedPolicy
from inspect_robots.types import Action,ActionChunk
from inspect_robots_yam.packing import pack
from config import *
import telemetry
from control_math import grip_fraction

LEFT_R=np.array([[-1.,0.,0.],[0.,0.,-1.],[0.,-1.,0.]])
RIGHT_R=np.array([[1.,0.,0.],[0.,0.,1.],[0.,-1.,0.]])
PRESS_R=axis_angle_matrix(np.array([1.,0.,0.]),np.radians(-45.))@RIGHT_R


class SprayDemo(YamScriptedPolicy):
    def __init__(self,cap_only=False,press_only=False):
        super().__init__();self.info=replace(self.info,name='spray_feedback_demo')
        self.cap_only=cap_only
        self.press_only=press_only

    def reset(self,scene):self.started=False

    def initialize(self):
        self.started=True;self.index=-1;self.failure=None;self.moves=[]
        self.press_offset=.093;self.grasp_calibrated=False;self.press_enabled=True
        self.contact_time=0.;self.press_grip=grip_fraction(-.028,FINGER_OPEN)
        self.targets=[];self.q=[]
        self.position_bias=[np.zeros(3),np.zeros(3)]
        self.rotation_bias=[np.zeros(3),np.zeros(3)]
        for h in telemetry.latest['hands']:
            self.targets.append([np.array(h['tcp']),np.array(h['rotation']),h['opening']])
            self.q.append(np.array(h['joints']))
        can=np.array(telemetry.latest['can']);cap=np.array(telemetry.latest['cap'])
        left=can+np.array((0.,0.,-.025))
        self.grip=grip_fraction(-.021,FINGER_OPEN);cap_grip=grip_fraction(-.025,FINGER_OPEN)
        def move(label,seconds,L=None,R=None,check=None,follow=False,aim=None):
            self.moves.append(dict(label=label,seconds=seconds,L=L,R=R,check=check,follow=follow,aim=aim))
        def lp(p,g):return (np.array(p),LEFT_R,g)
        def rp(p,g):return (np.array(p),RIGHT_R,g)
        move('brace_approach',2.,L=lp(left+(0.,.10,.015),1.))
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
        can_center=np.array((CAN_START[0],0.,TARGET_CENTER[1]-.077))
        move('can_lift',2.,L=lp(can_center+(0.,0.,-.025),self.grip))
        move('press_approach',2.,R=(can_center+(-.028,-.08,.135),PRESS_R,self.press_grip))
        move('press_hover',1.5,follow='hover')
        for index,(y,z) in enumerate([(-.035,-.035),(-.035,.035),(.035,.035),(.035,-.035)]):
            p=can_center+np.array((0.,y,z-.025))
            aim=(y,TARGET_CENTER[1]+z)
            move('coat_position_'+str(index),1.8,L=lp(p,self.grip),follow='hover')
            move('coat_aim_'+str(index),1.2,follow='hover',aim=aim)
            move('coat_shot_'+str(index),8.,follow='press',aim=aim)
            move('coat_unpress_'+str(index),.6,follow='hover')
        move('finish_coating',.3,check='coat')
        move('press_retreat',2.,R=rp(can_center+(0.,-.09,.07),1.))
        move('can_lower',3.,L=lp((CAN_PAD[0],CAN_PAD[1],TOP+.097),self.grip))
        move('can_release',1.,L=lp((CAN_PAD[0],CAN_PAD[1],TOP+.097),1.))
        move('brace_retreat',2.,L=lp((CAN_PAD[0],CAN_PAD[1]+.12,TOP+.13),1.))
        move('finish_hold',2.)
        if self.press_only:self.moves=self.moves[:3]+self.moves[11:]

    def next(self,now):
        self.index+=1;self.t0=now
        self.starts=[(p.copy(),r.copy(),g) for p,r,g in self.targets]
        if self.index>=len(self.moves):return
        step=self.moves[self.index]
        if step['label'].startswith('coat_shot'):
            self.position_bias[0][2]=min(.05,self.position_bias[0][2]+.014)
            self.contact_time=0.
        if step['label'].startswith('coat_unpress'):
            self.position_bias[0][2]-=.014
        if step['label']=='can_lift' and not self.grasp_calibrated:
            s=telemetry.latest;can_rot=np.array(s['can_rotation'])
            hand=s['hands'][0];offset=can_rot.T@(np.array(hand['tcp'])-np.array(s['can']))
            hold_rotation=can_rot.T@np.array(hand['rotation'])
            for future in self.moves[self.index:]:
                if future['L'] is not None:
                    p,r,g=future['L'];future['L']=(p+offset-np.array((0.,0.,-.025)),hold_rotation,g)
            self.grasp_calibrated=True
        if isinstance(step['R'],str) and step['R']=='unpress':
            p=np.array(telemetry.latest['can'])+np.array((0.,-.006,.12))
            step['R']=(p,RIGHT_R,0.)
        telemetry.events.append(dict(time=now,event='phase',phase=step['label']))

    def act(self,observation):
        if not self.started:self.initialize()
        now=float(observation.state_time);s=telemetry.latest
        if self.index<0:self.next(now)
        if abs(s['time']-now)>.075:raise RuntimeError('stale demo telemetry')
        finished=False
        if self.index<len(self.moves):
            step=self.moves[self.index];elapsed=now-self.t0
            finished=elapsed>=step['seconds']
            if step['label'].startswith('coat_shot'):
                n=np.array(s['nozzle']);a=np.array(s['axis'])
                if a[0]>.5:
                    hit=n+a*((TARGET_X-n[0])/a[0])
                    if s['button_travel']>=PRESS_TRAVEL and max(abs(np.array(step['aim'])-hit[1:]))<.012:
                        self.contact_time+=self._dt
                finished=finished or (elapsed>=1. and self.contact_time>=1.2)
                if elapsed>=step['seconds'] and self.contact_time<1.2:self.failure='insufficient measured spray contact'
        if finished:
            check=self.moves[self.index]['check']
            if check=='detached' and not s['cap_detached']:self.failure='cap pull failed'
            if check=='parked' and not s['metrics']['cap_removed']:self.failure='cap was not removed'
            if check=='coat' and s['metrics']['coverage']<.9:self.failure='coverage below 90%'
            self.next(now)
        phase='done' if self.index>=len(self.moves) else self.moves[self.index]['label']
        if not self.failure and self.index<len(self.moves):
            step=self.moves[self.index];f=ik.smoothstep(min(1.,(now-self.t0+self._dt)/step['seconds']))
            for i,key in enumerate(('L','R')):
                goal=step[key]
                if goal is not None:
                    p0,r0,g0=self.starts[i];p,r,g=goal
                    self.targets[i]=[p0+f*(p-p0),ik.slerp_matrix(r0,r,f),g0+f*(g-g0)]
            if step['follow']:
                # Press a physically moving piston with the other arm. The
                # target follows the measured can, not a changed button pose.
                can=np.array(s['can']);rot=np.array(s['can_rotation'])
                aim_error=None
                if step['aim'] is not None and s['axis'][0]>.5:
                    nozzle=np.array(s['nozzle']);axis=np.array(s['axis'])
                    hit=nozzle+axis*((TARGET_X-nozzle[0])/axis[0])
                    aim_error=np.array(step['aim'])-hit[1:]
                    correction=np.clip(.20*aim_error,-.0007,.0007)
                    self.targets[0][0]+=np.array((0.,*correction))
                    if max(abs(aim_error))>.014:self.press_enabled=False
                    elif max(abs(aim_error))<.008:self.press_enabled=True
                # Keep the physical load stable during an aimed dwell. Releasing
                # whenever load deflection moved the ray caused an on/off
                # oscillation; aim feedback can now settle under that same load.
                pressing=step['follow']=='press'
                if pressing:
                    travel_error=.0027-s['button_travel']
                    self.press_offset=float(np.clip(self.press_offset-.20*travel_error,.080,.110))
                offset=self.press_offset if pressing else .122
                # Open 56 mm and align one finger at the button; the other
                # stays behind the can, clear of both its body and spray path.
                target=can+rot@np.array((-.028,-.010,offset))
                previous=self.targets[1][0]
                delta=target-previous
                delta*=min(1.,.005/max(1e-9,np.linalg.norm(delta)))
                self.targets[1]=[previous+delta,rot@PRESS_R,self.press_grip]
        actions=[];errors={}
        for i,side in enumerate(('left','right')):
            p,r,g=self.targets[i]
            hand=s['hands'][i]
            error=p-np.array(hand['tcp'])
            rotation_error=ik._rot_error(r,np.array(hand['rotation']))
            # Slow outer-loop compensation for measured PD deflection under
            # gravity and button load; hardware force/velocity limits unchanged.
            bound=.05 if i==0 else .020
            gain=.16 if i==0 else .08
            self.position_bias[i]=np.clip(self.position_bias[i]+gain*error,-bound,bound)
            self.rotation_bias[i]=np.clip(self.rotation_bias[i]+.04*rotation_error,-.12,.12)
            rv=self.rotation_bias[i];angle=np.linalg.norm(rv)
            compensated=(axis_angle_matrix(rv/angle,angle)@r if angle>1e-9 else r)
            q,pe,re=ik.solve(p+self.position_bias[i],ik.matrix_to_quat_xyzw(compensated),self.q[i],base_pos=self._bases[side],iters=90)
            self.q[i]=q;errors[side]=dict(position=pe,rotation=re,
                                         tracking_position=float(np.linalg.norm(error)),tracking_rotation=float(np.linalg.norm(rotation_error)),
                                         position_bias=self.position_bias[i].tolist())
            actions.append(np.r_[q,np.clip(g,0.,1.)])
        telemetry.command=dict(phase=phase,errors=errors,failure=self.failure,press_offset=self.press_offset,measured_contact_time=self.contact_time)
        meta={'request_stop':True} if self.failure or self.index>=len(self.moves) else {}
        return ActionChunk(actions=[Action(data=pack(*actions),meta=meta)],control_hz=1/self._dt)


def register_policy(cap_only=False,press_only=False):
    from inspect_robots.registry import register
    register('policy','spray_feedback_demo')(lambda:SprayDemo(cap_only,press_only))
    return 'spray_feedback_demo'
