"""Feedback demonstration using measured poses and ordinary robot commands.

The script has privileged object/hand telemetry. It never sets object poses,
applies forces or edits scoring/tape state. Dream receives the standard inputs.
"""
from dataclasses import replace
import math
import numpy as np
from yam_arena import ik
from yam_arena.demo import ArmPlan, grip_rotation, Waypoint
from yam_arena.urdf import axis_angle_matrix, quat_xyzw_to_matrix
from yam_arena.constants import FINGER_OPEN, READY
from yam_arena.scripted import YamScriptedPolicy
from inspect_robots.types import Action, ActionChunk
from inspect_robots_yam.packing import pack
from config import *
import telemetry


def rx(angle):
    return axis_angle_matrix(np.array([1.,0.,0.]),math.radians(angle))


def flap_target(side,angle,offset=None,relative_rotation=None):
    """Rigid grasp trajectory about the measured carton fold's fixed axis."""
    sign=1 if side=='left' else -1
    rotation=rx(-sign*angle)
    hinge=np.array([CENTER[0],sign*WIDTH/2,LID_Z])
    root_offset=np.array([0.,-sign*(WIDTH/4-.001),0.])
    if offset is None: offset=np.array([0.,-sign*.011,.017])
    if relative_rotation is None: relative_rotation=grip_rotation()
    return hinge+rotation@(root_offset+offset),rotation@relative_rotation


