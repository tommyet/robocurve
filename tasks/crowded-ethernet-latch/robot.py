"""Measured bimanual release/reinsert using ordinary bounded 14D commands.

The LEFT robot grasps the ordinary boot. The RIGHT robot presses with its
unmodified tip_left finger. Object poses and actual finger joints are read,
never written; a grasp transform is measured rather than welded.
"""
import json
from pathlib import Path
import numpy as np
from yam_arena import ik
from yam_arena.constants import FINGER_OPEN
from yam_arena.urdf import quat_xyzw_to_matrix,rotation_angle_deg,axis_angle_matrix as axis_rotation
from config import SERVICE,TARGET,CLIP_Z,CLIP_TRAVEL,RELEASE_TRAVEL,port
from collision_geometry import FingerGeometry,minimum_separation
from feedback import snapshot,clearance,gripper_sweep,BootJawPredictor,plug_fit,plug_hand_target,retaining_face

_angle=np.radians(80.)
R_GRIP=np.array([[0.,np.cos(_angle),np.sin(_angle)],[0.,-np.sin(_angle),np.cos(_angle)],[1.,0.,0.]])
BOOT_LOCAL=np.array((-.0395,-.0035,-.0005))
GRIP=.0015/abs(FINGER_OPEN)
ENTRY_GRIP=.0065/abs(FINGER_OPEN)
PRESS_JAW=-.028
PRESS_GRIP=.028/abs(FINGER_OPEN)
MAX_RELEASE_STEPS=2000


