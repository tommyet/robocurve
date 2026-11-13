"""Cheap offline rejection check for fixed robot trajectories.

Tests actual YAM collision-hull vertices against static fixture solids at every
commanded pose. Any negative distance is a concrete penetration. A clean result
is not a complete continuous collision test, nor evidence of cloth contact or
successful robot control. Native physics and video remain necessary.
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
    from scene import support_geometry,rack_geometry,TABLE
    local_hulls=link_hulls()
    vertices={k:np.concatenate([h.vertices for h in hs])
              for k,hs in local_hulls.items() if k!='base'}
    boxes={**support_geometry(),**rack_geometry()}
    boxes['Table']=dict(kind='box',center=(.36,0.,TABLE-.03),size=(1.1,1.3,.06))
    violations=[]
    closest={}
    inter_arm_min=float('inf')
    for step,f in enumerate(plan['frames']):
        arm_hulls=[]
        for arm,side in enumerate(('left','right')):
            action=f['action14'][7*arm:7*(arm+1)]
            joints=dict(zip(ARM_JOINTS,action[:6]))
            joints.update(joint7=action[6]*FINGER_OPEN,joint8=action[6]*FINGER_OPEN)
            poses=fk_link_poses_world(joints,station.BASES[side])
            hull_group=[]
            for link,hulls in local_hulls.items():
                r=poses[link][:3,:3];p=poses[link][:3,3]
                for h in hulls:
                    w=h.vertices@r.T+p
                    hull_group.append((link,h,r,p,w,w.min(0),w.max(0)))
            arm_hulls.append(hull_group)
            for link,v in vertices.items():
                w=v@poses[link][:3,:3].T+poses[link][:3,3]
                for name,box in boxes.items():
                    if box['kind']=='box':
                        distances=box_signed_distance(w,np.array(box['center']),np.eye(3),np.array(box['size']))
                    else:
                        v=w-np.array(box['center']);axis='XYZ'.index(box.get('axis','Z'))
                        radial=np.linalg.norm(np.delete(v,axis,axis=1),axis=1)-box['radius']
                        axial=abs(v[:,axis])-box['height']/2
                        q=np.column_stack((radial,axial))
                        distances=np.linalg.norm(np.maximum(q,0.),axis=1)+np.minimum(np.maximum(q[:,0],q[:,1]),0.)
                    distance=float(distances.min())
                    key=f'{side}:{link}:{name}'
                    closest[key]=min(closest.get(key,float('inf')),distance)
                    if distance<-.0005:
                        violations.append(dict(step=step,stage=f['stage'],side=side,
                            link=link,box=name,penetration_m=-distance))
        for a in arm_hulls[0]:
            for b in arm_hulls[1]:
                # Disjoint world AABBs cannot contain penetrating vertices.
                if np.any(np.maximum(b[5]-a[6],a[5]-b[6])>0.):
                    continue
                def inside(source,target):
                    local=(source[4]-target[3])@target[2]
                    planes=target[1].planes
                    return float((local@planes[:,:3].T-planes[:,3]).max(1).min())
                distance=min(inside(a,b),inside(b,a))
                inter_arm_min=min(inter_arm_min,distance)
                if distance<-.0005:
                    violations.append(dict(step=step,stage=f['stage'],side='bimanual',
                        link_pair=[a[0],b[0]],box=None,penetration_m=-distance))
    return dict(kind='offline_kinematic_collision_rejection_check',checked_frames=len(plan['frames']),
                min_inter_arm_signed_vertex_distance_m=None if np.isinf(inter_arm_min) else inter_arm_min,
                check='actual collision-hull vertices against fixture boxes and opposite-arm hulls; tolerance 0.5 mm',
                passed_rejection_check=not violations,violations=violations,
                minimum_signed_vertex_distances_m=closest,
                limitation='Does not certify continuous collisions, robot tracking, cloth physics or grasp success')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('plan',type=Path)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    from fixed_motion import load
    plan,_=load(args.plan)
    result=audit(plan)
    result['motion_sha256']=hashlib.sha256(args.plan.read_bytes()).hexdigest()
    result['fixture_source_sha256']=hashlib.sha256(Path(__file__).with_name('scene.py').read_bytes()).hexdigest()
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed_rejection_check'],penetrating_samples=len(result['violations']),
                         max_penetration_m=max((v['penetration_m'] for v in result['violations']),default=0.)),indent=2))
    if result['violations']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
