"""Load a frozen diagnostic joint trajectory. No object-state policy feedback.

The 14-D actions are normal YAM joint and finger commands. A file passing this
check says nothing about physical cloth contact, knot topology or task success.
The runner separately checks the ordinary adapter limits and command speeds.
"""
import json
from pathlib import Path
import numpy as np


def load(path):
    data=json.loads(Path(path).read_text())
    if data.get('schema')!='cloth-fixed-motion-v1' or data.get('control_hz')!=20:
        raise ValueError('Unexpected motion schema or rate')
    frames=data.get('frames',[])
    actions=np.asarray([f['action14'] for f in frames],dtype=float)
    if actions.ndim!=2 or actions.shape[1]!=14 or not 1<=len(actions)<=3600 or not np.isfinite(actions).all():
        raise ValueError('A motion probe needs 1–3600 finite 14-D joint commands')
    if np.any(actions[:,[6,13]]<0.) or np.any(actions[:,[6,13]]>1.):
        raise ValueError('Grippers must be normalized to [0,1]')
    return data,actions


def compile_contact():
    """Offline wide-strand pinch/lift/release; no object-state runtime input."""
    from yam_arena import ik,station
    from yam_arena.constants import READY,FINGER_OPEN,SHOULDER,WRIST,GRIPPER
    angle=np.deg2rad(30.)
    rotation=np.array([[np.cos(angle),0.,np.sin(angle)],[-np.sin(angle),0.,np.cos(angle)],[0.,-1.,0.]])
    schedule=[
        (3.,(.382,-.189,.886),.6,'joint approach outside wide strand'),
        (2.,(.432,-.102,.886),.6,'approach hanging wide strand from side'),
        (1.,(.432,-.102,.886),0.,'pinch wide strand'),
        (2.,(.330,-.160,.900),0.,'draw held strand clear of collar'),
        (2.,(.300,-.160,1.080),0.,'lift held strand'),
        (2.,(.300,-.160,1.080),0.,'hold contact diagnostic'),
        (2.,(.300,-.160,1.080),1.,'release cloth'),
        (2.,(.260,-.200,1.080),1.,'withdraw empty gripper'),
    ]
    q=np.array(READY,dtype=float);opening=1.;frames=[];audits=[]
    for index,(seconds,position,target_opening,label) in enumerate(schedule):
        p0,r0=ik.tcp_pose(q,station.BASES['right']);q0=q.copy();o0=opening
        maxpe=maxre=0.;goal=None
        if index==0:
            goal,pe,re=ik.solve(position,ik.matrix_to_quat_xyzw(rotation),q,
                               base_pos=station.BASES['right'],iters=400)
            if pe>.004 or re>.04:raise ValueError('Initial contact waypoint unreachable')
        for step in range(1,round(seconds*20)+1):
            t=ik.smoothstep(step/(seconds*20))
            if goal is not None:q=q0+t*(goal-q0);pe=re=0.
            else:
                target=p0+t*(np.asarray(position)-p0);rot=ik.slerp_matrix(r0,rotation,t)
                q,pe,re=ik.solve(target,ik.matrix_to_quat_xyzw(rot),q,
                                base_pos=station.BASES['right'],iters=60)
            maxpe=max(maxpe,float(pe));maxre=max(maxre,float(re))
            opening=o0+t*(target_opening-o0)
            frames.append(dict(action14=np.r_[READY,1.,q,opening].tolist(),stage=label))
        audits.append(dict(stage=label,target_xyz_m=list(position),seconds=seconds,
                           max_position_error_m=maxpe,max_rotation_error_rad=maxre))
    a=np.array([np.r_[READY,1.,READY,1.]]+[f['action14'] for f in frames])
    limit=np.tile(np.array([SHOULDER['velocity']/20]*3+[WRIST['velocity']/20]*3+
                          [GRIPPER['velocity']/abs(FINGER_OPEN)/20]),2)
    if np.any(np.abs(np.diff(a,axis=0))>limit*1.001):raise ValueError('Normal joint speed exceeded')
    if max(x['max_position_error_m'] for x in audits)>.004 or max(x['max_rotation_error_rad'] for x in audits)>.04:
        raise ValueError('Failed 4 mm / 2.3 degree IK gate')
    import hashlib
    return dict(schema='cloth-fixed-motion-v1',kind='diagnostic_not_submission_demo',
                control_hz=20,score=None,feedback='none; frozen ordinary joint commands only',
                action_count=len(frames),frames=frames,kinematic_audit=audits,
                fixture_source_sha256=hashlib.sha256(Path(__file__).with_name('layout.py').read_bytes()).hexdigest(),
                waypoint_evidence='Offline batch013 YAM five-second reset, wide strand s=0.30 m; no online node feedback')


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();plan=compile_contact();args.out.write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(dict(actions=plan['action_count'],seconds=plan['action_count']/20,
        max_position_error_m=max(x['max_position_error_m'] for x in plan['kinematic_audit']),
        max_rotation_error_rad=max(x['max_rotation_error_rad'] for x in plan['kinematic_audit'])),indent=2))