class GraspProbe:
    def __init__(self,env,plug):
        self.env,self.base,self.plug=env,env._base,np.array(plug)
        self.previous=env._ready.detach().cpu().numpy().reshape(-1).copy()
        self.starts=[];self.q=[];self.bias=[np.zeros(3),np.zeros(3)];self.cartesian_bias_enabled=False
        for side in ('left','right'):
            q,f,p,r=self.arm(side);self.q.append(q.copy());self.starts.append((p.copy(),r.copy()))
        self.phase='approach_boot';self.phase_start=0.;self.stable_frames=0
        self.failure=None;self.last_t=None;self.release=False;self.events=[]
        self.boot_goal=self.plug+BOOT_LOCAL;self.boot_rotation=R_GRIP;self.front_offset=np.array((-.040,0,0))
        self.geometry=FingerGeometry();self.hand_clearance=None
        self.hold_offset=None;self.hold_rotation=None;self.grasp_drift=0.
        self.last_fingers=None
        self.free_clearance=None;self.entry_clearance=None;self.boot_prediction=None;self.jaw_predictor=BootJawPredictor(self.geometry)

    def arm(self,side):
        ids,fids=self.env._ids[side+'_robot']
        data=self.base.scene[side+'_robot'].data.joint_pos
        data=data.torch if hasattr(data,'torch') else data
        values=data.detach().cpu().numpy()[0]
        q,f=values[ids],values[fids]
        p,r=ik.tcp_pose(q,self.env.rig.bases[side])
        return q,f,p,r

    def object_pose(self,name):
        data=self.base.arena_world.get_pose_w(name)
        data=data.torch if hasattr(data,'torch') else data
        return data.detach().cpu().numpy()[0]

    def transition(self,phase,t):
        self.events.append({'time':float(t),'from':self.phase,'to':phase})
        self.phase,self.phase_start,self.stable_frames=phase,t,0

    @staticmethod
    def settled(measured,target,tolerance=.001,rotation_tolerance=1.):
        return np.linalg.norm(measured[0]-target[0])<tolerance and rotation_angle_deg(measured[1],target[1])<rotation_tolerance

    def gate(self,condition,age,duration,timeout,next_phase,t):
        self.stable_frames=self.stable_frames+1 if condition and age>=duration else 0
        if self.stable_frames>=5:self.transition(next_phase,t)
        elif age>duration+timeout:self.failure=self.phase+' did not satisfy measured settle gate'

    def capture_grasp(self,plug,rotation,measured):
        self.hold_offset=rotation.T@(measured[2]-plug[:3])
        self.hold_rotation=rotation.T@measured[3]
        self.held_origin=plug[:3].copy()
        self.boot_goal,self.boot_rotation=measured[2].copy(),measured[3].copy()

    def command(self,t):
        dt=.05 if self.last_t is None else float(np.clip(t-self.last_t,0.,.1));self.last_t=t
        measured=[self.arm(side) for side in ('left','right')]
        plug=self.object_pose(f'plug_{SERVICE}');rotation=quat_xyzw_to_matrix(plug[3:])
        clip=self.object_pose(f'clip_{SERVICE}');self.measured_clip=clip.copy()
        travel=float(CLIP_Z-(rotation.T@(clip[:3]-plug[:3]))[2])
        age=t-self.phase_start;phase=self.phase
        if self.hold_offset is None and phase in ('approach_boot','narrow_in_front_of_boot','enter_boot','close_on_boot'):
            # Cable load settles the real plug at a pitch/yaw before contact.
            # Track its actual boot centreline, while keeping this reachable
            # wrist orientation fixed in the world. The pad reaches forward
            # from this rearward/outboard TCP onto the rear of the ordinary boot.
            self.boot_goal=plug[:3]+rotation@BOOT_LOCAL
            self.boot_rotation=R_GRIP
            self.front_offset=rotation@np.array((-.040,0,0))
        lp,lr,lg=self.boot_goal.copy(),self.boot_rotation,GRIP
        rp,rr=self.starts[1];rg=1.
        left_actual=measured[0][2:];right_actual=measured[1][2:]
        if self.hold_offset is not None:
            actual_offset=rotation.T@(measured[0][2]-plug[:3])
            self.grasp_drift=float(np.linalg.norm(actual_offset-self.hold_offset))
            if self.grasp_drift>.006:self.failure='boot slipped more than 6 mm relative to measured grasp'
        if travel>CLIP_TRAVEL+.0002:self.failure='clip exceeded physical travel limit'
        # Only the certified front standoff uses a wider pose gate. Geometry
        # uses actual rotation/fingers and includes all 84 measured cables.
        if phase in ('approach_boot','narrow_in_front_of_boot') and age>=2.:
            front=self.boot_goal+self.front_offset
            if self.settled(left_actual,(front,self.boot_rotation),.003,3.):
                state=snapshot(self.object_pose)
                sweep=gripper_sweep(self.geometry,measured[0][1],measured[0][2],measured[0][3],end_fingers=[-.0065,-.0065])
                self.free_clearance=clearance(sweep,state)
        free_ok=self.free_clearance is not None and self.free_clearance['minimum_gap_m']>=.005

        if phase=='approach_boot':
            p0,r0=self.starts[0];s=ik.smoothstep(min(1.,age/4.))
            front=self.boot_goal+self.front_offset
            lp,lr,lg=p0+s*(front-p0),ik.slerp_matrix(r0,self.boot_rotation,s),1.
            self.gate(free_ok and self.settled(left_actual,(front,self.boot_rotation),.002,2.),age,4.,5.,'narrow_in_front_of_boot',t)
        elif phase=='narrow_in_front_of_boot':
            lp=self.boot_goal+self.front_offset;lr=self.boot_rotation
            lg=1.+(ENTRY_GRIP-1.)*ik.smoothstep(min(1.,age/2.))
            jaw_ok=np.max(np.abs(measured[0][1]+.0065))<.001
            self.gate(free_ok and jaw_ok and self.settled(left_actual,(lp,lr),.002,2.),age,2.,5.,'enter_boot',t)
        elif phase=='enter_boot':
            lp=self.boot_goal+self.front_offset*(1-ik.smoothstep(min(1.,age/3.)));lg=ENTRY_GRIP
            entry_ok=False
            if age>=3. or np.linalg.norm(measured[0][2]-self.boot_goal)<.010:
                self.entry_clearance=clearance(gripper_sweep(self.geometry,measured[0][1],measured[0][2],measured[0][3]),snapshot(self.object_pose),wire_margin=.0005)
                # Flexible cable brushing is permitted. Only rigid socket,
                # own-boot and clip clearance blocks this entry stage.
                entry_ok=(self.entry_clearance['rigid_gap_m']>=.0005 and self.settled(left_actual,(self.boot_goal,lr),.002,2.))
            self.gate(entry_ok,age,3.,5.,'close_on_boot',t)
        elif phase=='close_on_boot':
            lg=ENTRY_GRIP+(GRIP-ENTRY_GRIP)*ik.smoothstep(min(1.,age/2.))
            jaws=np.abs(measured[0][1]);jaw_ok=False
            jaw_stable=self.last_fingers is not None and np.max(np.abs(measured[0][1]-self.last_fingers))<.0001
            if age>=2. and self.settled(left_actual,(lp,lr),.002,2.):
                self.boot_prediction=self.jaw_predictor.predict(plug,measured[0][2],measured[0][3],measured[0][1])
                expected=np.array(self.boot_prediction['opening_m'])
                jaw_ok=(all(self.boot_prediction['contact_possible']) and np.all(np.abs(jaws-expected)<=.0005)
                        and np.all(jaws>.002) and max(self.boot_prediction['actual_surface_gap_m'])<=.0006)
            self.gate(jaw_ok and jaw_stable,age,2.,5.,'prepare_press' if self.release else 'verified_boot_hold',t)
            if self.phase!=phase:
                self.capture_grasp(plug,rotation,measured[0])
                self.press_start=(measured[1][2].copy(),measured[1][3].copy())
        elif phase=='verified_boot_hold':
            pass
        elif self.release:
            lp,lr,lg,rp,rr,rg=self.release_targets(t,age,phase,plug,rotation,travel,measured,(lp,lr,lg,rp,rr,rg))
        else:raise RuntimeError('unknown grasp phase '+phase)

        self.last_fingers=measured[0][1].copy()
        targets=[(lp,lr,lg),(rp,rr,rg)];out=self.env._ready.detach().cpu().numpy().reshape(-1).copy();arms=[]
        contact=phase in ('enter_boot','close_on_boot','lower_press_front','insert_above_clip','depress_clip','withdraw_with_clip_pressed','finish_withdrawal','lift_press_finger','clear_press_finger','align_empty_target','insert_empty_target','retract_for_alignment','seat_and_release_clip','release_boot','retreat_hands','certify_open_clearance','retreat_partially_open','open_clear_hands','retention_rest')
        for i,side in enumerate(('left','right')):
            p,r,g=targets[i];actual,actualr=measured[i][2:];error=p-actual
            if self.cartesian_bias_enabled and not contact and np.linalg.norm(error)<.02 and rotation_angle_deg(actualr,r)<5.:
                cap=.0025 if i==0 and phase in ('approach_boot','narrow_in_front_of_boot') and free_ok else .001
                self.bias[i]=np.clip(self.bias[i]+.8*dt*error,-cap,cap)
            # Contact retains bounded learned gravity/stiction compensation;
            # there is no new integral and no decay that erases the preload.
            self.q[i],pe,re=ik.solve(p+self.bias[i],ik.matrix_to_quat_xyzw(r),self.q[i],base_pos=self.env.rig.bases[side],iters=110)
            out[7*i:7*i+6],out[7*i+6]=self.q[i],g
            arms.append({'side':side,'tcp':actual.tolist(),'target':p.tolist(),'position_error':float(np.linalg.norm(error)),
                         'rotation_error_deg':rotation_angle_deg(actualr,r),'ik_position_error':float(pe),'ik_rotation_error':float(re),
                         'effective_ik_tcp_target':(p+self.bias[i]).tolist(),'actual_joints':measured[i][0].tolist(),'actual_finger_joints_m':measured[i][1].tolist(),'bias_m':self.bias[i].tolist()})
        delta=np.array([.04]*6+[.05]+[.04]*6+[.05]);out=np.clip(np.clip(out,self.previous-delta,self.previous+delta),self.env._low,self.env._high);self.previous=out
        for i,side in enumerate(('left','right')):
            command_p,command_r=ik.tcp_pose(out[7*i:7*i+6],self.env.rig.bases[side])
            arms[i]['bounded_command_fk_tcp']=command_p.tolist();arms[i]['bounded_command_fk_rotation']=command_r.tolist()
        report={'cartesian_bias_enabled':self.cartesian_bias_enabled,'bounded_action_14d':out.tolist(),'phase':phase,'phase_age_s':float(age),'next_phase':self.phase,'arms':arms,'position_error':arms[0]['position_error'],
                    'left_tcp':measured[0][2].tolist(),'left_target':lp.tolist(),'right_tcp':measured[1][2].tolist(),'right_target':rp.tolist(),
                    'boot_target_plug_local':BOOT_LOCAL.tolist(),'actual_boot_grasp_target':(plug[:3]+rotation@BOOT_LOCAL).tolist(),'clip_travel_m':travel,'grasp_drift_m':self.grasp_drift,'free_standoff_clearance':self.free_clearance,'entry_clearance':self.entry_clearance,'boot_jaw_prediction':self.boot_prediction,'hand_clearance_m':self.hand_clearance,'stable_frames':self.stable_frames,
                    'failure':self.failure,'complete':bool(self.failure is None and ((phase=='verified_boot_hold' and age>=1.) or (phase=='retention_rest' and age>=2.5 and self.retention_gate_s>=2.1))),
                    'events':self.events[-3:]}
        if self.release:
            point=self.point.copy();point[0]+=measured[1][1][0]+.028
            witness=measured[1][2]+measured[1][3]@point
            report.update({'measured_press_point':witness.tolist(),'measured_press_point_plug_local':(rotation.T@(witness-plug[:3])).tolist(),
                           'target_press_point':(rp+rr@point).tolist(),'press_depth_m':self.press_depth,'withdraw_target_distance_m':self.pull_distance,'measured_hook_front_x_m':getattr(self,'measured_hook_front',None),'guide_geometry':self.guide_geometry,'insertion_command_x_m':self.insertion_x,'insertion_retries':self.insertion_retries,'full_release_clearance':self.final_clearance,'released_hold_s':self.retention_gate_s})
        return out,report


