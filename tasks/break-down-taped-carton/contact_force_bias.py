"""CPU-only Plan-B contact-bias proposal; NOT integrated or native-validated.

Maps a bounded requested robot-on-carton PUSH to ordinary YAM joint targets.
No actuator gains/effort limits, native forces, contacts or task state are written.
The conditional certificate can replace ONLY the issued unloaded intended-contact
proxy depth check. It cannot exempt actual contact, unrelated bodies, the other
arm, missing force clocks or effort/slew/joint bounds. This is not force control
or proof that a native force will equal the requested vector.
"""
from dataclasses import dataclass
import numpy as np
from yam_arena import ik
from yam_arena.constants import SHOULDER,WRIST

STIFFNESS=np.array([SHOULDER['stiffness']]*3+[WRIST['stiffness']]*3)
DAMPING=np.array([SHOULDER['damping']]*3+[WRIST['damping']]*3)
EFFORT=np.array([SHOULDER['effort']]*3+[WRIST['effort']]*3)
for constant in (STIFFNESS,DAMPING,EFFORT):constant.setflags(write=False)
JACOBIAN_EPS=1e-5
MAX_PUSH_N=3.
MAX_CONTACT_TCP_M=.1
EFFORT_MARGIN_NM=.5
MAX_JOINT_SLEW_RAD=.025
HARD_GAP_M=.0002
MAX_ACTUAL_DEPTH_M=.0006
MAX_NOMINAL_DEPTH_M=.002
MAX_FAMILY_FORCE_N=4.


def _array(value,shape,name):
    result=np.asarray(value,dtype=float)
    if result.shape!=shape or not np.isfinite(result).all():raise ValueError('invalid '+name)
    return result


def _joints(value,name):
    q=_array(value,(6,),name)
    if np.any(q<ik.LOWER) or np.any(q>ik.UPPER):raise ValueError(name+' outside unchanged joint bounds')
    return q


def contact_point(q,contact_tcp,base):
    q=_joints(q,'nominal joints');point=_array(contact_tcp,(3,),'TCP contact point');base=_array(base,(3,),'base')
    if np.linalg.norm(point)>MAX_CONTACT_TCP_M:raise ValueError('contact lever exceeds100mm')
    p,R=ik.tcp_pose(q,base)
    return p+R@point


def contact_jacobian(q_nominal,contact_tcp,base):
    q=_joints(q_nominal,'nominal joints');point=_array(contact_tcp,(3,),'TCP contact point');base=_array(base,(3,),'base')
    if np.linalg.norm(point)>MAX_CONTACT_TCP_M:raise ValueError('contact lever exceeds100mm')
    # Derivative probes may cross a joint endpoint mathematically; they are never
    # issued. The nominal and final action must satisfy unchanged joint limits.
    jac=np.empty((3,6))
    for i in range(6):
        d=np.zeros(6);d[i]=JACOBIAN_EPS
        plus,Rplus=ik.tcp_pose(q+d,base);minus,Rminus=ik.tcp_pose(q-d,base)
        jac[:,i]=(plus+Rplus@point-minus-Rminus@point)/(2*JACOBIAN_EPS)
    return jac



