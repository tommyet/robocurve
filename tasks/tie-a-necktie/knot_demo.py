"""Measured grasps for the scripted necktie demonstration.

This module can only produce ordinary bounded robot targets. It has no scene,
attachment, force or object-state writer. Dream never calls it.
"""
import numpy as np
from adult_handoff import _compile
from adult_motion import grasp_frame
from audit_adult_motion import audit
from cross_motion import yaw_rotation


def compile_segment(stage,start,rest,nodes):
    from yam_arena import ik,station
    lp,lR=ik.tcp_pose(np.asarray(start)[:6],station.BASES['left'])
    rp,rR=ik.tcp_pose(np.asarray(start)[7:13],station.BASES['right'])
    if stage=='wrap':
        g=grasp_frame(rest,nodes,longitudinal=1.30,side='right')
        R=np.asarray(g['rotation'])@np.diag((-1.,-1.,1.))
        t=np.asarray(g['center_m'])+.022*R[:,2];pre=t-.065*R[:,2]
        schedule=[(3.,'left',(.24,.23,1.17),0.,yaw_rotation(150.),'cross wide tip and clear narrow hand','cartesian'),
          (2.,'right',(.20,-.23,.96),1.,yaw_rotation(30.),'approach below wide hand','joint'),
          (3.,'right',pre,1.,R,'align with measured narrow strip','joint'),
          (2.,'right',t,1.,R,'surround narrow strip','cartesian'),
          (1.,'right',t,0.,R,'pinch narrow strip','cartesian'),
          (2.,'right',t,0.,R,'hold narrow strip','cartesian'),
          (3.,'right',(.26,.04,.94),0.,R,'hold narrow strand below knot','cartesian')]
        route=[(2.,(.39,.16,1.14),'round edge to back'),(3.,(.39,-.15,1.14),'cross behind narrow strand'),
               (2.,(.21,-.15,1.14),'round edge to front'),(3.,(.21,.15,1.14),'cross front of narrow strand'),
               (1.,(.21,.15,1.14),'hold wrap')]
        schedule += [(seconds,'left',xyz,0.,yaw_rotation(90.),label,'cartesian') for seconds,xyz,label in route]
    elif stage=='cinch':
        g=grasp_frame(rest,nodes,longitudinal=1.30,side='right');R=yaw_rotation(30.)
        t=np.asarray(g['center_m'])+.020*R[:,2];pre=t-.06*R[:,2]
        schedule=[(3.,'right',pre,1.,R,'approach free narrow end','joint'),
          (2.,'right',t,1.,R,'surround measured narrow material','cartesian'),
          (1.,'right',t,0.,R,'grasp narrow end','cartesian'),(1.,'right',t,0.,R,'retain narrow end','cartesian'),
          (4.,'right',(.29,-.08,.94),0.,yaw_rotation(30.),'tension narrow end below knot','cartesian'),
          (4.,'left',(.24,.035,.85),0.,yaw_rotation(90.),'draw wide end through front loop','cartesian'),
          (2.,'left',(.24,.035,.85),0.,yaw_rotation(90.),'settle tightened knot','cartesian')]
    elif stage=='fit':
        g=grasp_frame(rest,nodes,longitudinal=.45,side='left');R=yaw_rotation(90.)
        t=np.asarray(g['center_m'])+.012*R[:,2];pre=t-.075*R[:,2]
        schedule=[(1.,'left',lp,1.,lR,'release wide tip for adjustment','cartesian'),
          (3.,'left',pre,1.,R,'approach front of knot','joint'),(2.,'left',t,1.,R,'surround knot body','cartesian'),
          (1.,'left',t,0.,R,'hold knot body','cartesian'),(1.,'left',t,0.,R,'retain knot body','cartesian'),
          (5.,'left',(.31,0.,1.175),0.,R,'slide knot toward collar','cartesian'),
          (2.,'left',(.31,0.,1.175),0.,R,'settle collar fit','cartesian'),
          (1.,'left',(.31,0.,1.175),1.,R,'release knot body','cartesian'),
          (2.,'left',(.20,.15,1.15),1.,R,'clear knot with left hand','cartesian'),
          (1.,'right',rp,1.,rR,'release narrow end','cartesian'),
          (2.,'right',(.20,-.20,1.08),1.,yaw_rotation(30.),'clear tie with right hand','cartesian'),
          (5.,'right',(.20,-.20,1.08),1.,yaw_rotation(30.),'observe released knot','cartesian')]
    else:raise ValueError('Unknown knot demonstration stage')
    plan=_compile(start,schedule,robust_joint=True)
    check=audit(dict(plan,frames=plan['frames'][::5]))
    if not check['passed']:raise RuntimeError('Measured '+stage+' route intersects a fixture or the other arm')
    plan.update(grasp=g,rigid_clearance=check,stage=stage)
    return plan
