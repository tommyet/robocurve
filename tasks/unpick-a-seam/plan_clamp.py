"""Frozen seam-ripper pickup and one-tack feed at the sewing clamp.

Only declared fixture geometry, URDF kinematics and the fixed 029 grasp
calibration enter the plan. No live cloth/tool feedback or target attachments.
This is an unrun diagnostic, not evidence of released stitches or a task score.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from geometry import TABLE_TOP
from tool_geometry import BLADE_OFFSET,GUARDS
from clamp_layout import ROTATION,transform
from plan import DOWN,rx,rz
from plan_cut import GRASP_OFFSET

HERE=Path(__file__).resolve().parent


def compile_plan(pickup):
    from yam_arena import ik,station
    from yam_arena.constants import FINGER_OPEN,READY,SHOULDER,WRIST,GRIPPER
    if pickup.get('control_hz')!=20 or pickup.get('no_object_feedback') is not True:
        raise ValueError('Expected the frozen tool pickup plan')
    # Native 029 demonstrated exactly this seven-second pickup and held grasp.
    frames=[dict(row) for row in pickup['frames'][:140]]
    state={side:{'q':np.asarray(frames[-1]['action14'][offset:offset+6]),
                 'finger':frames[-1]['action14'][offset+6]*FINGER_OPEN}
           for side,offset in (('left',0),('right',7))}
    position_error=rotation_error=0.
    def transition(seconds,label,goals):
        nonlocal position_error,rotation_error
        starts={side:(*ik.tcp_pose(s['q'],station.BASES[side]),s['finger']) for side,s in state.items()}
        count=round(seconds*20)
        for step in range(1,count+1):
            w=ik.smoothstep(step/count);action=[]
            for side,s in state.items():
                p0,r0,f0=starts[side];p1,r1,f1=goals.get(side,(p0,r0,f0))
                p=p0+(np.asarray(p1)-p0)*w;r=ik.slerp_matrix(r0,np.asarray(r1),w)
                q,pe,re=ik.solve(p,ik.matrix_to_quat_xyzw(r),s['q'],station.BASES[side],iters=200,tol=1e-6)
                if pe>.001 or re>np.deg2rad(.5):raise RuntimeError(f'Unreachable {label}: {side} {pe}, {re}')
                position_error=max(position_error,pe);rotation_error=max(rotation_error,re)
                s['q']=q;s['finger']=f0+(f1-f0)*w
                action.extend([*q.tolist(),float(np.clip(s['finger']/FINGER_OPEN,0.,1.))])
            frames.append({'phase':label,'action14':action})
    # Feed toward -Y, with the long point pitched two degrees toward the fabric.
    # This orientation is reachable within the right wrist's ordinary limits.
    flat_turn=rx(-np.deg2rad(2.))@rz(np.pi/2)
    tool_rotation=ROTATION@flat_turn
    def tcp(edge):return edge-tool_rotation@np.asarray(BLADE_OFFSET)+tool_rotation@GRASP_OFFSET
    # Gain vertical clearance before rotating; stay well in front of the cloth.
    position,orientation=ik.tcp_pose(state['right']['q'],station.BASES['right'])
    transition(1.,'raise ripper before turning',{'right':(position+[0.,0.,.04],orientation,-.0055)})
    blade=np.array((.276,.046,float(transform([[.300,0.,TABLE_TOP+.004]])[0,2])+.04))
    transition(2.,'orient ripper clear of clamped seam',{'right':(tcp(blade),tool_rotation@DOWN,-.0055)})
    blade[2]-=.04
    transition(1.,'approach first tack clear of fabric',{'right':(tcp(blade),tool_rotation@DOWN,-.0055)})
    guard_low=min((flat_turn@np.array((x-BLADE_OFFSET[0],0.,z)))[2]-radius
                  for start,length,z,radius in GUARDS for x in (start,start+length))
    # Upper fabric centre is at original Z=table+4 mm, thickness 0.4 mm.
    # Keep the long point at least 0.3 mm above that physical surface at entry.
    flat_blade_height=TABLE_TOP+.004+.0002+.0003-guard_low
    blade[0]=transform([[.300,0.,flat_blade_height]])[0,0]
    transition(1.,'place leading point before first tack',{'right':(tcp(blade),tool_rotation@DOWN,-.0055)})
    blade[1]=.027
    transition(1.5,'feed blade through first tack',{'right':(tcp(blade),tool_rotation@DOWN,-.0055)})
    transition(.2,'hold blade after feed',{})
    blade[0]-=.030
    transition(1.,'lift ripper away from clamped fabric',{'right':(tcp(blade),tool_rotation@DOWN,-.0055)})
    actions=np.asarray([row['action14'] for row in frames]);ready=np.tile(np.r_[READY,1.],2)
    limits=np.tile([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+
                   [GRIPPER['velocity']/abs(FINGER_OPEN)/20],2)
    ratio=np.abs(np.diff(np.vstack((ready,actions)),axis=0))/limits
    if np.max(ratio)>1.001:raise RuntimeError('Clamped-seam plan exceeds ordinary action rate limits')
    return {'schema':'fixed-joint-plan-v1','status':'unrun first-tack probe; no removal or score claim',
            'control_hz':20,'no_object_feedback':True,'requires_sewing_clamp':True,'requires_passive_clamp':True,
            'requires_junction_audit':True,'frames':frames,
            'maximum_ik_position_error_m':position_error,'maximum_ik_rotation_error_rad':rotation_error,
            'maximum_action_rate_fraction':float(ratio.max()),'grasp_offset_in_tool_frame_m':GRASP_OFFSET.tolist(),
            'calibration_evidence':'evidence/native-controls-029.json','feed_distance_m':.019,
            'entry_guard_to_fabric_clearance_m':.0003,'feed_blade_x_m':float(blade[0]+.030),
            'feed_blade_z_m':float(blade[2]),'approach_pitch_degrees':2.,
            'plan_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'fixture_source_sha256':hashlib.sha256((HERE/'passive_clamp.py').read_bytes()).hexdigest()}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pickup-plan',type=Path,default=HERE/'evidence/pickup-plan.json')
    p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    result=compile_plan(json.loads(args.pickup_plan.read_text()))
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='frames'}))