def modeled_existing_effort(q_nominal,q_actual,q_velocity,native_gravity_comp_current,*,declared_margin_nm):
    """Conservative absolute sum for the CURRENT sampled PD+own-GC request.

    Bound = |K(qnom-qactual)| + |D qvel| + |native own-GC| + declared margin.
    The native caller must select the actual six arm joint IDs from
    ArticulationData.gravity_compensation_forces (drop six floating-base entries
    only when its verified shape is num_joints+6). No assumed-zero gravity input
    or future-substep guarantee is supplied here. Native effort caps are unchanged.
    """
    nominal=_joints(q_nominal,'nominal joints');actual=_joints(q_actual,'actual joints')
    velocity=_array(q_velocity,(6,),'actual joint velocity');gravity=_array(native_gravity_comp_current,(6,),'current native gravity compensation')
    margin=_array(declared_margin_nm,(6,),'declared effort margin')
    if np.any(margin<0):raise ValueError('negative declared effort margin')
    position=np.abs(STIFFNESS*(nominal-actual));damping=np.abs(DAMPING*velocity);own_gc=np.abs(gravity)
    bound=position+damping+own_gc+margin
    return {'absolute_bound_Nm':bound.tolist(),'position_component_Nm':position.tolist(),
            'damping_component_Nm':damping.tolist(),'native_own_gravity_component_Nm':own_gc.tolist(),
            'declared_margin_Nm':margin.tolist(),'within_current_effort_caps':bool(np.all(bound<=EFFORT)),
            'scope':'CURRENT sampled modeled requested-effort absolute bound; not a future-substep/kernel force guarantee'}


def roles_for_stage(stage,*,brace_age_s=None,left_geometric_clear=False,left_previous_force_zero=False):
    """Trusted controller phase/event state derives exemptions, never caller roles."""
    if type(left_geometric_clear) is not bool or type(left_previous_force_zero) is not bool:raise ValueError('invalid measured brace-clear flags')
    if stage=='contact':return ('acquire','acquire')
    if stage=='first_roll':
        if brace_age_s is None:return ('push','push')
        if not np.isfinite(brace_age_s) or brace_age_s<0:raise ValueError('invalid brace release age')
        return ('inactive' if left_geometric_clear and left_previous_force_zero else 'release','push')
    if stage=='clear_first':return ('inactive','release')
    if stage=='bottom_contact':return ('inactive','acquire')
    if stage=='second_roll':return ('inactive','push')
    if stage=='finish_clear':return ('inactive','release')
    if stage in ('narrow_ready','approach','bottom_hover','return_ready'):return ('inactive','inactive')
    raise ValueError('stage has no reviewed contact-bias role contract')


def measured_force_summary(pair_force_world_by_arm,push_normals_world):
    """Actual sensor reaction is carton-on-robot, opposite requested robot push.

    Resistance = -sum(sensor reaction vectors) dot unit robot-push normal.
    Magnitude cap uses SUM of every finger/filter-cell vector norm per arm,
    never norm(net), so cancelling opposing contacts cannot hide excess force.
    Native frame, full-filter coverage and clock verification are caller duties.
    """
    normals=_array(push_normals_world,(2,3),'paired push normals')
    if not np.allclose(np.linalg.norm(normals,axis=1),1.,rtol=0.,atol=1e-8):raise ValueError('push normals must be unit')
    if len(pair_force_world_by_arm)!=2:raise ValueError('both arm force families required')
    magnitude=[];resistance=[]
    for pairs,n in zip(pair_force_world_by_arm,normals):
        pairs=np.asarray(pairs,dtype=float)
        if pairs.ndim!=2 or pairs.shape[1]!=3 or not np.isfinite(pairs).all():raise ValueError('invalid measured filter-pair forces')
        magnitude.append(float(np.linalg.norm(pairs,axis=1).sum()))
        resistance.append(float(-pairs.sum(axis=0)@n))
    return {'family_pair_norm_sums_N':magnitude,'signed_resisting_normal_forces_N':resistance,
            'sign_contract':'requested robot->carton push; sensor carton->robot reaction; resistance=-reaction dot push_normal'}

