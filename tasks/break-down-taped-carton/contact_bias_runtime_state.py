"""CPU-only B transaction building blocks. NOT connected to the native runner.

The ledger separates nominal planner actions from canonical float32 transport,
recomputes one bias after every changed nominal/force request, and publishes an
accepted-force ID only after an explicit successful-step acknowledgement. Its
conditional geometry/measurement context must come from a reviewed native
adapter; these bookkeeping checks cannot attest that caller provenance.
A future standalone nominal must be the measured force-free anchor plus only
a bounded tangent/orientation increment, not controller A normal preload plus
another total desired force. This ledger cannot establish that nominal contract.

Missing integration: per-candidate fresh actual/nominal/augmented full315 guard
production, current native effort/force binding, source-derived role/event hooks,
and the runner's post-step ACK call. This module grants NO native proxy-depth
exception by itself. Default controller A is unchanged.
"""
from dataclasses import dataclass
import copy
import numpy as np
from yam_arena import ik
from contact_force_bias import force_target,intended_proxy_certificate,GuardEvidence

SLEW=np.array([.025]*6+[.04]+[.025]*6+[.04])


def action(value):
    a=np.asarray(value,dtype=float)
    if a.shape!=(14,) or not np.isfinite(a).all():raise ValueError('invalid14D action')
    for offset in (0,7):
        if np.any(a[offset:offset+6]<ik.LOWER) or np.any(a[offset:offset+6]>ik.UPPER):raise ValueError('joint bound exceeded')
        if not 0<=a[offset+6]<=1:raise ValueError('finger action bound exceeded')
    return a.copy()


def canonical_target(nominal,force_world,contact_tcp,bases,effort_bounds):
    """Recompute from nominal once, then perform the actual nativefloat32 cast."""
    nominal=action(nominal);force=np.asarray(force_world,float)
    if force.shape!=(2,3) or not np.isfinite(force).all():raise ValueError('invalid paired force')
    issued=nominal.copy()
    for i in (0,1):
        result=force_target(nominal[i*7:i*7+6],force[i],contact_tcp[i],bases[i],existing_effort_bound_nm=effort_bounds[i])
        issued[i*7:i*7+6]=result['q_target']
    return action(issued.astype(np.float32).astype(float))


@dataclass(frozen=True)
class Accepted:
    nominal:np.ndarray
    issued:np.ndarray
    force_world:np.ndarray
    control_time_s:float
    ids:tuple
    def __post_init__(self):
        for name in ('nominal','issued','force_world'):
            value=np.array(getattr(self,name),dtype=float,copy=True);value.setflags(write=False);object.__setattr__(self,name,value)


