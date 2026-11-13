"""Unvalidated ordinary-contact continuation after the adult tip handoff.

These planners read recorded cloth geometry and return normal joint actions.
They cannot modify cloth state, attach material or alter physical parameters.
A candidate is not a knot demonstration and must pass the actual-input screens.
"""
import hashlib
import numpy as np
from adult_handoff import _compile


def carry_for_regrasp(start_action):
    from cross_motion import yaw_rotation
    return _compile(start_action,[(3.,'left',(.26,-.14,1.25),0.,yaw_rotation(150.),
        'carry wide tip into reachable regrasp area','cartesian')])


def take_wide_with_right(start_action,rest,nodes,longitudinal=.15,tilt_degrees=0.):
    """Transfer the working wide strip while the left hand holds its tip.

    The final pose preserves the measured pinch; subsequent narrow-end pickup
    must use a fresh cloth observation after this physical transfer succeeds.
    """
    from adult_motion import grasp_frame
    from cross_motion import yaw_rotation
    from yam_arena import ik,station
    if not .11<=longitudinal<=.30 or abs(tilt_degrees)>20:
        raise ValueError('Near-tip planning choice outside the bounded range')
    grasp=grasp_frame(rest,nodes,longitudinal=longitudinal,side='right')
    angle=np.deg2rad(tilt_degrees)
    turn=np.array([[1.,0.,0.],[0.,np.cos(angle),-np.sin(angle)],[0.,np.sin(angle),np.cos(angle)]])
    R=np.asarray(grasp['rotation'])@turn
    # The transferred strip can face either way. Swapping opposed fingers
    # preserves the closing plane while keeping the wrist above the cloth.
    if R[2,1]>0.:
        R=R@np.diag((-1.,-1.,1.))
    target=np.asarray(grasp['center_m'])+.020*R[:,2]
    if not (.15<target[0]<.45 and -.30<target[1]<.15 and .85<target[2]<1.35):
        raise ValueError('Measured near-tip patch lies outside the planned workspace')
    left_p,left_R=ik.tcp_pose(np.asarray(start_action)[:6],station.BASES['left'])
    approach_distance=.025 if longitudinal>=.25 else .065
    schedule=[
        (2.,'right',(.27,-.24,1.20),.6,yaw_rotation(30.),'clear the held wide tip','cartesian'),
        (2.,'right',target-approach_distance*R[:,2],.6,R,'align outside the measured near-tip patch','joint'),
        (2.,'right',target,.6,R,'insert right fingers around the wide strip','cartesian'),
        (1.,'right',target,0.,R,'pinch the wide strip near its tip','cartesian'),
        (1.,'left',left_p,1.,left_R,'release the receiving hand','cartesian'),
        (2.,'left',left_p-.07*left_R[:,2],1.,left_R,'withdraw receiving fingers along their entry axis','cartesian'),
        (2.,'right',target,0.,R,'hold the transferred near-tip pinch','cartesian')]
    plan=_compile(start_action,schedule)
    grasp.update(rotation=R.tolist(),target_tcp_m=target.tolist(),approach_tilt_degrees=float(tilt_degrees),approach_distance_m=approach_distance)
    plan.update(grasp=grasp,approach_steps=120,
        native_nodes_sha256=hashlib.sha256(np.ascontiguousarray(nodes).tobytes()).hexdigest(),
        do_not_run_reason='Requires actual completed handoff, full fixture/inter-arm screen and measured-cloth approach/release screen. No native transfer or knot proof.')
    return plan


def classify_patch_contacts(hits,rest,faces,*,longitudinal,final_insertion_from=80,patch_half_width=.04):
    """Only intended fingers may touch the chosen material patch on insertion."""
    if not .01<=patch_half_width<=.07:raise ValueError('Bounded intended material patch required')
    rest=np.asarray(rest);faces=np.asarray(faces);blocked=[];intended=[]
    for sample in hits:
        good=[];bad=[]
        for hit in sample['hits']:
            material=rest[faces[np.asarray(hit['faces'],int)],1]
            allowed=(sample['step']>final_insertion_from and hit['link'] in ('tip_left','tip_right')
                and material.min()>=longitudinal-patch_half_width and material.max()<=longitudinal+patch_half_width)
            (good if allowed else bad).append(hit)
        if good:intended.append(dict(sample,hits=good))
        if bad:blocked.append(dict(sample,hits=bad))
    return blocked,intended


def take_wide_along_plane(start_action,rest,nodes,*,longitudinal=.20,angle_degrees=-150.,shoulder_arc=.30,flip_fingers=False):
    """Enter along the measured wide strip, below the hand holding its tip.

    The fingers may brush the same continuous strip within65mm of the selected
   20cm material coordinate. This is an approach allowance, not permission for
    native penetration; full contact and retention audits remain required.
    """
    from adult_motion import grasp_frame
    from cross_motion import yaw_rotation
    from yam_arena import ik,station
    from yam_arena.constants import SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    if not .12<=longitudinal<=.30 or not -180.<=angle_degrees<=180. or not 0.<=shoulder_arc<=.6:
        raise ValueError('Measured regrasp candidate outside bounded search')
    grasp=grasp_frame(rest,nodes,longitudinal=longitudinal,side='right')
    angle=np.deg2rad(angle_degrees)
    turn=np.array(((1.,0.,0.),(0.,np.cos(angle),-np.sin(angle)),(0.,np.sin(angle),np.cos(angle))))
    R=np.asarray(grasp['rotation'])@turn
    if flip_fingers:R=R@np.diag((-1.,-1.,1.))
    target=np.asarray(grasp['center_m'])+.012*R[:,2];pre=target-.025*R[:,2]
    left_p,left_R=ik.tcp_pose(np.asarray(start_action)[:6],station.BASES['left'])
    schedule=[(2.,'right',(.23,-.24,1.10),.6,yaw_rotation(30.),'clear the held wide tip','joint'),
        (2.,'right',pre,.6,R,'align with measured wide patch','joint'),
        (2.,'right',target,.6,R,'insert along cloth plane','cartesian'),
        (1.,'right',target,0.,R,'pinch wide patch','cartesian'),
        (1.,'left',left_p,1.,left_R,'release tip','cartesian'),
        (2.,'left',left_p-.07*left_R[:,2],1.,left_R,'withdraw original hand','cartesian'),
        (2.,'right',target,0.,R,'hold wide patch','cartesian')]
    plan=_compile(start_action,schedule,robust_joint=True)
    for i in range(40,80):
        plan['frames'][i]['action14'][8]-=shoulder_arc*np.sin(np.pi*(i-39)/40)**2
    actions=np.asarray([start_action]+[f['action14'] for f in plan['frames']])
    limits=np.tile([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20],2)
    for offset in (0,7):
        if np.any(actions[:,offset:offset+6]<ik.LOWER) or np.any(actions[:,offset:offset+6]>ik.UPPER):
            raise ValueError('In-plane approach exceeds ordinary joint bounds')
    if np.any(abs(np.diff(actions,axis=0))>limits*1.001):raise ValueError('In-plane approach exceeds normal joint speed')
    grasp.update(rotation=R.tolist(),target_tcp_m=target.tolist(),desired_material_tcp_depth_m=-.012,
        inplane_angle_degrees=float(angle_degrees),finger_swap=bool(flip_fingers),intended_material_half_width_m=.065)
    plan.update(grasp=grasp,approach_steps=120,score=None,
        native_nodes_sha256=hashlib.sha256(np.ascontiguousarray(nodes).tobytes()).hexdigest())
    return plan
