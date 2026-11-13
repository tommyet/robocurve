"""Exact convex-volume rejection screen for the adult collar robot plan.

Sampled commanded hulls are checked against fixed fixtures and the other arm.
A passing screen does not establish native cloth contact or continuous safety.
"""
import argparse,hashlib,itertools,json
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
from scipy.spatial import ConvexHull


def convex(name,points):
    p=np.asarray(points);return dict(name=name,planes=np.unique(np.round(ConvexHull(p).equations,12),axis=0),low=p.min(0),high=p.max(0))


def candidates(a,b):
    return np.argwhere(np.all(np.minimum(np.array([x['high'] for x in a])[:,None],np.array([x['high'] for x in b])[None])-np.maximum(np.array([x['low'] for x in a])[:,None],np.array([x['low'] for x in b])[None])>=.0004,axis=2))


def overlap(a,b):
    p=np.vstack((a['planes'],b['planes']));r=linprog([0.,0.,0.,-1.],A_ub=np.c_[p[:,:3],np.ones(len(p))],b_ub=-p[:,3],bounds=[(None,None)]*3+[(0.,None)],method='highs')
    return float(r.x[3]) if r.success and r.x[3]>.0002 else None


def audit(plan):
    from yam_arena import station
    from yam_arena.analysis import link_hulls,fk_link_poses_world
    from yam_arena.constants import ARM_JOINTS,FINGER_OPEN
    from adult_layout import fixture_geometry,TABLE
    props=[];fixtures=fixture_geometry();fixtures['Table']=dict(kind='box',center=(.36,0.,TABLE-.03),size=(1.1,1.3,.06))
    for name,s in fixtures.items():
        if s['kind']=='box':p=np.array(list(itertools.product((-1.,1.),repeat=3)))*np.asarray(s['size'])/2
        else:
            angles=np.arange(64)*2*np.pi/64;radius=s['radius']/np.cos(np.pi/64)
            p=np.array([(radius*np.cos(t),radius*np.sin(t),z) for t in angles for z in (-s['height']/2,s['height']/2)])
        props.append(convex(name,p@np.asarray(s.get('rotation',np.eye(3))).T+s['center']))
    hulls=link_hulls();violations=[]
    for step,f in enumerate(plan['frames']):
        robots=[]
        for i,side in enumerate(('left','right')):
            a=np.asarray(f['action14'])[7*i:7*i+7];q=dict(zip(ARM_JOINTS,a[:6]));q.update(joint7=a[6]*FINGER_OPEN,joint8=a[6]*FINGER_OPEN)
            poses=fk_link_poses_world(q,station.BASES[side]);parts=[]
            for name,hs in hulls.items():
                R=poses[name][:3,:3];t=poses[name][:3,3]
                for hi,h in enumerate(hs):
                    w=h.vertices@R.T+t;n=h.planes[:,:3]@R.T
                    parts.append(dict(name=f'{side}/{name}/{hi}',planes=np.c_[n,-h.planes[:,3]-n@t],low=w.min(0),high=w.max(0)))
            robots.append(parts)
        for group_a,group_b in ((robots[0],props),(robots[1],props),(robots[0],robots[1])):
            for ai,bi in candidates(group_a,group_b):
                a,b=group_a[ai],group_b[bi];depth=overlap(a,b)
                if depth is not None:violations.append(dict(step=step+1,stage=f['stage'],a=a['name'],b=b['name'],intersection_radius_m=depth))
    return dict(kind='offline_adult_collar_convex_volume_rejection',passed=not violations,checked_frames=len(plan['frames']),violations=violations,
        limitation='Commanded poses only; no continuous collision, native tracking, material, grasp or knot-success claim.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('plan',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();result=audit(json.loads(a.plan.read_text()));result['motion_sha256']=hashlib.sha256(a.plan.read_bytes()).hexdigest();a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=result['passed'],intersections=len(result['violations'])),indent=2))
