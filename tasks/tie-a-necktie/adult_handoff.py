"""Ordinary two-hand tip transfer after the native adult pickup.

Only a disclosed scripted demonstration reads native material coordinates.
Every output is an ordinary bounded joint or finger target; no simulator state
writer, attachment, force or cloth mutation is available here.
"""
import copy,hashlib,json
from pathlib import Path
import numpy as np

RECEIVING_ROUTE_RELEASED = True


def _compile(start_action,schedule,*,robust_joint=False):
    from yam_arena import ik,station
    from yam_arena.constants import SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    q={s:np.asarray(start_action,float)[7*i:7*i+6].copy() for i,s in enumerate(('left','right'))}
    opening={s:float(start_action[7*i+6]) for i,s in enumerate(('left','right'))};frames=[];audits=[]
    for seconds,side,position,grip,rotation,label,mode in schedule:
        position=np.asarray(position);p0,r0=ik.tcp_pose(q[side],station.BASES[side]);q0=q[side].copy();o0=opening[side];pe_max=re_max=0.;goal=None
        if mode=='joint':
            goal,pe,re=ik.solve(position,ik.matrix_to_quat_xyzw(rotation),q0,base_pos=station.BASES[side],iters=600)
            if robust_joint and (pe>.004 or re>.04):
                from scipy.optimize import least_squares
                def residual(candidate):
                    p,r=ik.tcp_pose(candidate,station.BASES[side])
                    return np.r_[p-position,.3*ik._rot_error(rotation,r)]
                offset=0 if side=='left' else 7
                seeds=(q0,np.asarray(start_action)[offset:offset+6],(ik.LOWER+ik.UPPER)/2)
                solutions=[least_squares(residual,np.clip(seed,ik.LOWER,ik.UPPER),
                    bounds=(ik.LOWER,ik.UPPER),max_nfev=200,ftol=1e-10,xtol=1e-10,gtol=1e-10)
                    for seed in seeds]
                result=min(solutions,key=lambda s:np.linalg.norm(s.fun))
                goal=result.x;pe=float(np.linalg.norm(result.fun[:3]));re=float(np.linalg.norm(result.fun[3:])/.3)
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
    return _compile(start_action,[(3.,'right',(.23,-.16,1.30),0.,yaw_rotation(30.),'bring held wide strip in front of collar for transfer','cartesian')])


def receive_tip(start_action,rest,nodes,approach_tilt_degrees=0.,receiving_opening=1.):
    from adult_motion import grasp_frame
    from cross_motion import yaw_rotation
    if receiving_opening!=1. or approach_tilt_degrees!=0.:
        raise ValueError('This released route uses a full opening and the measured material plane')
    grasp=grasp_frame(rest,nodes,longitudinal=.03,side='left')
    R=np.asarray(grasp['rotation'])
    target=np.asarray(grasp['center_m'])+.010*R[:,2]
    pre=target-.090*R[:,2]
    align=np.array((.16,.02,max(.94,target[2]+.04)))
    grasp.update(rotation=R.tolist(),target_tcp_m=target.tolist(),desired_material_tcp_depth_m=-.010,
        receiving_opening=1.,approach='Orient outside the wide edge, then enter along the finger axis')
    if not (.17<target[0]<.34 and -.27<target[1]<-.06 and .80<target[2]<1.02):
        raise ValueError('Measured wide tip lies outside the receiving workspace: '+repr(target.tolist()))
    schedule=[(1.5,'left',(.18,.25,1.03),1.,yaw_rotation(90.),'withdraw in front of both strands','joint'),
        (1.5,'left',align,1.,yaw_rotation(180.),'move around the wide-strip edge','cartesian'),
        (1.,'left',align,1.,R,'orient outside the cloth','cartesian'),
        (2.,'left',pre,1.,R,'align outside the wide-tip edge','cartesian'),
        (2.,'left',target,1.,R,'insert along the open finger axis','cartesian'),
        (1.,'left',target,0.,R,'pinch the wide tip','cartesian'),
        (2.,'left',(.24,-.14,1.16),0.,yaw_rotation(150.),'raise receiving tip while both hands retain the strip','cartesian'),
        (1.,'right',(.23,-.16,1.30),1.,yaw_rotation(30.),'release original pinch after raising the tip','cartesian'),
        (2.,'right',(.23,-.24,1.30),1.,yaw_rotation(30.),'withdraw original hand','cartesian'),
        (1.,'left',(.24,-.14,1.16),0.,yaw_rotation(150.),'hold transferred wide tip','cartesian')]
    plan=_compile(start_action,schedule)
    plan.update(grasp=grasp,approach_steps=160,release_original_from=221,release_original_through=240,
        native_nodes_sha256=hashlib.sha256(np.ascontiguousarray(nodes).tobytes()).hexdigest())
    return plan


