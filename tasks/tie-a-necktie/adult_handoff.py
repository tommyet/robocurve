"""Ordinary two-hand tip transfer after the native adult pickup.

Only a disclosed scripted demonstration reads native material coordinates.
Every output is an ordinary bounded joint or finger target; no simulator state
writer, attachment, force or cloth mutation is available here.
"""
import copy,hashlib,json
from pathlib import Path
import numpy as np


def _compile(start_action,schedule):
    from yam_arena import ik,station
    from yam_arena.constants import SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    q={s:np.asarray(start_action,float)[7*i:7*i+6].copy() for i,s in enumerate(('left','right'))}
    opening={s:float(start_action[7*i+6]) for i,s in enumerate(('left','right'))};frames=[];audits=[]
    for seconds,side,position,grip,rotation,label,mode in schedule:
        position=np.asarray(position);p0,r0=ik.tcp_pose(q[side],station.BASES[side]);q0=q[side].copy();o0=opening[side];pe_max=re_max=0.;goal=None
        if mode=='joint':
            goal,pe,re=ik.solve(position,ik.matrix_to_quat_xyzw(rotation),q0,base_pos=station.BASES[side],iters=600)
            if pe>.004 or re>.04:raise ValueError('Measured receiving approach is unreachable')
        for k in range(1,round(seconds*20)+1):
            t=ik.smoothstep(k/(seconds*20))
            if goal is not None:q[side]=q0+t*(goal-q0);pe=re=0.
            else:q[side],pe,re=ik.solve(p0+t*(position-p0),ik.matrix_to_quat_xyzw(ik.slerp_matrix(r0,rotation,t)),q[side],base_pos=station.BASES[side],iters=120)
            pe_max=max(pe_max,float(pe));re_max=max(re_max,float(re));opening[side]=o0+t*(grip-o0)
            frames.append(dict(action14=np.r_[q['left'],opening['left'],q['right'],opening['right']].tolist(),stage=label))
        audits.append(dict(stage=label,max_position_error_m=pe_max,max_rotation_error_rad=re_max))
    if any(a['max_position_error_m']>.004 or a['max_rotation_error_rad']>.04 for a in audits):raise ValueError('Measured handoff IK gate failed: '+json.dumps(audits))
    actions=np.asarray([start_action]+[f['action14'] for f in frames]);limits=np.tile([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20],2)
    if np.any(abs(np.diff(actions,axis=0))>limits*1.001):raise ValueError('Handoff exceeds normal action speeds')
    return dict(schema='cloth-fixed-motion-fragment-v1',frames=frames,action_count=len(frames),kinematic_audit=audits,feedback='Explicit native-state scripted planning of ordinary robot actions only',score=None)


def raise_for_transfer(start_action):
    from cross_motion import yaw_rotation
    return _compile(start_action,[(3.,'right',(.30,-.16,1.30),0.,yaw_rotation(30.),'raise and turn held wide strip for tip transfer','cartesian')])


def receive_tip(start_action,rest,nodes,approach_tilt_degrees=10.):
    from adult_motion import grasp_frame
    from cross_motion import yaw_rotation
    grasp=grasp_frame(rest,nodes,longitudinal=.03,side='left')
    if not -20. <= approach_tilt_degrees <= 20.:
        raise ValueError('Receiving tilt exceeds the bounded planning range')
    angle=np.deg2rad(approach_tilt_degrees)
    # Rotate the approach within the material plane. The closing normal is
    # unchanged; this moves the forearm clear of the loose narrow strand.
    turn=np.array([[1.,0.,0.],[0.,np.cos(angle),-np.sin(angle)],[0.,np.sin(angle),np.cos(angle)]])
    R=np.asarray(grasp['rotation'])@turn
    target=np.asarray(grasp['center_m'])+.020*R[:,2]
    grasp.update(rotation=R.tolist(),target_tcp_m=target.tolist(),approach_tilt_degrees=float(approach_tilt_degrees))
    if not (.20<target[0]<.39 and -.25<target[1]<-.06 and .80<target[2]<1.02):raise ValueError('Measured wide tip lies outside the receiving workspace: '+repr(target.tolist()))
    schedule=[(2.,'left',(.18,.25,1.03),.6,yaw_rotation(90.),'withdraw in front of both strands','joint'),
        (2.,'left',(.17,-.20,.94),.6,yaw_rotation(180.),'cross open front space','cartesian'),
        (2.,'left',target,.6,R,'insert receiving fingers around wide tip','cartesian'),
        (1.,'left',target,0.,R,'pinch wide tip with receiving hand','cartesian'),
        (2.,'right',(.30,-.16,1.30),1.,yaw_rotation(30.),'release original wide-strand pinch','cartesian'),
        (2.,'right',(.23,-.24,1.30),1.,yaw_rotation(30.),'withdraw original hand','cartesian'),
        (3.,'left',(.24,-.14,1.16),0.,yaw_rotation(150.),'lift wide tip clear for knotting','cartesian'),
        (1.,'left',(.24,-.14,1.16),0.,yaw_rotation(150.),'hold transferred wide tip','cartesian')]
    plan=_compile(start_action,schedule);plan['grasp']=grasp;plan['approach_steps']=120;plan['native_nodes_sha256']=hashlib.sha256(np.ascontiguousarray(nodes).tobytes()).hexdigest();return plan