def force_target(q_nominal,force_world,contact_tcp,base,*,existing_effort_bound_nm):
    """Return q_nominal + tau/K once; caller must retain an unaugmented nominal.

    existing_effort_bound_nm is a CURRENT-sample modeled absolute bound on all
    *other* requested motor effort, not an omitted/assumed-zero native readback
    or a guarantee for subsequent physics substeps. The pure helper
    cannot establish that bound. Integration must verify its provenance/freshness.
    Requested F is robot-on-object push; Jc^T F adds actuator effort in that
    direction. No claim is made about achieved pressure under native saturation.
    """
    q=_joints(q_nominal,'nominal joints');force=_array(force_world,(3,),'requested push')
    bound=_array(existing_effort_bound_nm,(6,),'existing effort bound')
    if np.linalg.norm(force)>MAX_PUSH_N:raise ValueError('requested push exceeds3N')
    if np.any(bound<0.) or np.any(bound>EFFORT):raise ValueError('invalid existing effort bound')
    jac=contact_jacobian(q,contact_tcp,base);tau=jac.T@force
    effort_bound=bound+np.abs(tau)
    if np.any(effort_bound>EFFORT-EFFORT_MARGIN_NM):raise ValueError('insufficient unchanged motor effort margin')
    offset=tau/STIFFNESS;target=q+offset;_joints(target,'augmented target')
    return {'q_nominal':q.tolist(),'q_target':target.tolist(),'offset_rad':offset.tolist(),
            'bias_torque_Nm':tau.tolist(),'total_absolute_effort_bound_Nm':effort_bound.tolist(),
            'contact_jacobian_m_per_rad':jac.tolist(),'requested_push_world_N':force.tolist(),
            'metadata':{'scope':'proposed ordinary position-target bias only; no integration/native feasibility',
                        'target_rule':'unaugmented q_nominal + Jc(q_nominal)^T F / existing stiffness, once',
                        'central_difference_eps_rad':JACOBIAN_EPS,'requested_force_bound_N':MAX_PUSH_N,
                        'contact_lever_bound_m':MAX_CONTACT_TCP_M,'effort_margin_Nm':EFFORT_MARGIN_NM,
                        'actuator_stiffness_Nm_per_rad':STIFFNESS.tolist(),'unchanged_effort_limits_Nm':EFFORT.tolist()}}


@dataclass(frozen=True)
class GuardEvidence:
    """Caller-produced full315-piece guard on current geometry; no partial masks."""
    time_s:float
    hard_gap_m:float
    other_arm_gap_m:float
    target_gap_m:float
    all_unrelated_checked:bool
    intended_contact_enabled:bool=True


