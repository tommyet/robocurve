"""Compile a fixed joint-action plan with pure kinematics, before simulation.

The plan has no object-state input or callback. Development trials can diagnose
slip from their recorded telemetry, but never repair it by moving an object or
altering later actions while an episode is running. This first plan is an
unvalidated pickup/positioning experiment, not a demonstrated piping policy.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

# Gripper X is its closing axis. Barrel lies along Y, so pads close along X.
DOWN=np.array([[1.,0.,0.],[0.,-1.,0.],[0.,0.,-1.]])
# Fixed tool-in-hand calibration from the last 20 frames of native pickup009.
# This is a declared offline calibration, not live task-object feedback. The
# settled barrel varied by <0.05 mm per axis over that one-second interval.
# Initial pickup actions stay unchanged; subsequent goals compensate its
# measured seating offset and 3.2 degree pitch difference.
GRASP_TRANSLATION=np.array((-.001836185,.008420001,.011846225))
GRASP_ROTATION=np.array((
    (-.999929335,-.009796625,.006734309),
    (-.010160689,.998359913,-.056340427),
    (-.006171318,-.056404871,-.998388905)))


def calibrated_hand_pose(barrel_centre,barrel_rotation):
    hand_rotation=np.asarray(barrel_rotation)@GRASP_ROTATION.T
    hand_position=np.asarray(barrel_centre)-hand_rotation@GRASP_TRANSLATION
    return hand_position,hand_rotation


def rx(angle):
    c,s=np.cos(angle),np.sin(angle)
    return np.array([[1.,0.,0.],[0.,c,-s],[0.,s,c]])


def compile_plan(mode='pickup',press_stroke=.006):
    from yam_arena import ik,station
    from yam_arena.constants import READY,FINGER_OPEN
    state={side:{'q':np.asarray(READY,float),'finger':FINGER_OPEN} for side in ('left','right')}
    frames=[];maximum_position_error=maximum_rotation_error=0.

    def transition(seconds,label,goals):
        nonlocal maximum_position_error,maximum_rotation_error
        starts={side:(*ik.tcp_pose(s['q'],station.BASES[side]),s['finger']) for side,s in state.items()}
        steps=round(seconds*20)
        for i in range(1,steps+1):
            weight=ik.smoothstep(i/steps);action=[]
            for side,s in state.items():
                p0,r0,f0=starts[side]
                p1,r1,f1=goals.get(side,(p0,r0,f0))
                p=p0+(np.asarray(p1)-p0)*weight
                r=ik.slerp_matrix(r0,np.asarray(r1),weight)
                q,pe,re=ik.solve(p,ik.matrix_to_quat_xyzw(r),s['q'],station.BASES[side],iters=200,tol=1e-6)
                maximum_position_error=max(maximum_position_error,pe)
                maximum_rotation_error=max(maximum_rotation_error,re)
                if pe>.001 or re>np.deg2rad(.5):
                    raise RuntimeError(f'Unreachable fixed plan: {label}, {side}, {pe*1000:.3f} mm, {np.rad2deg(re):.3f} degrees')
                s['q']=q;s['finger']=f0+(f1-f0)*weight
                action.extend([*q.tolist(),float(np.clip(s['finger']/FINGER_OPEN,0,1))])
            frames.append({'phase':label,'action14':action})

    p=np.array((.18,-.16,.7775))
    transition(2.,'approach dispenser',{'right':(p+[0,0,.10],DOWN,FINGER_OPEN)})
    transition(2.,'lower around barrel',{'right':(p+[0,0,.009],DOWN,FINGER_OPEN)})
    transition(1.,'close on barrel',{'right':(p+[0,0,.009],DOWN,-.0145)})
    transition(2.,'lift dispenser',{'right':(p+[0,0,.10],DOWN,-.0145)})
    # Carry while horizontal, then rotate above the table. The intended nozzle
    # points -Y/down so the right wrist and left pressing hand both stay within
    # their independently checked kinematic workspace.
    tool_rotation=rx(np.pi/4)
    centre=np.array((.235,.102,.865))
    turning_centre=np.array((.235,.040,.865))
    tcp_offset=np.array((0.,0.,.009))
    transition(3.,'carry above cake',{'right':(turning_centre+tcp_offset,DOWN,-.0145)})
    transition(3.,'tilt nozzle downward',{'right':(turning_centre+tool_rotation@tcp_offset,tool_rotation@DOWN,-.0145)})
    transition(2.,'position nozzle above border',{'right':(centre+tool_rotation@tcp_offset,tool_rotation@DOWN,-.0145)})
    transition(2.,'hold for pickup inspection',{})
    if mode in ('press','shell'):
        axis=np.array((0.,-np.sqrt(.5),-np.sqrt(.5)))
        tip=np.array((.235,-.035 if mode=='shell' else -.040,.8065 if mode=='shell' else .8035));centre=tip-axis*.080
        push_rotation=rx(-np.pi/4)@DOWN@np.diag((-1.,-1.,1.))
        # The closed finger tips extend 13 mm beyond TCP. Position them behind
        # the actual 5 mm plunger face; no grasp/latch is added to the pusher.
        contact=centre-axis*(.060+.0025+.013)
        hand_p,hand_r=calibrated_hand_pose(centre,tool_rotation@np.diag((-1.,-1.,1.)))
        transition(3.,'position for first pressure contact',{
            'right':(hand_p,hand_r,-.0145),
            'left':(contact-axis*.04,push_rotation,FINGER_OPEN)})
        if mode=='shell':
            transition(1.,'firm barrel grasp for pressure',{'right':(hand_p,hand_r,-.0105)})
        transition(1.,'close pressing fingers',{'left':(contact-axis*.04,push_rotation,0.)})
        transition(1.,'approach plunger face',{'left':(contact,push_rotation,0.)})
        transition(.5,'press passive plunger',{'left':(contact+axis*press_stroke,push_rotation,0.)})
        transition(.6 if mode=='shell' else .4,'hold first pressure pulse',{})
        if mode=='shell':
            # Both hands translate the real dispenser while pressure is eased.
            # This is one frozen technique trial, not a material shape command.
            tail_delta=np.array((0.,.014,.002))
            transition(.35,'draw first tail under pressure',{
                'right':(hand_p+tail_delta*.5,hand_r,-.0105),
                'left':(contact+tail_delta*.5+axis*press_stroke,push_rotation,0.)})
            transition(.4,'ease pressure into pointed tail',{
                'right':(hand_p+tail_delta,hand_r,-.0105),
                'left':(contact+tail_delta+axis*.008,push_rotation,0.)})
            contact=contact+tail_delta
            hand_p=hand_p+tail_delta
        transition(.5,'release pressure',{'left':(contact-axis*.008,push_rotation,0.)})
        transition(1.,'withdraw pressing hand',{'left':(contact-axis*.04,push_rotation,0.)})
        if mode=='shell':
            transition(1.,'lift nozzle clear',{'right':(hand_p+np.array((0.,0.,.025)),hand_r,-.0105)})
            parked_p,parked_r=calibrated_hand_pose(np.array((.18,-.16,.95)),tool_rotation@np.diag((-1.,-1.,1.)))
            transition(2.,'move clear of judging views',{'right':(parked_p,parked_r,-.0105)})
        transition(1.,'observe deposited material',{})
    return {'schema':'fixed-joint-plan-v1','control_hz':20,'status':'development '+mode+' only',
            'no_object_feedback':True,'frames':frames,
            'offline_grasp_calibration':'Native pickup009 final one-second mean; fixed constants, no trial-state input' if mode in ('press','shell') else None,
            'maximum_ik_position_error_m':maximum_position_error,
            'maximum_ik_rotation_error_rad':maximum_rotation_error,
            'plan_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--mode',choices=('pickup','press','shell'),default='pickup')
    p.add_argument('--press-stroke',type=float,default=.006)
    args=p.parse_args()
    if not .001<=args.press_stroke<=.016:p.error('Pressure diagnostic stroke limited to 1–16 mm')
    plan=compile_plan(args.mode,args.press_stroke)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps({k:v for k,v in plan.items() if k!='frames'}))


if __name__=='__main__':main()
