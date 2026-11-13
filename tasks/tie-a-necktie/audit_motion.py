"""Offline collision-hull rejection check for the frozen tie contact probe.

Checks sampled commanded poses against all fixed solids and the opposite arm.
Passing does not prove continuous collision freedom, tracking or cloth grasping.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def audit(plan):
    from yam_arena import station
    from yam_arena.analysis import link_hulls,fk_link_poses_world,box_signed_distance
    from yam_arena.constants import ARM_JOINTS,FINGER_OPEN
    from layout import fixture_geometry,TABLE
    hulls=link_hulls();fixtures=fixture_geometry()
    fixtures['Table']=dict(kind='box',center=(.36,0.,TABLE-.03),size=(1.1,1.3,.06))
    cache={};violations=[];closest={};inter_arm_min=float('inf')
    def world_hulls(action,side):
        key=side,tuple(action)
        if key in cache:return cache[key]
        joints=dict(zip(ARM_JOINTS,action[:6]));joints.update(joint7=action[6]*FINGER_OPEN,joint8=action[6]*FINGER_OPEN)
        poses=fk_link_poses_world(joints,station.BASES[side]);values=[]
        for link,parts in hulls.items():
            r=poses[link][:3,:3];p=poses[link][:3,3]
            for hull in parts:
                w=hull.vertices@r.T+p
                values.append((link,hull,r,p,w,w.min(0),w.max(0)))
        cache[key]=values
        return values
    for step,frame in enumerate(plan['frames']):
        groups=[]
        for a,side in enumerate(('left','right')):
            group=world_hulls(frame['action14'][7*a:7*(a+1)],side);groups.append(group)
            for link,hull,r,p,w,low,high in group:
                if link=='base':continue
                for name,solid in fixtures.items():
                    center=np.array(solid['center'])
                    if solid['kind']=='box':
                        d=box_signed_distance(w,center,np.eye(3),np.array(solid['size']))
                    else:
                        v=w-center
                        q=np.column_stack((np.linalg.norm(v[:,:2],axis=1)-solid['radius'],
                                           abs(v[:,2])-solid['height']/2))
                        d=np.linalg.norm(np.maximum(q,0.),axis=1)+np.minimum(np.maximum(q[:,0],q[:,1]),0.)
                    distance=float(d.min());key=f'{side}:{link}:{name}'
                    closest[key]=min(closest.get(key,float('inf')),distance)
                    if distance<-.0005:
                        violations.append(dict(step=step,stage=frame['stage'],side=side,
                                               link=link,fixture=name,penetration_m=-distance))
        low_a=np.asarray([a[5] for a in groups[0]]);high_a=np.asarray([a[6] for a in groups[0]])
        low_b=np.asarray([b[5] for b in groups[1]]);high_b=np.asarray([b[6] for b in groups[1]])
        pairs=np.argwhere(np.all(np.maximum(low_b[None,:,:]-high_a[:,None,:],low_a[:,None,:]-high_b[None,:,:])<=0.,axis=2))
        for ai,bi in pairs:
                a,b=groups[0][ai],groups[1][bi]
                def inside(source,target):
                    local=(source[4]-target[3])@target[2];planes=target[1].planes
                    return float((local@planes[:,:3].T-planes[:,3]).max(1).min())
                distance=min(inside(a,b),inside(b,a));inter_arm_min=min(inter_arm_min,distance)
                if distance<-.0005:
                    violations.append(dict(step=step,stage=frame['stage'],side='bimanual',
                                           link_pair=[a[0],b[0]],fixture=None,penetration_m=-distance))
    return dict(kind='offline_kinematic_collision_rejection_check',checked_frames=len(plan['frames']),
                passed_rejection_check=not violations,violations=violations,
                min_inter_arm_signed_vertex_distance_m=None if np.isinf(inter_arm_min) else inter_arm_min,
                minimum_signed_vertex_distances_m=closest,tolerance_m=.0005,
                limitation='Sampled collision hull vertices only; no continuous collision, robot tracking or cloth contact claim')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('plan',type=Path);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    from fixed_motion import load
    plan,_=load(args.plan);result=audit(plan)
    result['motion_sha256']=hashlib.sha256(args.plan.read_bytes()).hexdigest()
    result['fixture_source_sha256']=hashlib.sha256(Path(__file__).with_name('layout.py').read_bytes()).hexdigest()
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed_rejection_check'],penetrating_samples=len(result['violations']),
                         max_penetration_m=max((v['penetration_m'] for v in result['violations']),default=0.)),indent=2))
    if result['violations']:raise SystemExit(1)