class ForceLedger:
    def __init__(self,reset_action):
        self.reset_action=action(reset_action).astype(np.float32).astype(float)
        self.accepted=None;self.pending=None;self.next_ids=(1,1)

    def _check_start(self,now):
        if not np.isfinite(now) or now<0:raise ValueError('invalid control time')
        if self.pending is not None:raise ValueError('previous proposal lacks successful-step ACK')
        if self.accepted is not None and abs(now-self.accepted.control_time_s-.05)>1e-7:raise ValueError('accepted ledger is stale or non20Hz')

    def _queue(self,now,nominal,issued,forces,evidence):
        prior=self.reset_action if self.accepted is None else self.accepted.issued
        if np.any(np.abs(issued-prior)>SLEW+1e-12):raise ValueError('quantized14D issued slew exceeded')
        self.pending={'time':float(now),'nominal':nominal.copy(),'issued':issued.copy(),'force_world':np.asarray(forces,float).copy(),'evidence':copy.deepcopy(evidence)}
        return issued.astype(np.float32).copy()

    def queue_ordinary_zero(self,now,nominal,*,actual_guards,nominal_guards,issued_guards,measurement_clock_verified,effort_readback_verified):
        """No force and NO proxy exception: every ordinary guard still applies.

        This seeds zero-force provenance after the successful-step ACK. Flags
        are native-caller attestations, not a substitute for runner integration.
        """
        self._check_start(now);nominal=action(nominal);issued=action(nominal.astype(np.float32).astype(float))
        if self.accepted is not None and np.any(self.accepted.force_world!=0):raise ValueError('nonzero prior force requires certified release, not ordinary bypass')
        if measurement_clock_verified is not True or effort_readback_verified is not True:raise ValueError('native evidence missing')
        for label,guards,depth in [('actual',actual_guards,.0006),('nominal',nominal_guards,.002),('issued',issued_guards,.002)]:
            if len(guards)!=2:raise ValueError('both arms required')
            for g in guards:
                if not isinstance(g,GuardEvidence) or g.all_unrelated_checked is not True or abs(g.time_s-now)>1e-9 or not np.isfinite([g.time_s,g.hard_gap_m,g.other_arm_gap_m,g.target_gap_m]).all():raise ValueError('missing fresh full-arm '+label+' guard')
                if g.hard_gap_m<.0002 or g.other_arm_gap_m<.0002 or g.target_gap_m < -depth:raise ValueError('ordinary guard failed; no proxy exception')
        return self._queue(now,nominal,issued,np.zeros((2,3)),{'ordinary_zero_bias':True,'proxy_exception':False})

    def queue_certified(self,now,nominal,context):
        """Evaluate the full conditional helper; caller cannot supply prior IDs."""
        self._check_start(now)
        if self.accepted is None:raise ValueError('no acknowledged prior command')
        nominal=action(nominal);ctx=copy.deepcopy(context)
        issued=canonical_target(nominal,ctx['force_world'],ctx['contact_tcp'],ctx['bases'],ctx['existing_effort_bound_nm'])
        ctx.update(q_nominal=np.stack((nominal[:6],nominal[7:13])),q_augmented=np.stack((issued[:6],issued[7:13])),previous_issued=np.stack((self.accepted.issued[:6],self.accepted.issued[7:13])),previous_accepted_force_world=self.accepted.force_world.copy(),previous_force_was_accepted=[True,True],previous_accepted_time_s=[self.accepted.control_time_s]*2,previous_accepted_ids=list(self.accepted.ids),expected_previous_accepted_ids=list(self.accepted.ids),now_s=float(now),issued_dtype='float32')
        certificate=intended_proxy_certificate(**ctx)
        if not certificate['valid']:raise ValueError('conditional certificate failed: '+str(certificate['reasons']))
        return self._queue(now,nominal,issued,ctx['force_world'],certificate)

    def acknowledge_successful_step(self,input_control_time_s,emitted_action):
        """CALL ONLY after env.step returned successfully; failure means no ACK."""
        if self.pending is None:raise ValueError('no pending proposal')
        emitted=np.asarray(emitted_action)
        if emitted.shape!=(14,) or not np.isfinite(emitted).all() or not np.array_equal(emitted.astype(float),emitted.astype(np.float32).astype(float)):raise ValueError('ACK is not canonical nativefloat32 transport')
        if abs(float(input_control_time_s)-self.pending['time'])>1e-9 or emitted.astype(np.float32).tobytes()!=self.pending['issued'].astype(np.float32).tobytes():raise ValueError('ACK time or emitted bits do not match proposal')
        p=self.pending
        self.accepted=Accepted(p['nominal'].copy(),p['issued'].copy(),p['force_world'].copy(),p['time'],self.next_ids)
        self.next_ids=tuple(i+1 for i in self.next_ids);self.pending=None
        return self.accepted


class StickyReleaseEvents:
    """Observed angle/COM events survive any planner rollback; not bound yet."""
    def __init__(self):self.left_start=None;self.right_first_start=None;self.right_finish_start=None
    def observe(self,now,*,stage,stage_started_s,angle_deg,com_beyond_support_m):
        if not np.isfinite([now,stage_started_s,angle_deg,com_beyond_support_m]).all() or not 0<=stage_started_s<=now:raise ValueError('invalid observed event')
        if stage=='first_roll':
            if angle_deg>25 and self.left_start is None:self.left_start=float(now)
            if com_beyond_support_m>.003 and now-stage_started_s>1 and self.right_first_start is None:self.right_first_start=float(now)
        if stage=='second_roll' and com_beyond_support_m>.003 and now-stage_started_s>1 and self.right_finish_start is None:self.right_finish_start=float(now)
    @staticmethod
    def decay_exact_world(previous_force_world,previous_accepted_time_s,now,event_started_s):
        previous=np.asarray(previous_force_world,float)
        if previous.shape!=(3,) or not np.isfinite(previous).all() or not np.isfinite([previous_accepted_time_s,now,event_started_s]).all() or event_started_s>now or previous_accepted_time_s>now:raise ValueError('invalid release provenance')
        age=now-event_started_s
        if age>=1:return np.zeros(3)
        remaining_before=max(1e-12,1-max(0.,previous_accepted_time_s-event_started_s))
        factor=min(1.,max(0.,(1-age)/remaining_before))
        return factor*previous
