"""Compile ordinary robot actions from the measured cloth at stage boundaries.

The prefix uses the same joint/finger commands as the saved demo segments.
It cannot change cloth, fixtures, physics, or scores. Stop before release and fit.
"""
import numpy as np
from adult_handoff import receive_tip, _compile
from knot_demo import compile_segment
from cross_motion import yaw_rotation

STAGES = {281: 'handoff', 581: 'wrap', 1121: 'neck', 1481: 'front',
          1841: 'cinch'}

def compile_stage(stage, start, rest, nodes):
    if stage=='handoff':
     plan=receive_tip(start,rest,nodes,clear_alignment=(.12,-.04,1.02),receiving_yaw=210.)
    elif stage in ('wrap','cinch','release_tip','fit'):
     plan=compile_segment(stage,start,rest,nodes)
    elif stage=='neck':
     route=[(3.,(.25,.14,1.13)),(3.,(.35,.08,1.10)),(3.,(.35,0.,1.13)),(4.,(.35,0.,1.17)),(3.,(.25,0.,1.20)),(2.,(.25,0.,1.20))]
     plan=_compile(start,[(sec,'left',xyz,0.,yaw_rotation(90.),'carry wide tip through neck loop','cartesian') for sec,xyz in route],robust_joint=True)
    elif stage=='tip_regrasp':
     from yam_arena import ik,station
     lp,lR=ik.tcp_pose(start[:6],station.BASES['left'])
     t=lp-.012*lR[:,2]-.002*lR[:,0]
     plan=_compile(start,[(1.,'left',lp,1.,lR,'open to take a shallower knot-body pinch','cartesian'),(1.,'left',t,1.,lR,'place knot fabric nearer the fingertips','cartesian'),(1.,'left',t,0.,lR,'close on the outer knot fold','cartesian'),(1.,'left',t,0.,lR,'retain outer knot fold','cartesian')],robust_joint=True)
    elif stage=='regrasp_knot':
     from yam_arena import ik,station
     from adult_motion import grasp_frame
     lp,lR=ik.tcp_pose(start[:6],station.BASES['left'])
     g=grasp_frame(rest,nodes,longitudinal=.45,side='left');R=np.asarray(g['rotation'])@np.diag((1.,-1.,-1.))
     t=np.asarray(g['center_m'])+.012*R[:,2];pre=t-.065*R[:,2]
     plan=_compile(start,[(1.,'left',lp,1.,lR,'open after missed knot-body grasp','cartesian'),(2.,'left',pre,1.,R,'align with measured knot fabric plane','joint'),(2.,'left',t,1.,R,'enclose actual knot fabric','cartesian'),(1.,'left',t,0.,R,'pinch knot body in measured plane','cartesian'),(1.,'left',t,0.,R,'check retained knot body','cartesian')],robust_joint=True)
     plan['grasp']=g
    elif stage=='finish_fit':
     from yam_arena import ik,station
     rp,rR=ik.tcp_pose(start[7:13],station.BASES['right'])
     target=np.array((.31,0.,1.175));Rfit=yaw_rotation(90.)
     rightdown=rR@np.array([[1.,0.,0.],[0.,0.,1.],[0.,-1.,0.]])
     ready,Rready=ik.tcp_pose(np.array([0.,1.,1.,-.6,0.,0.]),station.BASES['right'])
     plan=_compile(start,[(5.,'left',target,0.,Rfit,'slide knot toward collar','cartesian'),(2.,'left',target,0.,Rfit,'settle collar fit','cartesian'),(1.,'left',target,1.,Rfit,'release knot body','cartesian'),(2.,'left',target-.12*Rfit[:,2],1.,Rfit,'withdraw from knot body','cartesian'),(2.,'right',rp,0.,rightdown,'turn narrow-tip fingers downward','cartesian'),(1.,'right',rp,1.,rightdown,'release narrow end','cartesian'),(2.,'right',rp,1.,rightdown,'allow narrow end to fall','cartesian'),(3.,'right',ready,1.,Rready,'clear right hand','joint'),(5.,'right',ready,1.,Rready,'observe released knot','cartesian')],robust_joint=True)
    elif stage=='clear_left':
     from yam_arena import ik,station
     lp,lR=ik.tcp_pose(start[:6],station.BASES['left'])
     ready,Rready=ik.tcp_pose(np.array([0.,1.,1.,-.6,0.,0.]),station.BASES['left'])
     plan=_compile(start,[(3.,'left',lp+np.array((-.10,0.,0.)),1.,lR,'clear open fingers sideways from wide blade','cartesian'),(3.,'left',ready,1.,Rready,'return empty left hand to ready','joint'),(2.,'left',ready,1.,Rready,'observe freely hanging wide blade','cartesian')],robust_joint=True)
    elif stage=='front':
     from yam_arena import ik,station
     rp,rR=ik.tcp_pose(start[7:13],station.BASES['right'])
     plan=_compile(start,[(3.,'left',(.31,.015,1.08),0.,yaw_rotation(90.),'align wide tip over front loop','cartesian'),(2.,'left',(.31,.015,1.045),0.,yaw_rotation(90.),'enter front loop','cartesian'),(1.,'right',rp,1.,rR,'release narrow strip','cartesian'),(3.,'right',(.25,-.20,1.08),1.,yaw_rotation(30.),'withdraw from free narrow strip','joint'),(4.,'left',(.31,.015,.96),0.,yaw_rotation(90.),'pass wide tip down through front loop','cartesian'),(3.,'left',(.22,.015,.90),0.,yaw_rotation(90.),'draw wide tip through','cartesian'),(2.,'left',(.22,.015,.90),0.,yaw_rotation(90.),'hold threaded strip','cartesian')],robust_joint=True)
    else:raise ValueError(stage)
    return plan


def prefix_payload(step, start, rest, nodes, left_grip_count):
    if step not in STAGES:
        return None
    if step>281 and left_grip_count<3:
        raise RuntimeError('Wide-tip grip is missing; pause for an ordinary correction')
    plan = compile_stage(STAGES[step], start, rest, nodes)
    frames = plan['frames'][:140] if step == 2501 else plan['frames']
    return dict(schema='ordinary-demo-actions-v1', start_step=step,
                final=False, frames=frames)
