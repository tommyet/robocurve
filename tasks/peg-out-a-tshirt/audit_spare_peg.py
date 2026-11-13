"""Reject commanded robot volume intersections with the unused spare peg.

The peg's initial native poses come from a completed diagnostic. This is an
offline planning check, not a proof that the free peg will stay still later.
All convex hulls are tested by halfspace intersection, including crossings
that a contained-vertex test would miss.
"""
import argparse,gzip,hashlib,itertools,json
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
from scipy.spatial import ConvexHull
from interpret_motion import rotation_xyzw


def overlap(a,b):
    planes=np.vstack((a,b))
    r=linprog([0.,0.,0.,-1.],A_ub=np.c_[planes[:,:3],np.ones(len(planes))],
        b_ub=-planes[:,3],bounds=[(None,None)]*3+[(0.,None)],method='highs')
    return float(r.x[3]) if r.success and r.x[3]>.0002 else None


def audit(plan,poses):
    from yam_arena import station
    from yam_arena.analysis import link_hulls,fk_link_poses_world
    from yam_arena.constants import ARM_JOINTS,FINGER_OPEN
    props=[];signs=np.array(list(itertools.product((-1.,1.),repeat=3)))
    for i,pose in enumerate(poses):
        R=rotation_xyzw(pose[3:]);sgn=-1 if i==0 else 1
        for label,center in [('jaw',(.0175,0.,sgn*.0035)),('handle',(-.0175,0.,sgn*.008))]:
            p=(signs*np.array((.035,.010,.006))/2+center)@R.T+pose[:3]
            props.append(dict(name=f'{i}:{label}',low=p.min(0),high=p.max(0),planes=np.unique(np.round(ConvexHull(p).equations,12),axis=0)))
    hulls=link_hulls();hits=[]
    for step,f in enumerate(plan['frames']):
        for hand,side in enumerate(('left','right')):
            a=np.asarray(f['action14'])[hand*7:hand*7+7];q=dict(zip(ARM_JOINTS,a[:6]));q.update(joint7=a[6]*FINGER_OPEN,joint8=a[6]*FINGER_OPEN)
            T=fk_link_poses_world(q,station.BASES[side])
            for link,hs in hulls.items():
                R=T[link][:3,:3];t=T[link][:3,3]
                for h in hs:
                    w=h.vertices@R.T+t;lo=w.min(0);hi=w.max(0)
                    for prop in props:
                        if np.any(np.minimum(hi,prop['high'])-np.maximum(lo,prop['low'])<.0004):continue
                        n=h.planes[:,:3]@R.T;d=overlap(np.c_[n,-h.planes[:,3]-n@t],prop['planes'])
                        if d is not None:hits.append(dict(step=step+1,stage=f['stage'],side=side,link=link,spare_shape=prop['name'],intersection_radius_m=d))
    return dict(kind='offline_unused_peg_convex_volume_rejection',passed=not hits,checked_frames=len(plan['frames']),violations=hits,
        limitation='Static measured spare poses and sampled commanded robot poses; actual dynamics, tracking and continuous collisions remain unverified.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('plan',type=Path);p.add_argument('trial',type=Path);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    with gzip.open(args.trial/'trace.jsonl.gz','rt') as f:row=json.loads(f.readline())
    poses=np.asarray(row['objects']['right_peg']['body_poses']);result=audit(json.loads(args.plan.read_text()),poses)
    result.update(peg_initial_poses_xyzw=poses.tolist(),motion_sha256=hashlib.sha256(args.plan.read_bytes()).hexdigest(),source_trace_sha256=hashlib.sha256((args.trial/'trace.jsonl.gz').read_bytes()).hexdigest())
    args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=result['passed'],intersections=len(result['violations'])),indent=2))