def intended_proxy_certificate(*,stage,q_nominal,q_augmented,q_actual,previous_issued,
                               force_world,contact_tcp,bases,push_normals_world,existing_effort_bound_nm,
                               effort_bound_time_s,effort_bound_verified,
                               nominal_guards,augmented_guards,actual_guards,
                               family_pair_norm_sums_N,signed_resisting_normal_forces_N,
                               now_s,force_time_s,native_force_clock_verified,
                               previous_accepted_force_world,previous_force_was_accepted,
                               previous_accepted_time_s,previous_accepted_ids,expected_previous_accepted_ids,
                               stage_started_s,brace_clear_started_s=None,left_geometric_clear=False):
    """Conditional per-arm guard certificate; never native feasibility evidence.

    Source-derived phase roles are acquire/push/release/inactive. LEFT may
    release while RIGHT keeps pushing during first_roll; after its *previously
    accepted* force is zero and actual clearance is measured, LEFT is inactive.
    Each release independently decays its exact last accepted WORLD vector.
    After1s, release may persist waiting for clearance only with exactly zero FF.
    Its start comes from brace_clear for LEFT or phase entry for RIGHT, not a
    separately restartable release timer. Controller-owned accepted IDs must
    match, time must be fresh (<=one20Hz control), and counters stay caller-owned.

    Reaction sign=-sensor carton-on-robot force dot robot-push normal. Family
    caps are SUM of all filter-pair norms. All guards and actual depth bounds
    always apply. Only active issued intended proxy depth can be exempted;
    inactive arms receive no bias or intended mask. Caller flags/IDs/provenance
    require native/source verification; this pure function cannot attest them.
    """
    result={'valid':False,'scope':'CPU-only proposed issued-INTENDED proxy exception; no native feasibility',
            'reasons':[],'replaces_only_issued_intended_depth':False}
    try:
        clocks=_array([now_s,force_time_s,effort_bound_time_s,stage_started_s],(4,),'evidence clocks')
        if now_s<0 or stage_started_s<0 or stage_started_s>now_s or np.max(np.abs(clocks[1:3]-now_s))>1e-9:raise ValueError('stale or mismatched force/effort clock')
        if native_force_clock_verified is not True:raise ValueError('native force clock unverified')
        if effort_bound_verified is not True:raise ValueError('existing effort bound unverified')
        qn=_array(q_nominal,(2,6),'paired nominal joints');qa=_array(q_augmented,(2,6),'paired augmented joints')
        actual=_array(q_actual,(2,6),'paired actual joints');prev=_array(previous_issued,(2,6),'previous issued joints')
        forces=_array(force_world,(2,3),'paired requested pushes');contacts=_array(contact_tcp,(2,3),'paired contact levers')
        prior=_array(previous_accepted_force_world,(2,3),'previous accepted WORLD forces')
        prior_times=_array(previous_accepted_time_s,(2,),'previous accepted timestamps')
        prior_ids=_array(previous_accepted_ids,(2,),'previous accepted IDs');expected_ids=_array(expected_previous_accepted_ids,(2,),'controller expected accepted IDs')
        if len(previous_force_was_accepted)!=2 or any(v is not True for v in previous_force_was_accepted):raise ValueError('previous force lacks accepted provenance')
        if np.any(prior_ids<0) or np.any(prior_ids!=np.floor(prior_ids)) or not np.array_equal(prior_ids,expected_ids):raise ValueError('wrong previous accepted force IDs')
        if np.any(now_s-prior_times < -1e-9) or np.any(now_s-prior_times>.05+1e-9):raise ValueError('stale previous accepted force')
        if np.any(np.linalg.norm(prior,axis=1)>MAX_PUSH_N):raise ValueError('previous accepted force exceeds3N')
        brace_age=None
        if brace_clear_started_s is not None and stage=='first_roll':
            brace_start=float(brace_clear_started_s)
            if not np.isfinite(brace_start) or brace_start<stage_started_s or brace_start>now_s:raise ValueError('invalid trusted brace-clear start')
            brace_age=now_s-brace_start
        roles=roles_for_stage(stage,brace_age_s=brace_age,left_geometric_clear=left_geometric_clear,left_previous_force_zero=bool(np.linalg.norm(prior[0])<=1e-12))
        active=tuple(role!='inactive' for role in roles)
        normals_world=_array(push_normals_world,(2,3),'paired push-normal directions')
        if not np.allclose(np.linalg.norm(normals_world,axis=1),1.,rtol=0.,atol=1e-8):raise ValueError('push-normal directions must be unit vectors')
        normal_push=np.einsum('ij,ij->i',forces,normals_world)
        for i,role in enumerate(roles):
            if role=='inactive' and (np.linalg.norm(forces[i])>1e-12 or np.linalg.norm(prior[i])>1e-12):raise ValueError('inactive arm requires zero requested/previous force')
            if role in ('acquire','push') and (normal_push[i]<0 or np.linalg.norm(forces[i]-normal_push[i]*normals_world[i])>1e-8):raise ValueError('requested force is not a normal push')
        base=_array(bases,(2,3),'paired bases');efforts=_array(existing_effort_bound_nm,(2,6),'paired effort bounds')
        magnitudes=_array(family_pair_norm_sums_N,(2,),'full family sum of pair norms');normals=_array(signed_resisting_normal_forces_N,(2,),'signed resisting normals')
        if np.any(magnitudes<0) or np.any(magnitudes>MAX_FAMILY_FORCE_N):raise ValueError('intended-family magnitude exceeds4N or invalid')
        if np.any(np.abs(normals)>magnitudes+1e-10):raise ValueError('signed normal exceeds measured family magnitude')
        for i in range(2):
            _joints(actual[i],'actual joints');_joints(prev[i],'previous issued joints')
            target=force_target(qn[i],forces[i],contacts[i],base[i],existing_effort_bound_nm=efforts[i])
            if not np.allclose(qa[i],target['q_target'],rtol=0.,atol=1e-10):raise ValueError('augmented target is not exactly one nominal force bias')
            if np.any(np.abs(qa[i]-prev[i])>MAX_JOINT_SLEW_RAD+1e-12):raise ValueError('unchanged25mrad issued slew exceeded')
        for label,guards in [('nominal',nominal_guards),('augmented',augmented_guards),('actual',actual_guards)]:
            if len(guards)!=2:raise ValueError('both arms require '+label+' guards')
            for i,g in enumerate(guards):
                if not isinstance(g,GuardEvidence) or g.all_unrelated_checked is not True:raise ValueError('incomplete '+label+' full-arm guard')
                if g.intended_contact_enabled is not active[i]:raise ValueError('guard intended exemption does not match phase-derived roles')
                _array([g.time_s,g.hard_gap_m,g.other_arm_gap_m,g.target_gap_m],(4,),label+' guard')
                if abs(g.time_s-now_s)>1e-9:raise ValueError('stale '+label+' actual-geometry guard')
                if g.hard_gap_m<HARD_GAP_M or g.other_arm_gap_m<HARD_GAP_M:raise ValueError(label+' unrelated/other-arm guard failed')
                if label=='nominal' and g.target_gap_m < -MAX_NOMINAL_DEPTH_M:raise ValueError('nominal intended depth exceeds2mm')
                if label=='actual' and g.target_gap_m < -MAX_ACTUAL_DEPTH_M:raise ValueError('actual intended depth exceeds0.6mm')
                if not active[i] and g.target_gap_m < -MAX_NOMINAL_DEPTH_M:raise ValueError('inactive arm has no issued intended-depth exemption')
        decay=[None,None]
        for i,role in enumerate(roles):
            if role=='acquire':
                if np.linalg.norm(forces[i])>.5:raise ValueError('unconfirmed acquire request exceeds0.5N')
                if actual_guards[i].target_gap_m>.0005:raise ValueError('acquire actual contact gap exceeds0.5mm')
            elif role=='push':
                if normals[i]<=.1:raise ValueError('push requires fresh resisting normal above0.1N on active arm')
            elif role=='release':
                norm2=float(prior[i]@prior[i]);lam=float(forces[i]@prior[i]/norm2) if norm2>1e-24 else 0.
                if lam < -1e-10 or lam>1.+1e-10 or np.linalg.norm(forces[i]-lam*prior[i])>1e-8:raise ValueError('release must decay exact previous accepted WORLD vector independently')
                began=brace_clear_started_s if i==0 and stage=='first_roll' else stage_started_s
                if began is None:raise ValueError('release lacks trusted controller event start')
                age=now_s-float(began)
                if age>=1.-1e-9 and np.linalg.norm(forces[i])>1e-12:raise ValueError('release requires zero force after1s event deadline')
                decay[i]=lam
        result.update(valid=True,replaces_only_issued_intended_depth=True,roles=list(roles),
                      release_decay_lambda_by_arm=decay,active_contacts=list(active),
                      augmented_intended_proxy_exceeds2mm=any(active[i] and g.target_gap_m < -MAX_NOMINAL_DEPTH_M for i,g in enumerate(augmented_guards)),
                      freshness_tolerance_s=1e-9,actual_depth_bound_m=MAX_ACTUAL_DEPTH_M,
                      nominal_depth_bound_m=MAX_NOMINAL_DEPTH_M,family_magnitude_bound_N=MAX_FAMILY_FORCE_N)
    except (ValueError,TypeError,IndexError) as error:result['reasons'].append(str(error))
    return result
