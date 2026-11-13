"""Unvalidated lateral hem pickup on the explicitly raised laundry support.

Native reset coordinates select ordinary bounded robot targets. No material,
prop, collision or force writer is used. Actual contact remains unproven.
"""
import copy,hashlib
import numpy as np
from fixed_motion import ROTATIONS


def calibrate(reference,rest,nodes):
    from yam_arena import ik,station
    from yam_arena.constants import READY,SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    rest=np.asarray(rest);nodes=np.asarray(nodes)
    if rest.shape!=nodes.shape or not np.isfinite(nodes).all():raise ValueError('Invalid cloth observation')
    arms={};records=[];patches={}
    for side,hx,sign in [('left',-.12,1.),('right',.12,-1.)]:
        ids=(abs(rest[:,0]-hx)<.011)&(rest[:,1]<.011);front=ids&(rest[:,2]>0)
        uv=rest[front,:2];points=nodes[front]
        fit=np.linalg.lstsq(np.c_[uv-uv.mean(0),np.ones(len(uv))],points-points.mean(0),rcond=None)[0]
        width=fit[0]/np.linalg.norm(fit[0]);normal=np.cross(width,fit[1]);normal/=np.linalg.norm(normal)
        approach=sign*width;closing=sign*normal;R=np.column_stack((closing,np.cross(approach,closing),approach))
        angle=np.deg2rad(-10. if side=='right' else 0.)
        R=R@np.array([[1,0,0],[0,np.cos(angle),-np.sin(angle)],[0,np.sin(angle),np.cos(angle)]])
        center=nodes[ids].mean(0);target=center+.01*R[:,2];pre=target-.06*R[:,2]
        if not (.17<center[0]<.27 and .84<center[2]<.94 and abs(center[1]-sign*.12)<.04):
            raise ValueError('Actual hem is outside the raised-support planning region')
        q=np.array(READY,float);opening=1.;frames=[]
        schedule=[(3.,np.array((.15,sign*.12,1.00)),.2,ROTATIONS[side],'orient above and outside the support','joint'),
            (1.,np.array((.15,pre[1],pre[2])),.2,R,'descend and turn in front of support','cartesian'),
            (1.,pre,.2,R,'align laterally outside hem edge','cartesian'),
            (2.,target,.2,R,'insert along exposed hem edge','cartesian'),
            (1.,target,.018,R,'pinch both cloth layers','cartesian'),
            (1.,np.array((.1494,target[1],target[2])),.018,R,'pull forward clear of support','cartesian'),
            (1.,np.array((.1494,sign*.115,.898 if side=='left' else .902)),.018,ROTATIONS[side],'turn held hem in clear space','cartesian')]
        for seconds,position,grip,rotation,label,mode in schedule:
            q0=q.copy();p0,R0=ik.tcp_pose(q0,station.BASES[side]);opening0=opening;goal=None;em=er=0.
            if mode=='joint':
                goal,pe,re=ik.solve(position,ik.matrix_to_quat_xyzw(rotation),q0,base_pos=station.BASES[side],iters=800)
                if pe>.004 or re>.04:raise ValueError('Raised-support clear approach is unreachable')
            for k in range(1,round(seconds*20)+1):
                t=ik.smoothstep(k/(seconds*20))
                if goal is not None:q=q0+t*(goal-q0);pe=re=0.
                else:q,pe,re=ik.solve(p0+t*(position-p0),ik.matrix_to_quat_xyzw(ik.slerp_matrix(R0,rotation,t)),q,base_pos=station.BASES[side],iters=120)
                em=max(em,float(pe));er=max(er,float(re));opening=opening0+t*(grip-opening0)
                frames.append(dict(action=np.r_[q,opening].tolist(),stage=label))
            records.append(dict(side=side,stage=label,max_position_error_m=em,max_rotation_error_rad=er))
            if em>.004 or er>.04:raise ValueError('Actual lateral-grasp IK is unreachable: '+repr(records[-1]))
        arms[side]=frames;patches[side]=dict(material_node_ids=np.flatnonzero(ids).tolist(),observed_center_m=center.tolist(),target_tcp_m=target.tolist(),rotation=R.tolist(),desired_patch_local_m=[0.,0.,-.010])
    result=copy.deepcopy(reference)
    result['frames'][:200]=[dict(action14=a['action']+b['action'],stage=a['stage']) for a,b in zip(arms['left'],arms['right'])]
    actions=np.array([np.r_[READY,1.,READY,1.]]+[f['action14'] for f in result['frames']])
    limits=np.tile([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20],2)
    if np.any(abs(np.diff(actions,axis=0))>limits*1.001):raise ValueError('Lateral grasp exceeds ordinary action speed')
    result['kinematic_audit']=records
    return result,dict(patches=patches,input_native_nodes_sha256=hashlib.sha256(np.ascontiguousarray(nodes).tobytes()).hexdigest(),state_writes=False,method='Measured lateral hem insertion on the declared180mm support')
