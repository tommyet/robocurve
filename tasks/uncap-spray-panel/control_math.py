"""Gripper unit conversion with a guard against the original positive-sign bug."""
import math
import numpy as np

GRASP_Z=-.010
GRASP_OFFSET=np.array((0.,0.,GRASP_Z))
RELEASE_DISTANCE=.030
RELEASE_SPEED=.010
RELEASE_DEADLINE=10. # Maximum permitted path-derived release deadline.
MEASURED_DWELL=.8


def minimum_future_seconds(moves):
    """Necessary future work, rather than a sum of failure deadlines."""
    total=0.
    for move in moves:
        if move['follow']=='release':total+=RELEASE_DISTANCE/RELEASE_SPEED+.014/.005+.5
        elif move['label'].startswith('coat_shot'):total+=max(1.,MEASURED_DWELL)
        else:total+=move['seconds']
    return total


def press_contact_state(sample,point):
    """Read native contact and actual support geometry; no synthetic forces."""
    try:
        matrix=np.asarray(sample['right_contact_matrix'],dtype=float)
        hand=sample['hands'][1];tcp=np.asarray(hand['tcp'],dtype=float);rotation=np.asarray(hand['rotation'],dtype=float)
        canR=np.asarray(sample['can_rotation'],dtype=float);button=np.asarray(sample['button'],dtype=float)
        finger=float(hand['finger_joints'][0]);travel=float(sample['button_travel'])
        if matrix.ndim!=3 or matrix.shape[0]==0 or matrix.shape[1:]!=(5,3):raise ValueError('invalid native contact matrix shape')
        if tcp.shape!=(3,) or button.shape!=(3,) or rotation.shape!=(3,3) or canR.shape!=(3,3):raise ValueError('invalid measured contact geometry shape')
        if not all(np.isfinite(v).all() for v in (matrix,tcp,rotation,canR,button,finger,travel)):raise ValueError('nonfinite contact state')
    except (KeyError,IndexError,TypeError,ValueError) as error:
        raise ValueError('missing or invalid native press contact state: '+str(error)) from error
    button_force=float(np.linalg.norm(matrix[:,1],axis=-1).sum())
    unexpected=float(np.linalg.norm(matrix[:,[0,2,3,4]],axis=-1).sum())
    support=np.asarray(point,dtype=float).copy();support[0]+=finger+.028
    local=canR.T@(tcp+rotation@support-button)
    radius=float(np.linalg.norm(local[:2]))
    if button_force>=8.:raise ValueError('native button contact reached 8 N pressure guard')
    if unexpected>1.:raise ValueError('unexpected can/interarm contact exceeded 1 N pressure guard')
    return dict(button_force_N=button_force,unexpected_force_N=unexpected,witness_radius_m=radius,travel_m=travel,
                extra_pressure_allowed=bool(button_force>.1 and radius<=.0075 and travel<.0027))


def press_bias_step(bias,error,dt,contact):
    """Extend only negative press Z; limit extra loading and allow unwind."""
    bias=np.asarray(bias,dtype=float);error=np.asarray(error,dtype=float)
    if bias.shape!=(3,) or error.shape!=(3,) or not np.isfinite([bias,error]).all() or not math.isfinite(dt) or not 0<=dt<=.1:
        raise ValueError('invalid measured pressure feedback state/timestep')
    if np.any(np.abs(bias[:2])>.020) or not -.030<=bias[2]<=.020:
        raise ValueError('pressure feedback bias exceeds its existing bounds')
    proposed=np.clip(bias+.08*error,[-.020,-.020,-.030],[.020,.020,.020])
    if contact['travel_m']>=.0027:proposed[2]=max(proposed[2],bias[2])
    if proposed[2]<-.020:
        floor=min(bias[2],-.020)
        if contact['extra_pressure_allowed']:floor-=.005*dt
        proposed[2]=max(proposed[2],floor)
    return proposed


def release_command_target(start,goal,elapsed):
    """Linear command-space retreat, including inherited load deflection."""
    start=np.asarray(start,dtype=float);goal=np.asarray(goal,dtype=float)
    if start.shape!=(3,) or goal.shape!=(3,) or not np.isfinite([start,goal]).all() or not math.isfinite(elapsed):
        raise ValueError('release command path requires finite three-component positions and time')
    distance=float(np.linalg.norm(goal-start));duration=distance/RELEASE_SPEED
    fraction=min(1.,max(0.,elapsed)/duration) if duration>0 else 1.
    return start+fraction*(goal-start),fraction,duration


def calibrated_hand_target(nominal,actual_offset):
    """Replace the common nominal grasp offset with its measured value."""
    return np.asarray(nominal)+np.asarray(actual_offset)-GRASP_OFFSET


