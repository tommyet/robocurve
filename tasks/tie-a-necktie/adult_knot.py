"""Unvalidated ordinary-contact continuation after the adult tip handoff.

These planners read recorded cloth geometry and return normal joint actions.
They cannot modify cloth state, attach material or alter physical parameters.
A candidate is not a knot demonstration and must pass the actual-input screens.
"""
import hashlib
import numpy as np
from adult_handoff import _compile


def take_wide_with_right(start_action,rest,nodes,longitudinal=.15,tilt_degrees=0.):
    """Move the right pinch nearer the tip while the left hand holds it.

    The final pose preserves the measured pinch; subsequent narrow-end pickup
    must use a fresh cloth observation after this physical transfer succeeds.
    """
    from adult_motion import grasp_frame
    from cross_motion import yaw_rotation
    from yam_arena import ik,station
    if not .11<=longitudinal<=.20 or abs(tilt_degrees)>20:
        raise ValueError('Near-tip planning choice outside the bounded range')
    grasp=grasp_frame(rest,nodes,longitudinal=longitudinal,side='right')
    angle=np.deg2rad(tilt_degrees)
    turn=np.array([[1.,0.,0.],[0.,np.cos(angle),-np.sin(angle)],[0.,np.sin(angle),np.cos(angle)]])
    R=np.asarray(grasp['rotation'])@turn
    target=np.asarray(grasp['center_m'])+.020*R[:,2]
    if not (.15<target[0]<.45 and -.30<target[1]<.15 and .85<target[2]<1.35):
        raise ValueError('Measured near-tip patch lies outside the planned workspace')
    left_p,left_R=ik.tcp_pose(np.asarray(start_action)[:6],station.BASES['left'])
    schedule=[
        (2.,'right',(.17,-.28,1.28),.6,yaw_rotation(30.),'clear the held wide tip','cartesian'),
        (2.,'right',target-.065*R[:,2],.6,R,'align outside the measured near-tip patch','cartesian'),
        (2.,'right',target,.6,R,'insert right fingers around the wide strip','cartesian'),
        (1.,'right',target,0.,R,'pinch the wide strip near its tip','cartesian'),
        (1.,'left',left_p,1.,left_R,'release the receiving hand','cartesian'),
        (2.,'left',left_p-.07*left_R[:,2],1.,left_R,'withdraw receiving fingers along their entry axis','cartesian'),
        (2.,'right',target,0.,R,'hold the transferred near-tip pinch','cartesian')]
    plan=_compile(start_action,schedule)
    grasp.update(rotation=R.tolist(),target_tcp_m=target.tolist(),approach_tilt_degrees=float(tilt_degrees))
    plan.update(grasp=grasp,approach_steps=120,
        native_nodes_sha256=hashlib.sha256(np.ascontiguousarray(nodes).tobytes()).hexdigest(),
        do_not_run_reason='Requires actual completed handoff, full fixture/inter-arm screen and measured-cloth approach/release screen. No native transfer or knot proof.')
    return plan


def classify_patch_contacts(hits,rest,faces,*,longitudinal,final_insertion_from=80):
    """Only intended fingers may touch the chosen material patch on insertion."""
    rest=np.asarray(rest);faces=np.asarray(faces);blocked=[];intended=[]
    for sample in hits:
        good=[];bad=[]
        for hit in sample['hits']:
            material=rest[faces[np.asarray(hit['faces'],int)],1]
            allowed=(sample['step']>final_insertion_from and hit['link'] in ('tip_left','tip_right')
                and material.min()>=longitudinal-.04 and material.max()<=longitudinal+.04)
            (good if allowed else bad).append(hit)
        if good:intended.append(dict(sample,hits=good))
        if bad:blocked.append(dict(sample,hits=bad))
    return blocked,intended
