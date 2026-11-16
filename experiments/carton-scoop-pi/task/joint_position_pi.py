"""Transactional proprioceptive outer-loop PI for ordinary joint targets.

No simulator, objects, forces, poses, or mechanical-drive settings are read.
The caller must guard BOTH fresh actual geometry and the exact augmented
command before resolving a proposal. No path may advance before resolution.
"""
from dataclasses import dataclass
import math
import numpy as np


def _six(value, label):
    value = np.asarray(value, dtype=float)
    if value.shape != (6,) or not np.isfinite(value).all():
        raise ValueError(label + ' must contain six finite joint values')
    return value.copy()


@dataclass(frozen=True)
class Proposal:
    command: tuple
    proposed_bias: tuple
    time_s: float
    dt_s: float
    kind: str
    valid: bool
    command_clipped: bool
    reason: str | None = None


@dataclass(frozen=True)
class Resolution:
    accepted: bool
    command: tuple
    bias: tuple
    path_dt_s: float
    reason: str | None


class JointPositionPI:
    """One outstanding proposal; commit only after caller safety approval.

    `begin` is the only reset. Nominal references are unaugmented targets,
    never the preceding augmented command. The first command is preserved
    exactly, with no I update or path advance. Rejected ticks are not integrated
    later. Invalid state latches a held-command failure until explicit `begin`.
    """

    def __init__(self, lower, upper, *, ki=.5, bias_cap=.02,
                 bias_rate=.005, command_step=.04, max_dt=.05):
        self.lower = _six(lower, 'lower limits')
        self.upper = _six(upper, 'upper limits')
        values = (ki, bias_cap, bias_rate, command_step, max_dt)
        if (not all(math.isfinite(x) for x in values)
                or ki < 0 or min(values[1:]) <= 0
                or bias_cap > .02 or bias_rate > .005
                or command_step > .04 or max_dt > .05
                or np.any(self.lower >= self.upper)):
            raise ValueError('invalid or enlarged PI/command bounds')
        self.ki = float(ki)
        self.bias_cap = float(bias_cap)
        self.bias_rate = float(bias_rate)
        self.command_step = float(command_step)
        self.max_dt = float(max_dt)
        self._issued = None
        self._bias = np.zeros(6)
        self._pending = None
        self._observed_time = None
        self._started = False
        self._failure = None

    @property
    def bias(self):
        return self._bias.copy()

    @property
    def issued(self):
        return None if self._issued is None else self._issued.copy()

    @property
    def failure(self):
        return self._failure

    def begin(self, last_issued, time_s):
        issued = _six(last_issued, 'last issued command')
        if (not math.isfinite(time_s) or time_s < 0
                or np.any(issued < self.lower) or np.any(issued > self.upper)):
            raise ValueError('initial command/clock outside declared bounds')
        self._issued = issued
        self._bias = np.zeros(6)
        self._observed_time = float(time_s)
        self._pending = None
        self._started = False
        self._failure = None

    def _hold(self, time_s, kind, valid, reason=None):
        # time_s is telemetry; even an invalid nonfinite clock never enters JSON.
        clock = float(time_s) if math.isfinite(time_s) else self._observed_time
        proposal = Proposal(tuple(self._issued), tuple(self._bias), clock,
                            0., kind, valid, False, reason)
        self._pending = proposal
        return proposal

    def propose(self, nominal, actual, time_s):
        if self._issued is None:
            raise RuntimeError('begin(last_issued, time_s) is required')
        if self._pending is not None:
            raise RuntimeError('resolve the outstanding proposal before proposing')
        if self._failure is not None:
            return self._hold(self._observed_time, 'invalid', False, self._failure)
        try:
            nominal = _six(nominal, 'unbiased nominal target')
            actual = _six(actual, 'own measured joints')
            if (not math.isfinite(time_s) or time_s < self._observed_time
                    or time_s - self._observed_time > self.max_dt + 1e-9
                    or np.any(nominal < self.lower) or np.any(nominal > self.upper)):
                raise ValueError('nonmonotonic/gapped clock or illegal nominal target')
        except (ValueError, TypeError, OverflowError) as error:
            self._failure = str(error)
            return self._hold(self._observed_time, 'invalid', False, self._failure)
        dt = min(self.max_dt, float(time_s) - self._observed_time)
        self._observed_time = float(time_s)
        if not self._started:
            return self._hold(time_s, 'initial_handoff', True)
        if dt == 0:
            return self._hold(time_s, 'duplicate_clock', True)

        # Integral error is NOMINAL - measured, not augmented command - measured.
        increment = np.clip(self.ki * dt * (nominal - actual),
                            -self.bias_rate * dt, self.bias_rate * dt)
        candidate_bias = np.clip(self._bias + increment,
                                 -self.bias_cap, self.bias_cap)
        increment = candidate_bias - self._bias
        low = np.maximum(self.lower, self._issued - self.command_step)
        high = np.minimum(self.upper, self._issued + self.command_step)
        augmented = nominal + candidate_bias
        outward = ((augmented > high) & (increment > 0)
                   | (augmented < low) & (increment < 0))
        candidate_bias[outward] = self._bias[outward]
        augmented = nominal + candidate_bias
        command = np.clip(augmented, low, high)
        clipped = bool(np.any(command != augmented))
        proposal = Proposal(tuple(command), tuple(candidate_bias), float(time_s),
                            dt, 'tracking', True, clipped)
        self._pending = proposal
        return proposal

    def resolve(self, proposal, *, guard_safe):
        """Commit only this exact immutable proposal, or retain prior state.

        `guard_safe` combines fresh actual safety and the safety of
        `proposal.command`, after every applicable joint/action clamp. A false
        result rejects the whole vector: no integral or issued-command commit,
        and `path_dt_s` is zero. Clock-clipped commands also cannot advance path.
        """
        if self._pending is None or proposal is not self._pending:
            raise RuntimeError('stale or foreign PI proposal')
        if type(guard_safe) is not bool:
            raise ValueError('guard_safe must be an explicit bool')
        self._pending = None
        accepted = bool(guard_safe and proposal.valid
                        and proposal.kind != 'duplicate_clock')
        if accepted:
            self._issued = np.asarray(proposal.command).copy()
            self._bias = np.asarray(proposal.proposed_bias).copy()
            self._started = True
        path_dt = (proposal.dt_s if accepted and not proposal.command_clipped else 0.)
        reason = (proposal.reason if not proposal.valid else
                  'caller_guard_rejected' if not guard_safe else
                  'duplicate_clock' if proposal.kind == 'duplicate_clock' else
                  'command_limit_path_hold' if proposal.command_clipped else None)
        return Resolution(accepted, tuple(self._issued), tuple(self._bias),
                          path_dt, reason)