def template(pickup):
    plan=copy.deepcopy(pickup);plan['frames']+=raise_for_transfer(plan['frames'][-1]['action14'])['frames'];hold=copy.deepcopy(plan['frames'][-1]);hold['stage']='placeholder awaiting measured tip handoff';plan['frames'] += [copy.deepcopy(hold) for _ in range(300)];plan['action_count']=len(plan['frames']);plan['requires_state_assisted_handoff']=True;plan['do_not_run_reason']='Awaiting full handoff hull and receiving-cloth approach checks';return plan


def classify_receiving_contacts(hits,rest,faces):
    """Classify static-material predictions without claiming actual penetration.

    The final open-finger insertion may touch the selected wide-tip patch.
    Link4/link5 may brush the loose, unheld final25cm of the narrow tail. That
    warning requires actual native integrity review; the cloth must respond
    physically. Contact with the held wide strip or neck band stays blocked.
    """
    rest=np.asarray(rest);faces=np.asarray(faces);blocked=[];intended=[];loose=[]
    for sample in hits:
        good=[];bad=[];tail=[]
        for hit in sample['hits']:
            material=rest[faces[np.asarray(hit['faces'],int)],1]
            if sample['step']>120 and hit['link'] in ('tip_left','tip_right') and material.min()>=0. and material.max()<=.10000001:
                good.append(hit)
            elif hit['link'] in ('link4','link5') and material.min()>=1.20:
                tail.append(hit)
            else:bad.append(hit)
        if good:intended.append(dict(sample,hits=good))
        if tail:loose.append(dict(sample,hits=tail))
        if bad:blocked.append(dict(sample,hits=bad))
    return blocked,intended,loose


def select_receiving_plan(start_action,rest,nodes,faces,half_thickness):
    """Measure the held strip once, then use ordinary axial receiving actions."""
    from audit_adult_motion import audit
    from audit_reset_approach import screen
    if not 0.<half_thickness<=.002:raise ValueError('Invalid material half-thickness')
    entry=dict(approach='axial, full opening,10mm bite');records=[entry]
    try:plan=receive_tip(start_action,rest,nodes)
    except ValueError as exc:
        entry['kinematic_error']=str(exc)
        return dict(plan=None,candidates=records)
    rigid=audit(plan);entry['rigid_intersections']=len(rigid['violations'])
    if not rigid['passed']:return dict(plan=None,candidates=records)
    hits=screen(plan,nodes,faces,steps=range(1,plan['approach_steps']+1),side='left',inflation=half_thickness)
    blocked,intended,loose=classify_receiving_contacts(hits,rest,faces)
    entry.update(blocked_static_contact_samples=len(blocked),loose_narrow_tail_warning_samples=len(loose))
    if blocked:return dict(plan=None,candidates=records)
    approach=dict(samples=plan['approach_steps'],inflation_m=half_thickness,raw_intersections=hits,
        blocked_intersections=blocked,intended_finger_contact=intended,
        permitted_loose_tail_contact_warnings=loose,
        meaning='Static cloth predicts loose narrow-tail contact. Native cloth response and actual integrity must be reviewed; this is not contact, transfer or knot proof.')
    return dict(plan=plan,rigid=rigid,approach=approach,candidates=records,
        selection='Axial receiving route; disclosed incidental loose narrow-tail contact remains subject to native review')


def receiving_material_present(rest,nodes,gripper_pose_xyzw):
    """Stop only an obvious empty pinch before releasing the original hand.

    This broad volume encloses the physical finger-pad region with generous
    clearance. Presence permits an attempt; it is never a grasp/retention score.
    """
    from interpret_motion import rotation_xyzw
    pose=np.asarray(gripper_pose_xyzw,float);R=rotation_xyzw(pose[3:])
    tcp=pose[:3]+R@np.array((0.,0.,.134))
    local=(np.asarray(nodes)-tcp)@R
    tip=np.asarray(rest)[:,1]<.10
    inside=tip&(abs(local[:,0])<.010)&(abs(local[:,1])<.025)&(local[:,2]>-.040)&(local[:,2]<.005)
    return dict(potentially_enclosed_tip_nodes=int(inside.sum()),obvious_empty_pinch=not bool(inside.any()),
        broad_tcp_volume_m={'x':[-.010,.010],'y':[-.025,.025],'z':[-.040,.005]},
        meaning='A broad empty-volume stop only. Material presence does not establish physical contact or a successful transfer.')
