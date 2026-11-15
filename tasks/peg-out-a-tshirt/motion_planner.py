"""Ordinary bounded Cartesian/joint motion compiler for the laundry demo."""
import json
import numpy as np

def compile_motion(start_action,schedule,*,robust_joint=False):
    from yam_arena import ik,station
    from yam_arena.constants import SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    q={s:np.asarray(start_action,float)[7*i:7*i+6].copy() for i,s in enumerate(('left','right'))}
    opening={s:float(start_action[7*i+6]) for i,s in enumerate(('left','right'))};frames=[];audits=[]
    for seconds,side,position,grip,rotation,label,mode in schedule:
        position=np.asarray(position);p0,r0=ik.tcp_pose(q[side],station.BASES[side]);q0=q[side].copy();o0=opening[side];pe_max=re_max=0.;goal=None
        if mode=='joint':
            goal,pe,re=ik.solve(position,ik.matrix_to_quat_xyzw(rotation),q0,base_pos=station.BASES[side],iters=600)
            if robust_joint and (pe>.004 or re>.04):
                from scipy.optimize import least_squares
                def residual(candidate):
                    p,r=ik.tcp_pose(candidate,station.BASES[side])
                    return np.r_[p-position,.3*ik._rot_error(rotation,r)]
                offset=0 if side=='left' else 7
                seeds=(q0,np.asarray(start_action)[offset:offset+6],(ik.LOWER+ik.UPPER)/2)
                solutions=[least_squares(residual,np.clip(seed,ik.LOWER,ik.UPPER),
                    bounds=(ik.LOWER,ik.UPPER),max_nfev=200,ftol=1e-10,xtol=1e-10,gtol=1e-10)
                    for seed in seeds]
                result=min(solutions,key=lambda s:np.linalg.norm(s.fun))
                goal=result.x;pe=float(np.linalg.norm(result.fun[:3]));re=float(np.linalg.norm(result.fun[3:])/.3)
            if pe>.004 or re>.04:raise ValueError(f'Measured receiving approach is unreachable: {label}; position={pe:.6g}m rotation={re:.6g}rad')
        for k in range(1,round(seconds*20)+1):
            t=ik.smoothstep(k/(seconds*20))
            if goal is not None:q[side]=q0+t*(goal-q0);pe=re=0.
            else:q[side],pe,re=ik.solve(p0+t*(position-p0),ik.matrix_to_quat_xyzw(ik.slerp_matrix(r0,rotation,t)),q[side],base_pos=station.BASES[side],iters=120)
            pe_max=max(pe_max,float(pe));re_max=max(re_max,float(re));opening[side]=o0+t*(grip-o0)
            frames.append(dict(action14=np.r_[q['left'],opening['left'],q['right'],opening['right']].tolist(),stage=label))
        audits.append(dict(stage=label,max_position_error_m=pe_max,max_rotation_error_rad=re_max))
    if any(a['max_position_error_m']>.004 or a['max_rotation_error_rad']>.04 for a in audits):raise ValueError('Measured handoff IK gate failed: '+json.dumps([a for a in audits if a['max_position_error_m']>.004 or a['max_rotation_error_rad']>.04]))
    actions=np.asarray([start_action]+[f['action14'] for f in frames]);limits=np.tile([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20],2)
    if np.any(abs(np.diff(actions,axis=0))>limits*1.001):raise ValueError('Handoff exceeds normal action speeds')
    return dict(schema='cloth-fixed-motion-fragment-v1',frames=frames,action_count=len(frames),kinematic_audit=audits,feedback='Explicit native-state scripted planning of ordinary robot actions only',score=None)