class ParcelFeedbackPolicy(YamScriptedPolicy):
    def __init__(self,opening_only=False):
        super().__init__()
        self.info=replace(self.info,name='parcel_feedback_demo')
        self.opening_only=opening_only

    def event(self,kind,**kwargs):
        telemetry.events.append(dict(time=self.now,kind=kind,phase=self.phase,**kwargs))

    def reset(self,scene):
        # Inspect resets the policy before the embodiment. Initialize from the
        # first real observation after the simulator reset has completed.
        self.initialized=False

    def initialize(self):
        if telemetry.latest is None: raise RuntimeError('demo requires measured initial telemetry')
        self.initialized=True
        self.now=0.;self.phase='cut';self.failure=None;self.motion=None
        self.target={};self.q={};self.q_override={}
        for i,side in enumerate(('left','right')):
            h=telemetry.latest['hands'][i]
            self.target[side]=(np.array(h['tcp']),np.array(h['tcp_rotation']),h['opening'])
            self.q[side]=np.array(h['joints'])
            self.q_override[side]=self.q[side].copy()
        self.cut_plan=ArmPlan(self._task.module.demo()['left'][:12],self._bases['left'])
        self.park_plan=ArmPlan([Waypoint(3.,(.13,-.24,TOP+.17),FINGER_OPEN)],self._bases['right'])
        self.retries={'left':0,'right':0};self.pick_retries=0;self.carrying=False
        if self.opening_only: self.begin_flap('left')
        self.event('start',diagnostic_precut=self.opening_only)

    def hand(self,side):
        return telemetry.latest['hands'][0 if side=='left' else 1]

    def angle(self,side):
        return telemetry.latest['flap_angles'][0 if side=='left' else 1]

    def move(self,side,pos,rotation,opening,seconds,then):
        h=self.hand(side)
        self.q_override.pop(side,None)
        self.q[side]=np.array(h['joints'])
        self.motion=dict(side=side,start=self.now,p0=np.array(h['tcp']),r0=np.array(h['tcp_rotation']),
                         g0=self.target[side][2],p1=np.array(pos),r1=np.array(rotation),g1=opening,
                         seconds=seconds,then=then)
        self.phase='move:'+then

    def park(self,side,then):
        self.motion=dict(mode='joints',side=side,start=self.now,q0=np.array(self.hand(side)['joints']),
                         q1=np.array(READY),seconds=3.,then=then)
        self.phase='park:'+side

    def hold(self,seconds,then):
        self.phase='hold:'+then;self.until=self.now+seconds

    def fail(self,reason):
        self.failure=reason;self.event('failure',reason=reason);self.phase='failed'
        self.motion=None;self.carrying=False

    def begin_flap(self,side):
        self.side=side
        p,r=flap_target(side,self.angle(side))
        self.event('approach_flap',side=side,angle=self.angle(side),attempt=self.retries[side]+1)
        self.move(side,p-r[:,2]*.075,r,1.,2.,'flap_approached')

    def retry_flap(self,reason):
        side=self.side
        self.event('flap_retry',side=side,reason=reason,angle=self.angle(side))
        self.retries[side]+=1
        if self.retries[side]>2: return self.fail(side+' flap: '+reason)
        h=self.hand(side);p=np.array(h['tcp']);r=np.array(h['tcp_rotation'])
        self.move(side,p-r[:,2]*.06,r,.75,1.5,'flap_retry_clear')

    def begin_pick(self):
        self.carrying=False
        p=np.array(telemetry.latest['item']['pos'])+[0.,0.,.008]
        self.pick_point=p
        self.event('approach_item',item_position=telemetry.latest['item']['pos'])
        self.move('right',(*p[:2],TOP+.17),grip_rotation(),1.,2.,'item_approached')

    def transition(self,name):
        side=getattr(self,'side','left')
        if name=='flap_approached':
            p,r=flap_target(side,self.angle(side))
            self.move(side,p,r,1.,2.,'flap_descended')
        elif name=='flap_descended':
            p,r=self.target[side][:2]
            self.move(side,p,r,.011/abs(FINGER_OPEN)/2,.9,'flap_closed')
        elif name=='flap_closed': self.hold(.4,'flap_grasp_check')
        elif name=='flap_grasp_check':
            h=self.hand(side);flap=telemetry.latest['flaps'][side]
            if not .08<h['opening']<.3: return self.retry_flap('no tab between the jaws')
            r=quat_xyzw_to_matrix(np.array(flap['quat']))
            self.grasp_offset=r.T@(np.array(h['tcp'])-np.array(flap['pos']))
            self.grasp_rotation=r.T@np.array(h['tcp_rotation'])
            self.command_angle=max(0.,self.angle(side));self.last_angle=self.angle(side)
            self.last_progress=self.now;self.rotate_start=self.now;self.phase='rotate_flap'
            self.event('flap_grasp',side=side,offset=self.grasp_offset.tolist(),opening=h['opening'])
        elif name=='flap_retry_clear': self.begin_flap(side)
        elif name=='flap_rotated':
            p,r=self.target[side][:2]
            self.move(side,p,r,.75,.9,'flap_released')
        elif name=='flap_released':
            h=self.hand(side);p=np.array(h['tcp']);r=np.array(h['tcp_rotation'])
            self.move(side,p-r[:,2]*.075,r,.75,1.8,'flap_withdrawn')
        elif name=='flap_withdrawn':
            self.park(side,'flap_parked')
        elif name=='flap_parked':
            if self.angle(side)<80: return self.retry_flap('flap did not remain open after release')
            self.event('flap_open_verified',side=side,angle=self.angle(side))
            if side=='left': self.begin_flap('right')
            elif min(telemetry.latest['flap_angles'])<80: self.fail('first flap fell shut')
            elif self.opening_only:
                self.event('diagnostic_open_completed');self.phase='done'
            else: self.begin_pick()
        elif name=='item_approached': self.move('right',self.pick_point,grip_rotation(),1.,2.,'item_descended')
        elif name=='item_descended':
            self.move('right',self.target['right'][0],grip_rotation(),.038/abs(FINGER_OPEN)/2,1.,'item_closed')
        elif name=='item_closed':
            h=self.hand('right');p=np.array(h['tcp']);p[2]=TOP+.17
            self.move('right',p,grip_rotation(),.038/abs(FINGER_OPEN)/2,2.,'item_lifted')
        elif name=='item_lifted':
            h=self.hand('right');item=np.array(telemetry.latest['item']['pos']);tcp=np.array(h['tcp'])
            if item[2]<LID_Z+.035 or np.linalg.norm(item-tcp)>.045:
                self.pick_retries+=1
                if self.pick_retries>1: return self.fail('item pickup not established')
                return self.begin_pick()
            self.item_offset=grip_rotation().T@(item-tcp)
            self.carrying=True
            self.event('item_pickup_verified',height=float(item[2]),grasp_offset=self.item_offset.tolist())
            self.move('right',(.10,0.,TOP+.17),grip_rotation(),.038/abs(FINGER_OPEN)/2,2.,'item_front')
        elif name=='item_front':
            self.move('right',(.10,DESTINATION[1],TOP+.17),grip_rotation(),.038/abs(FINGER_OPEN)/2,2.,'item_outside')
        elif name=='item_outside':
            self.move('right',(*DESTINATION,TOP+.17),grip_rotation(),.038/abs(FINGER_OPEN)/2,1.5,'item_above_pad')
        elif name=='item_above_pad':
            goal=np.array([*DESTINATION,TOP+.023])-grip_rotation()@self.item_offset
            self.move('right',goal,grip_rotation(),.038/abs(FINGER_OPEN)/2,2.,'item_lowered')
        elif name=='item_lowered':
            self.carrying=False
            self.move('right',self.target['right'][0],grip_rotation(),1.,1.,'item_released')
        elif name=='item_released':
            self.move('right',(*DESTINATION,TOP+.17),grip_rotation(),1.,2.,'finish')
        elif name=='finish': self.hold(3.,'finish_check')
        elif name=='finish_check':
            self.event('finished',metrics=telemetry.latest['metrics'])
            if telemetry.latest['metrics']['score']<1.: self.fail('final placement did not reach full score')
            else: self.phase='done'
        else: raise RuntimeError('unknown transition '+name)

    def advance(self):
        if self.motion is not None:
            m=self.motion;u=(self.now-m['start'])/m['seconds'];blend=ik.smoothstep(u)
            if m.get('mode')=='joints':
                q=m['q0']+blend*(m['q1']-m['q0'])
                self.q_override[m['side']]=q
                self.q[m['side']]=q.copy()
                p,r=ik.tcp_pose(q,self._bases[m['side']])
                self.target[m['side']]=(p,r,1.)
            else:
                self.target[m['side']]=(m['p0']+blend*(m['p1']-m['p0']),
                                       ik.slerp_matrix(m['r0'],m['r1'],blend),m['g0']+blend*(m['g1']-m['g0']))
            if u>=1.:
                self.motion=None;self.transition(m['then'])
        elif self.phase.startswith('hold:'):
            if self.now>=self.until: self.transition(self.phase[5:])
        elif self.phase=='rotate_flap':
            a=self.angle(self.side);h=self.hand(self.side)
            if a>self.last_angle+1.:
                self.last_angle=a;self.last_progress=self.now
            if self.now-self.last_progress>2.5 or self.now-self.rotate_start>16.:
                return self.retry_flap('opening stalled')
            if h['opening']<.06: return self.retry_flap('tab slipped out')
            self.command_angle=min(107.,self.command_angle+18.*self._dt,max(0.,a)+10.)
            p,_=flap_target(self.side,self.command_angle,self.grasp_offset,self.grasp_rotation)
            sign=1 if self.side=='left' else -1
            # Keep the wrist within its reachable range. Past 80 degrees the
            # TCP continues its arc while the tab rotates in the compliant grasp.
            r=rx(-sign*min(self.command_angle,80.))@self.grasp_rotation
            self.target[self.side]=(p,r,.011/abs(FINGER_OPEN)/2)
            if a>=102. and self.command_angle>=105.: self.hold(.5,'flap_rotated')

    def act(self,observation):
        if not self.initialized: self.initialize()
        self.now=float(observation.state_time)
        sample=telemetry.latest
        if sample is None or abs(sample['time']-self.now)>.075: raise RuntimeError('stale privileged demo telemetry')
        if self.phase=='cut':
            t=self.now+self._dt
            if t<=self.cut_plan.duration:
                a=self.cut_plan.action7(t)[0];b=self.park_plan.action7(t)[0]
                return ActionChunk(actions=[Action(data=pack(a,b))],control_hz=1/self._dt)
            if sample['metrics']['cut_segments']!=21 or sample['held']:
                self.fail('cutting and cutter return were not established')
            else:
                for side in ('left','right'):
                    h=self.hand(side)
                    self.target[side]=(np.array(h['tcp']),np.array(h['tcp_rotation']),h['opening'])
                    self.q[side]=np.array(h['joints'])
                    self.q_override[side]=self.q[side].copy()
                self.begin_flap('left')
        if self.carrying:
            h=self.hand('right')
            predicted=np.array(h['tcp'])+np.array(h['tcp_rotation'])@self.item_offset
            slip=float(np.linalg.norm(np.array(sample['item']['pos'])-predicted))
            if slip>.018:
                self.event('item_slip_detected',slip_m=slip)
                self.carrying=False;self.pick_retries+=1
                if self.pick_retries>1: self.fail('item slipped during transport')
                else: self.begin_pick()
        self.advance()
        actions=[];errors={}
        for side in ('left','right'):
            pos,rot,opening=self.target[side]
            if side in self.q_override:
                q=self.q_override[side];pe=re=0.
            else:
                q,pe,re=ik.solve(pos,ik.matrix_to_quat_xyzw(rot),self.q[side],base_pos=self._bases[side],iters=70)
            self.q[side]=q
            errors[side]=dict(position_m=pe,rotation_rad=re)
            actions.append(np.r_[q,np.clip(opening,0,1)])
        telemetry.command=dict(phase=self.phase,ik_errors=errors,failure=self.failure)
        meta={'request_stop':True} if self.phase in ('failed','done') else {}
        return ActionChunk(actions=[Action(data=pack(*actions),meta=meta)],control_hz=1/self._dt)


def register_policy(opening_only=False):
    from inspect_robots.registry import register
    register('policy','parcel_feedback_demo')(lambda:ParcelFeedbackPolicy(opening_only))
    return 'parcel_feedback_demo'
