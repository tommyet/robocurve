"""State-assisted ordinary grasp/lift for the adult collar diagnostic.

The measured cloth selects a physical pinch pose. Only bounded joint/gripper
targets are returned; this code has no simulator mutators. It is explicitly a
scripted feasibility controller, never an input to Dream.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np


def grasp_frame(rest,nodes,longitudinal=.45,side='right'):
    rest=np.asarray(rest,float);nodes=np.asarray(nodes,float)
    if rest.shape!=nodes.shape or rest.ndim!=2 or rest.shape[1]!=3 or not np.isfinite(nodes).all():
        raise ValueError('Finite matching cloth coordinates are required')
    levels=np.unique(rest[:,1]);j=int(np.argmin(abs(levels-longitudinal)))
    if j==0 or j==len(levels)-1:raise ValueError('Pinch cannot target a degenerate tip')
    rows=[np.flatnonzero(abs(rest[:,1]-levels[k])<1e-8) for k in (j-1,j,j+1)]
    row=rows[1];width=nodes[row[-1]]-nodes[row[0]];width/=np.linalg.norm(width)
    tangent=nodes[rows[2]].mean(0)-nodes[rows[0]].mean(0);tangent/=np.linalg.norm(tangent)
    normal=np.cross(width,tangent);normal/=np.linalg.norm(normal)
    approach=width*(1. if side=='right' else -1.)
    rotation=np.column_stack((normal,np.cross(approach,normal),approach))
    center=nodes[row].mean(0)
    return dict(material_longitudinal_m=float(levels[j]),node_ids=row.tolist(),center_m=center.tolist(),
        rotation=rotation.tolist(),target_tcp_m=(center+.020*approach).tolist(),desired_material_tcp_depth_m=-.020)


def compile_pickup(rest,nodes):
    from yam_arena import ik,station
    from yam_arena.constants import READY,SHOULDER,WRIST,GRIPPER,FINGER_OPEN
    from cross_motion import yaw_rotation
    grasp=grasp_frame(rest,nodes);R=np.asarray(grasp['rotation']);target=np.asarray(grasp['target_tcp_m'])
    if not (.22<target[0]<.39 and -.22<target[1]<-.05 and .79<target[2]<.93):
        raise ValueError('Measured adult wide-strand pinch is outside planned workspace: '+repr(target.tolist()))
    q=np.asarray(READY,float);opening=1.;frames=[];audits=[]
    schedule=[(3.,target-.06*R[:,2],.6,yaw_rotation(110.),'approach outside measured wide strand','joint'),
              (2.,target,.6,R,'insert fingers around measured wide strand','cartesian'),
              (1.,target,0.,R,'close ordinary fingers on wide strand','cartesian'),
              (3.,(.30,-.16,1.20),0.,yaw_rotation(120.),'lift wide end for tip handoff','cartesian'),
              (1.,(.30,-.16,1.20),0.,yaw_rotation(120.),'hold lifted wide strand','cartesian')]
    for seconds,position,grip,rotation,label,mode in schedule:
        p0,r0=ik.tcp_pose(q,station.BASES['right']);q0=q.copy();o0=opening;pe_max=re_max=0.
        goal=None
        if mode=='joint':
            goal,pe,re=ik.solve(position,ik.matrix_to_quat_xyzw(rotation),q,base_pos=station.BASES['right'],iters=600)
            if pe>.004 or re>.04:raise ValueError('Adult grasp approach is unreachable')
        for k in range(1,round(seconds*20)+1):
            t=ik.smoothstep(k/(seconds*20))
            if goal is not None:q=q0+t*(goal-q0);pe=re=0.
            else:q,pe,re=ik.solve(p0+t*(np.asarray(position)-p0),ik.matrix_to_quat_xyzw(ik.slerp_matrix(r0,rotation,t)),q,base_pos=station.BASES['right'],iters=120)
            pe_max=max(pe_max,float(pe));re_max=max(re_max,float(re));opening=o0+t*(grip-o0)
            frames.append(dict(action14=np.r_[READY,1.,q,opening].tolist(),stage=label))
        audits.append(dict(stage=label,target_xyz_m=list(position),max_position_error_m=pe_max,max_rotation_error_rad=re_max))
    if any(a['max_position_error_m']>.004 or a['max_rotation_error_rad']>.04 for a in audits):raise ValueError('Adult pickup IK gate failed: '+json.dumps(audits))
    actions=np.array([np.r_[READY,1.,READY,1.]]+[f['action14'] for f in frames]);limits=np.tile([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+[GRIPPER['velocity']/abs(FINGER_OPEN)/20],2)
    if np.any(abs(np.diff(actions,axis=0))>limits*1.001):raise ValueError('Ordinary action speed exceeded')
    return dict(schema='cloth-fixed-motion-v1',kind='diagnostic_not_submission_demo',control_hz=20,score=None,
        requires_adult_collar=True,requires_inside_out_reset=True,action_count=len(frames),frames=frames,
        feedback='Explicit scripted reset-state grasp calibration, followed by ordinary joint actions; Dream has no material-state access',
        fixture_source_sha256=hashlib.sha256(Path(__file__).with_name('adult_layout.py').read_bytes()).hexdigest(),
        native_reset_nodes_sha256=hashlib.sha256(np.ascontiguousarray(nodes).tobytes()).hexdigest(),
        grasp=grasp,kinematic_audit=audits,do_not_run_reason='Awaiting full commanded hull clearance and valid native adult reset.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('probe',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    with np.load(a.probe/'nodes.npz',allow_pickle=False) as d:plan=compile_pickup(d['rest'],d['positions'][-1])
    a.out.write_text(json.dumps(plan,indent=2)+'\n');print(json.dumps(dict(actions=plan['action_count'],grasp=plan['grasp'],audit=plan['kinematic_audit']),indent=2))