class ReleaseProbe(GraspProbe):
    def __init__(self,env,plug):
        super().__init__(env,plug);self.release=True
        spec=json.loads(Path(__file__).with_name('press_point.json').read_text())
        self.point=np.array(spec['point_tcp']);self.pressR=np.array(spec['rotation'])
        self.press_depth=0.;self.pull_distance=0.;self.source_clear=False;self.target_origin=np.array(port(TARGET))
        self.alignment_bias=np.zeros(3);self.alignment_rotation_bias=np.zeros(3);self.insertion_x=None;self.insertion_retries=0;self.bad_fit_frames=0
        self.guide_geometry=None;self.final_clearance=None;self.retention_gate_s=0.;self.retention_last_position=None;self.escape_count=0

    def release_targets(self,t,age,phase,plug,bodyR,travel,measured,targets):
        lp,lr,lg,rp,rr,rg=targets
        point=self.point.copy()
        # Selected support is tip_left, also when used by the RIGHT arm.
        point[0]+=measured[1][1][0]+.028
        rr=bodyR@self.pressR;rg=PRESS_GRIP
        local_contact=np.array((-.010,0,CLIP_Z+.0005))
        above=plug[:3]+bodyR@(local_contact+np.array((0,0,.0041)))-rr@point
        front=above+bodyR@np.array((-.040,0,0))
        far=front+bodyR@np.array((0,0,.025))
        actual_left,actual_right=measured[0][2:],measured[1][2:]
        left_ok=self.settled(actual_left,(lp,lr),.0015)
        jaw_ok=np.max(np.abs(measured[1][1]-PRESS_JAW))<.001

        if phase=='prepare_press':
            p0,r0=self.press_start;s=ik.smoothstep(min(1.,age/4.));rp=p0+s*(far-p0);rr=ik.slerp_matrix(r0,rr,s);rg=1.+(PRESS_GRIP-1.)*s
            self.gate(self.settled(actual_right,(far,bodyR@self.pressR)) and jaw_ok and left_ok,age,4.,5.,'lower_press_front',t)
        elif phase=='lower_press_front':
            rp=far+(front-far)*ik.smoothstep(min(1.,age/2.))
            self.gate(self.settled(actual_right,(front,rr)) and jaw_ok and left_ok,age,2.,5.,'insert_above_clip',t)
        elif phase=='insert_above_clip':
            rp=front+(above-front)*ik.smoothstep(min(1.,age/3.))
            settled=self.settled(actual_right,(above,rr)) and jaw_ok and left_ok
            if settled and age>=3.:
                left=[a@measured[0][3].T+measured[0][2] for _,a in self.geometry.pieces(measured[0][1])]
                sweep=[np.concatenate([a@rr.T+above-bodyR@np.array((0,0,depth)) for depth in (0.,.0064)]) for _,a in self.geometry.pieces(measured[1][1])]
                self.hand_clearance=minimum_separation(left,sweep)
                if self.hand_clearance<.0002:self.failure='measured loaded hands lack 0.2 mm certificate over clip press stroke'
            self.gate(settled and self.hand_clearance is not None and self.hand_clearance>=.0002,age,3.,5.,'depress_clip',t)
        elif phase=='depress_clip':
            self.press_depth=min(.0023,-.0041+.0007*age)
            rp=plug[:3]+bodyR@(local_contact-np.array((0,0,self.press_depth)))-rr@point
            self.stable_frames=self.stable_frames+1 if travel>=RELEASE_TRAVEL else 0
            if self.stable_frames>=5:
                self.withdraw_start=lp.copy();self.withdraw_plug=plug[:3].copy();self.pull_distance=0.;self.transition('withdraw_with_clip_pressed',t)
            elif age>10.5:self.failure='clip did not reach measured release travel within bounded 2.3 mm depression'
        elif phase=='withdraw_with_clip_pressed':
            # Maintain real clip travel while advancing the grasp target slowly;
            # the pressing hand follows the measured plug, not a stale point.
            self.press_depth=float(np.clip(self.press_depth+.12*(.00195-travel),.0015,.0023))
            rp=plug[:3]+bodyR@(local_contact-np.array((0,0,self.press_depth)))-rr@point
            if travel>=RELEASE_TRAVEL-.0001:self.pull_distance=min(.038,self.pull_distance+.0015*.05)
            lp=self.withdraw_start+np.array((-self.pull_distance,0,0))
            # Only the real hook must remain depressed while crossing the
            # retaining ledge. Following the plug all the way out makes the
            # spare jaw collide with a neighbouring roof. Read the actual hook
            # front before raising the pressing finger, then finish withdrawal.
            clip_pose=getattr(self,'measured_clip',None)
            if clip_pose is None:
                hook_front=max((plug[:3]+bodyR@np.array((x,y,CLIP_Z-travel+z)))[0]
                               for x,y,z in ((.006,-.0025,.0005),(.006,.0025,.0005),(.006,-.0025,.0025),(.006,.0025,.0025),(.010,-.0025,.0005),(.010,.0025,.0005)))
            else:
                clipR=quat_xyzw_to_matrix(clip_pose[3:])
                hook_front=max((clip_pose[:3]+clipR@np.array(v))[0]
                               for v in ((.006,-.0025,.0005),(.006,.0025,.0005),(.006,-.0025,.0025),(.006,.0025,.0025),(.010,-.0025,.0005),(.010,.0025,.0005)))
            self.measured_hook_front=float(hook_front)
            if hook_front<.407-.0005:
                self.withdraw_end=lp.copy();self.press_retreat=(rp.copy(),rr.copy());self.transition('lift_press_finger',t)
            elif age>15.:self.failure='actual hook did not clear retaining ledge while clip held depressed'
            elif travel<RELEASE_TRAVEL-.0002 and age>1.:
                # Pause withdrawal when the measured clip springs back; never
                # continue a timed pull through an engaged hook.
                if age>6. and self.pull_distance<.001:self.failure='clip depression could not be maintained for withdrawal'
        elif phase=='lift_press_finger':
            lp=self.withdraw_end
            p0,r0=self.press_retreat;rp=p0+np.array((0,0,.020))*ik.smoothstep(min(1.,age/2.));rr=r0
            self.gate(self.settled(actual_right,(rp,rr)),age,2.,5.,'finish_withdrawal',t)
        elif phase=='finish_withdrawal':
            self.pull_distance=min(.038,self.pull_distance+.002*.05)
            lp=self.withdraw_start+np.array((-self.pull_distance,0,0))
            p0,r0=self.press_retreat;rp=p0+np.array((0,0,.020));rr=r0
            tip=plug[:3]+bodyR@np.array((.012,0,0))
            if tip[0]<(.412-.027/2)-.003:
                self.source_clear=True;self.withdraw_end=lp.copy();self.transition('clear_press_finger',t)
            elif age>15.:self.failure='plug tip did not physically clear source housing after hook release'
        elif phase=='clear_press_finger':
            lp=self.withdraw_end
            p0,r0=self.press_retreat;rp=p0+np.array((0,0,.020))+np.array((-.080,0,.030))*ik.smoothstep(min(1.,age/3.));rr=r0
            self.gate(self.settled(actual_right,(rp,rr)),age,3.,5.,'align_empty_target',t)
            if self.phase!=phase:
                self.right_clear=(rp.copy(),rr.copy());self.align_start=lp.copy();self.align_plug_start=plug[:3].copy();self.align_body_start=bodyR.copy()
        elif phase=='align_empty_target':
            rp,rr=self.right_clear
            pretarget=self.target_origin+np.array((-.038,0,0));s=ik.smoothstep(min(1.,age/3.))
            # Learn only outside the mouth. This compensates actual plug pose,
            # rather than declaring a 1.5 mm TCP residual to be guide alignment.
            if age>=3.:
                tip=plug[:3]+bodyR@np.array((.012,0,0))
                if tip[0]>(.412-.027/2)-.003:self.failure='target alignment attempted before plug cleared mouth'
                error=pretarget-plug[:3]
                self.alignment_bias=np.clip(self.alignment_bias+.04*error,[-.001,-.0025,-.0025],[.001,.0025,.0025])
                self.alignment_rotation_bias=np.clip(self.alignment_rotation_bias+.02*ik._rot_error(np.eye(3),bodyR),-np.radians(1.5),np.radians(1.5))
            angle=np.linalg.norm(self.alignment_rotation_bias)
            correction=np.eye(3) if angle<1e-10 else axis_rotation(self.alignment_rotation_bias/angle,angle)
            command=self.align_plug_start+s*(pretarget-self.align_plug_start)+self.alignment_bias
            body_goal=correction@ik.slerp_matrix(self.align_body_start,np.eye(3),s)
            lp,lr=plug_hand_target(command,body_goal,plug,measured[0][2],measured[0][3])
            self.guide_geometry=plug_fit(plug,TARGET)
            ready=(self.guide_geometry['minimum_clearance_m']>=.0001 and abs(plug[0]-pretarget[0])<.002)
            self.gate(ready,age,3.,8.,'insert_empty_target',t)
            if self.phase!=phase:self.insertion_x=float(plug[0]);self.bad_fit_frames=0;self.frozen_alignment_rotation=body_goal.copy()
        elif phase=='insert_empty_target':
            rp,rr=self.right_clear;self.guide_geometry=plug_fit(plug,TARGET)
            fit=self.guide_geometry
            # Guide contact is ordinary insertion contact. Stop advancing for
            # substantial transverse interference, and retract to realign;
            # no correction integral is accumulated against a wall.
            guide_safe=(fit['minimum_clearance_m']>=-.0001 and fit['axis_angle_deg']<5. and fit['lateral_error_m']<.001)
            self.bad_fit_frames=self.bad_fit_frames+1 if not guide_safe else 0
            if guide_safe and self.insertion_x-plug[0]<.0007:self.insertion_x=min(self.target_origin[0],self.insertion_x+.003*.05)
            command=self.target_origin+np.array((self.insertion_x-self.target_origin[0],0,0))+self.alignment_bias
            lp,lr=plug_hand_target(command,self.frozen_alignment_rotation,plug,measured[0][2],measured[0][3])
            tip=plug[:3]+bodyR@np.array((.012,0,0))
            seated=(self.insertion_x>=self.target_origin[0]-1e-8 and tip[0]>(.412-.027/2)+.008
                    and fit['lateral_error_m']<.001 and fit['axis_angle_deg']<5.)
            self.gate(seated,age,0.,22.,'seat_and_release_clip',t)
            if self.bad_fit_frames>=3:
                if self.insertion_retries>=2:self.failure='actual plug/guide fit failed after two bounded realignments'
                else:
                    self.insertion_retries+=1;self.retract_plug_start=plug[:3].copy();self.retract_body_start=bodyR.copy();self.transition('retract_for_alignment',t)
        elif phase=='retract_for_alignment':
            rp,rr=self.right_clear;goal=self.target_origin+np.array((-.038,0,0));s=ik.smoothstep(min(1.,age/3.))
            command=self.retract_plug_start+s*(goal-self.retract_plug_start)
            lp,lr=plug_hand_target(command,self.retract_body_start,plug,measured[0][2],measured[0][3])
            clear=abs(plug[0]-goal[0])<.002
            self.gate(clear,age,3.,5.,'align_empty_target',t)
            if self.phase!=phase:self.align_plug_start=plug[:3].copy();self.align_body_start=bodyR.copy();self.alignment_bias[:]=0.;self.alignment_rotation_bias[:]=0.
        elif phase=='seat_and_release_clip':
            command=self.target_origin+self.alignment_bias;lp,lr=plug_hand_target(command,self.frozen_alignment_rotation,plug,measured[0][2],measured[0][3]);rp,rr=self.right_clear
            face=retaining_face(getattr(self,'measured_clip',self.object_pose(f'clip_{SERVICE}')),TARGET)
            fit=plug_fit(plug,TARGET)
            self.gate(travel<.0003 and face['retained'] and fit['axis_angle_deg']<5. and fit['lateral_error_m']<.001,age,1.,5.,'release_boot',t)
            if self.phase!=phase:self.seated_hand_target=(lp.copy(),lr.copy())
        elif phase=='release_boot':
            lp,lr=self.seated_hand_target;rp,rr=self.right_clear;lg=GRIP+(ENTRY_GRIP-GRIP)*ik.smoothstep(min(1.,age/2.))
            self.gate(np.max(np.abs(measured[0][1]+.0065))<.001,age,2.,5.,'retreat_hands',t)
            if self.phase!=phase:self.retreat_start=(lp.copy(),lr.copy());self.hold_offset=None
        elif phase=='retreat_hands':
            p0,r0=self.retreat_start;s=ik.smoothstep(min(1.,age/3.));lp=p0+np.array((-.11,0,0))*s;lr=r0;lg=ENTRY_GRIP;rp,rr=self.right_clear
            self.gate(self.settled(actual_left,(lp,lr),.002),age,3.,5.,'certify_open_clearance',t)
        elif phase=='certify_open_clearance':
            lp,lr=measured[0][2].copy(),measured[0][3].copy();lg=ENTRY_GRIP;rp,rr=self.right_clear
            state=snapshot(self.object_pose)
            left=gripper_sweep(self.geometry,measured[0][1],lp,lr,end_fingers=[FINGER_OPEN,FINGER_OPEN])
            right=[a@measured[1][3].T+measured[1][2] for _,a in self.geometry.pieces(measured[1][1])]
            self.final_clearance=clearance(left+right,state)
            mutual=minimum_separation(left,right)
            if self.final_clearance['minimum_gap_m']>=.005 and mutual>=.005:
                self.final_hand_target=(lp.copy(),lr.copy());self.transition('open_clear_hands',t)
            elif self.escape_count>=3:self.failure='full jaw opening lacks measured object/cable clearance after three retreats'
            else:
                # Remain partially open while choosing a complete, certified
                # escape translation. Fully open jaws are never swept blindly
                # through the hanging cables at the old straight-back height.
                for delta in (np.array((0,0,.080)),np.array((-.050,0,.060)),np.array((0,.080,.060))):
                    moving=gripper_sweep(self.geometry,measured[0][1],lp,lr,translation=delta)
                    cert=clearance(moving+right,state,wire_margin=.001)
                    if cert['minimum_gap_m']>=.001 and minimum_separation(moving,right)>=.001:
                        self.escape_start=(lp.copy(),lr.copy());self.escape_delta=delta;self.escape_count+=1;self.transition('retreat_partially_open',t);break
                else:self.failure='partially open hand has no certified cable-clear retreat translation'
        elif phase=='retreat_partially_open':
            p0,r0=self.escape_start;lp=p0+self.escape_delta*ik.smoothstep(min(1.,age/3.));lr=r0;lg=ENTRY_GRIP;rp,rr=self.right_clear
            self.gate(self.settled(actual_left,(lp,lr),.002),age,3.,5.,'certify_open_clearance',t)
        elif phase=='open_clear_hands':
            lp,lr=self.final_hand_target;rp,rr=self.right_clear;lg=ENTRY_GRIP+(1-ENTRY_GRIP)*ik.smoothstep(min(1.,age/1.5))
            self.gate(np.max(np.abs(measured[0][1]-FINGER_OPEN))<.001,age,1.5,5.,'retention_rest',t)
        elif phase=='retention_rest':
            lp,lr=self.final_hand_target;lg=1.;rp,rr=self.right_clear
            state=snapshot(self.object_pose);parts=[]
            for arm in measured:parts.extend(a@arm[3].T+arm[2] for _,a in self.geometry.pieces(arm[1]))
            self.final_clearance=clearance(parts,state)
            face=retaining_face(state[1][SERVICE],TARGET);fit=plug_fit(plug,TARGET)
            speed=0. if self.retention_last_position is None else np.linalg.norm(plug[:3]-self.retention_last_position)/.05
            self.retention_last_position=plug[:3].copy()
            ready=(self.final_clearance['minimum_gap_m']>=.005 and face['retained'] and travel<.0003 and fit['axis_angle_deg']<5.
                   and fit['lateral_error_m']<.001 and speed<.01 and all(np.linalg.norm(arm[2]-plug[:3])>.070 for arm in measured))
            self.retention_gate_s=self.retention_gate_s+.05 if ready else 0.
            if age>12.:self.failure='actual unheld latch/whole-gripper clearance did not maintain a released hold'
        else:raise RuntimeError('unknown release phase '+phase)
        return lp,lr,lg,rp,rr,rg