def template(pickup):
    plan=copy.deepcopy(pickup);plan['frames']+=raise_for_transfer(plan['frames'][-1]['action14'])['frames'];hold=copy.deepcopy(plan['frames'][-1]);hold['stage']='placeholder awaiting measured tip handoff';plan['frames'] += [copy.deepcopy(hold) for _ in range(300)];plan['action_count']=len(plan['frames']);plan['requires_state_assisted_handoff']=True;plan['do_not_run_reason']='Awaiting full handoff hull and receiving-cloth approach checks';return plan


def classify_receiving_contacts(hits,rest,faces):
    """Separate intended fingertip contact from forbidden body/strand crossings.

    Only the final insertion may touch the first10cm of the wide end with
    finger links. Forearm, palm and narrow-strand intersections stay blocked.
    The full raw screen remains in evidence; permission to attempt contact is
    not evidence that contact, the receiving pinch or the handoff succeeds.
    """
    rest=np.asarray(rest);faces=np.asarray(faces);blocked=[];intended=[]
    for sample in hits:
        good=[];bad=[]
        for hit in sample['hits']:
            material=rest[faces[np.asarray(hit['faces'],int)],1]
            allowed=sample['step']>80 and hit['link'] in ('tip_left','tip_right') and material.min()>=0. and material.max()<=.10000001
            (good if allowed else bad).append(hit)
        if good:intended.append(dict(sample,hits=good))
        if bad:blocked.append(dict(sample,hits=bad))
    return blocked,intended


def select_receiving_plan(start_action, rest, nodes, faces, half_thickness):
    """Choose a clear ordinary approach from the measured loose cloth.

    Two millimetres is a route preference, never an acceptance threshold. The
    blocking check uses the actual shell half-thickness. A fallback may use
    closer surface clearance; all proximity warnings remain in the audit.
    """
    from audit_adult_motion import audit
    from audit_reset_approach import screen
    if not 0. < half_thickness <= .002:
        raise ValueError('Invalid material half-thickness')
    records=[];fallback=[]
    def validate(plan, entry):
        rigid=audit(plan)
        entry['rigid_intersections']=len(rigid['violations'])
        if not rigid['passed']:
            return None
        steps=range(1,plan['approach_steps']+1)
        hits=screen(plan,nodes,faces,steps=steps,side='left',inflation=half_thickness)
        blocked,intended=classify_receiving_contacts(hits,rest,faces)
        entry['forbidden_shell_contact_samples']=len(blocked)
        if blocked:
            return None
        proximity=screen(plan,nodes,faces,steps=steps,side='left',inflation=.001)
        approach=dict(samples=plan['approach_steps'],inflation_m=half_thickness,
            proximity_inflation_m=.001,proximity_warnings=proximity,
            raw_intersections=hits,blocked_intersections=blocked,
            intended_finger_contact=intended)
        return dict(plan=plan,rigid=rigid,approach=approach,candidates=records)
    for tilt in (10.,-10.,-20.,0.):
        entry=dict(approach_tilt_degrees=tilt);records.append(entry)
        try:
            plan=receive_tip(start_action,rest,nodes,approach_tilt_degrees=tilt)
        except ValueError as exc:
            entry['kinematic_error']=str(exc)
            continue
        near=screen(plan,nodes,faces,steps=range(116,121),side='left',inflation=.002)
        blocked,_=classify_receiving_contacts(near,rest,faces)
        entry['two_mm_final_approach_warning_samples']=len(blocked)
        if blocked:
            fallback.append((plan,entry))
            continue
        selected=validate(plan,entry)
        if selected is not None:
            selected['selection']='Clear physical route with additional final-approach separation'
            return selected
    for plan,entry in fallback:
        selected=validate(plan,entry)
        if selected is not None:
            selected['selection']='Physical shell-clear route; extra proximity warnings retained'
            return selected
    return dict(plan=None,candidates=records)
