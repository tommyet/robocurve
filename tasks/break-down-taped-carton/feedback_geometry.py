"""CPU geometry/gates for ordinary feedback robot commands; no physics writes."""
import numpy as np


def blade_tcp_target(blade_goal, tool_rotation, tool_in_hand_rotation, tip_in_hand):
    """Compensate the *rotated* measured TCP-to-blade offset exactly."""
    hand_rotation=np.asarray(tool_rotation)@np.asarray(tool_in_hand_rotation).T
    return np.asarray(blade_goal)-hand_rotation@np.asarray(tip_in_hand),hand_rotation


def measured_blade_grasp(tcp,hand_rotation,tool_position,tool_rotation,tip_local=(.062,0.,-.020)):
    """Read the current rigid relationship, including real handle slip."""
    tip=np.asarray(tool_position)+np.asarray(tool_rotation)@np.asarray(tip_local)
    return np.asarray(hand_rotation).T@tool_rotation,np.asarray(hand_rotation).T@(tip-tcp),tip


def missing_cut_spans(cells,cut,margin=.004):
    """Read-only bounded physical retraces: one span per incomplete tape path."""
    from model import CUT_PATHS
    spans=[]
    for group,a,b in CUT_PATHS:
        axis=0 if a[0]!=b[0] else 1
        missing=[np.asarray(p,dtype=float) for i,(name,p) in enumerate(cells) if name==group and i not in cut]
        if not missing:continue
        first=np.array(a,dtype=float);last=np.array(b,dtype=float)
        first[axis]=max(a[axis]-margin,min(p[axis] for p in missing)-margin)
        last[axis]=min(b[axis]+margin,max(p[axis] for p in missing)+margin)
        # The reachable seam grip traverses +X -> -X. End folds traverse +Y.
        start,end=(last,first) if group=='seam' else (first,last)
        spans.append({'group':group,'start':start,'end':end,'missing_cells':len(missing)})
    return spans


def flap_grip_frame(outward, approach, tangent_sign):
    """Y runs along the edge; X (the finger closing axis) crosses the edge."""
    outward=np.asarray(outward,dtype=float).copy();outward[2]=0.;outward/=np.linalg.norm(outward)
    z=np.asarray(approach,dtype=float);z/=np.linalg.norm(z)
    y=tangent_sign*np.cross((0.,0.,1.),outward);y/=np.linalg.norm(y)
    x=np.cross(y,z);x/=np.linalg.norm(x)
    return np.column_stack((x,y,z))


class TrackedProgress:
    """Advance a Cartesian path only while actual pose follows its last target."""
    def __init__(self,length,angle,speed=.035,angular_speed=.7):
        self.length=float(length);self.angle=float(angle);self.speed=speed;self.angular_speed=angular_speed;self.fraction=0.;self.settled=0
    def update(self,dt,position_error,rotation_error,endpoint_error,endpoint_rotation,position_tolerance=.003,
               tracking_tolerance=.006,rotation_tracking_tolerance=.07,advance_allowed=True):
        if advance_allowed and position_error<=tracking_tolerance and rotation_error<=rotation_tracking_tolerance:
            duration=max(self.length/self.speed,self.angle/self.angular_speed,.05)
            self.fraction=min(1.,self.fraction+dt/duration)
        ready=self.fraction>=1.-1e-12 and endpoint_error<=position_tolerance and endpoint_rotation<=.06
        self.settled=self.settled+1 if ready else 0
        return self.settled>=3


def cut_entry_bias(bias,previous,phase,local_start,local_rotation):
    """Carry a matching lower endpoint's WORLD bias unchanged into its cut."""
    value=np.asarray(bias,dtype=float)
    if value.shape!=(3,) or not np.isfinite(value).all() or np.any(abs(value)>.003):
        raise ValueError('cut entry bias must be finite within existing3mm bounds')
    return value.copy() if matching_lower_cut(previous,phase,local_start,local_rotation) else np.zeros(3)


def matching_lower_cut(previous,phase,local_start,local_rotation):
    return (previous is not None and phase.endswith('_cut') and
              previous['phase']==phase[:-4]+'_lower' and
              np.allclose(previous['local_endpoint'],local_start,rtol=0.,atol=1e-6) and
              np.allclose(previous['local_rotation'],local_rotation,rtol=0.,atol=1e-6))


def cut_watchdog(elapsed,idle):
    """Honest wall limits; an accepted cursor increment resets only idle time."""
    if elapsed>100.:return 'cut phase exceeded100second hard cap'
    if idle>20.:return 'cut cursor had no accepted advance for20seconds'
    return None