def grasp_drift(can,can_rotation,hand,hand_rotation,offset,relative_rotation):
    """Measured can-to-hand drift; return None only inside the safety bounds."""
    values=[np.asarray(v,dtype=float) for v in (can,can_rotation,hand,hand_rotation,offset,relative_rotation)]
    if not all(np.isfinite(v).all() for v in values):return 'nonfinite calibrated grasp state'
    can,rotation,hand,handR,offset,relativeR=values
    if rotation[2,2]<math.cos(math.radians(25)):return 'can tilted beyond 25 degrees'
    if np.linalg.norm(rotation.T@(hand-can)-offset)>.008:return 'can grasp offset drift exceeded 8 mm'
    error=relativeR.T@(rotation.T@handR)
    angle=math.acos(float(np.clip((np.trace(error)-1)/2,-1.,1.)))
    if angle>math.radians(15):return 'can grasp relative angle exceeded 15 degrees'
    return None


def release_target(start,rotation,axis,elapsed):
    """Retract from the achieved pose along one latched unit axis."""
    axis=np.asarray(axis,dtype=float)
    if not np.isfinite(axis).all() or abs(np.linalg.norm(axis)-1)>.001 or not math.isfinite(elapsed):
        raise ValueError('release requires finite elapsed time and a latched unit axis')
    distance=min(RELEASE_DISTANCE,max(0.,elapsed)*RELEASE_SPEED)
    return np.asarray(start)+distance*axis,np.asarray(rotation).copy()


def release_clearance(tcp,rotation,face,finger,button,can_axis,axis):
    """Minimum physical pressing-face clearance from the current button top."""
    vertices=np.asarray(face).copy();vertices[:,0]+=finger+.028
    world=vertices@np.asarray(rotation).T+tcp
    top=np.asarray(button)+.005*np.asarray(can_axis)
    return float(((world-top)@np.asarray(axis)).min())


def release_gate_frames(button_travel,clearance,previous):
    if not math.isfinite(button_travel) or not math.isfinite(clearance):return 0
    return previous+1 if button_travel<.0005 and clearance>=.020 else 0


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


def can_frame_ramp_translation(current,target,previous_pose,current_pose,speed,dt):
    """Carry an unbiased reference with measured can motion, then limit relative travel."""
    current=np.asarray(current,dtype=float);target=np.asarray(target,dtype=float)
    center,rotation=(np.asarray(v,dtype=float) for v in current_pose)
    if current.shape!=(3,) or target.shape!=(3,) or center.shape!=(3,) or rotation.shape!=(3,3) or not all(np.isfinite(v).all() for v in (current,target,center,rotation)):
        raise ValueError('can following requires finite positions and rotations')
    carried=current.copy()
    if previous_pose is not None:
        previous_center,previous_rotation=(np.asarray(v,dtype=float) for v in previous_pose)
        if previous_center.shape!=(3,) or previous_rotation.shape!=(3,3) or not all(np.isfinite(v).all() for v in (previous_center,previous_rotation)):
            raise ValueError('can following requires finite previous pose')
        carried=center+rotation@previous_rotation.T@(current-previous_center)
    return ramp_translation(carried,target,speed,dt)


def transport_can_reference(position,rotation,entry_pose,current_pose):
    """Express an entry-world reference after the measured can's rigid motion."""
    position=np.asarray(position,dtype=float);rotation=np.asarray(rotation,dtype=float)
    center0,canR0=(np.asarray(v,dtype=float) for v in entry_pose)
    center,canR=(np.asarray(v,dtype=float) for v in current_pose)
    if position.shape!=(3,) or rotation.shape!=(3,3) or center0.shape!=(3,) or center.shape!=(3,) or canR0.shape!=(3,3) or canR.shape!=(3,3) or not all(np.isfinite(v).all() for v in (position,rotation,center0,center,canR0,canR)):
        raise ValueError('release transport requires finite poses')
    turn=canR@canR0.T
    return center+turn@(position-center0),turn@rotation


def actual_face_tcp_target(can,can_rotation,height,actual_hand_rotation,point):
    """TCP translation making its error equal the selected physical point's error."""
    can=np.asarray(can,dtype=float);can_rotation=np.asarray(can_rotation,dtype=float)
    actual_hand_rotation=np.asarray(actual_hand_rotation,dtype=float);point=np.asarray(point,dtype=float)
    if can.shape!=(3,) or point.shape!=(3,) or can_rotation.shape!=(3,3) or actual_hand_rotation.shape!=(3,3) or not all(np.isfinite(v).all() for v in (can,can_rotation,actual_hand_rotation,point)) or not math.isfinite(height):
        raise ValueError('selected face target requires finite geometry')
    return can+can_rotation@np.array((0.,0.,height))-actual_hand_rotation@point
