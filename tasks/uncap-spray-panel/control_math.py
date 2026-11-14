"""Gripper unit conversion with a guard against the original positive-sign bug."""
import math


def grip_fraction(joint_target,open_joint):
    if not (math.isfinite(joint_target) and math.isfinite(open_joint) and
            open_joint<0 and open_joint<=joint_target<=0):
        raise ValueError('YAM finger targets must be negative metres, open_joint..0')
    return joint_target/open_joint
