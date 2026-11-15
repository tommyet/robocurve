"""Gripper unit conversion with a guard against the original positive-sign bug."""
import math


def grip_fraction(joint_target,open_joint):
    if not (math.isfinite(joint_target) and math.isfinite(open_joint) and
            open_joint<0 and open_joint<=joint_target<=0):
        raise ValueError('YAM finger targets must be negative metres, open_joint..0')
    return joint_target/open_joint


def ramp_scalar(current,target,speed,dt):
    """Rate-limited scalar approach, without overshoot."""
    if not all(math.isfinite(v) for v in (current,target,speed,dt)) or speed<0 or not 0<=dt<=.1:
        raise ValueError('ramp requires finite values, nonnegative speed and dt in 0..0.1')
    limit=speed*dt
    return current+max(-limit,min(limit,target-current))


def ramp_translation(current,target,speed,dt):
    """Euclidean translation-rate limit; return a fresh three-component list."""
    if len(current)!=3 or len(target)!=3:raise ValueError('translation requires three components')
    ramp_scalar(0.,0.,speed,dt)
    if not all(math.isfinite(v) for v in (*current,*target)):raise ValueError('nonfinite translation')
    delta=[b-a for a,b in zip(current,target)]
    length=math.sqrt(sum(v*v for v in delta))
    fraction=min(1.,speed*dt/max(1e-12,length))
    return [a+fraction*d for a,d in zip(current,delta)]
