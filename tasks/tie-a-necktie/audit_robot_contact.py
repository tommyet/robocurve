"""Offline native cloth triangles against actual robot collision hull poses.

A shrunken hull rejects clear interpenetration while ignoring numerical surface
contact. This does not infer a grasp or supply any online policy feedback.
"""
import argparse,gzip,hashlib,json
from pathlib import Path
import numpy as np
from trace_data import cloth_array
from interpret_motion import rotation_xyzw


def clipped_triangle(tri,planes,shrink):
    poly=tri.copy()
    for plane in planes:
        ds=poly@plane[:3]-plane[3]+shrink
        if np.all(ds>0.):return False
        if np.all(ds<=0.):continue
        result=[]
        for a,b,da,db in zip(poly,np.roll(poly,-1,axis=0),ds,np.roll(ds,-1)):
            ai=da<=0.;bi=db<=0.
            if ai:result.append(a)
            if ai!=bi:result.append(a+(b-a)*da/(da-db))
        if not result:return False
        poly=np.asarray(result)
    return bool(len(poly))


def clipped_triangles(triangles,planes,shrink):
    """Exact scalar clipping with vectorized separating/contained fast paths."""
    triangles=np.asarray(triangles)
    if not len(triangles):return np.zeros(0,dtype=bool)
    distances=triangles@planes[:,:3].T-planes[:,3]+shrink
    separated=(distances>0.).all(axis=1).any(axis=1)
    contained=(distances<=0.).all(axis=2).any(axis=1)
    result=contained&~separated
    for index in np.flatnonzero(~separated&~contained):
        result[index]=clipped_triangle(triangles[index],planes,shrink)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('trial',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--steps',default='240,380,400,440,480,520,560,600,640');p.add_argument('--shrink',type=float,default=.0002)
    args=p.parse_args();wanted={int(x) for x in args.steps.split(',')}
    from yam_arena.analysis import link_hulls
    hulls=link_hulls();meshes=json.loads((args.trial/'meshes.json').read_text());name=next(iter(meshes));faces=np.array(meshes[name]['faces']);samples=[]
    with gzip.open(args.trial/'trace.jsonl.gz','rt') as f:
        for line in f:
            row=json.loads(line)
            if row['step'] not in wanted:continue
            nodes=cloth_array(args.trial,row,name);triangles=nodes[faces];low=triangles.min(1);high=triangles.max(1);hits=[];deepest=0.
            for side in ('left_robot','right_robot'):
                robot=row['robot_links'][side];poses=dict(zip(robot['names'],robot['poses_xyzw']))
                for link,parts in hulls.items():
                    if link not in poses:continue
                    pose=np.asarray(poses[link]);r=rotation_xyzw(pose[3:]);position=pose[:3]
                    for hi,h in enumerate(parts):
                        w=h.vertices@r.T+position;lo=w.min(0);up=w.max(0);indices=np.flatnonzero(np.all(high>=lo,axis=1)&np.all(low<=up,axis=1))
                        if not len(indices):continue
                        local=(triangles[indices]-position)@r
                        signed=(local.reshape(-1,3)@h.planes[:,:3].T-h.planes[:,3]).max(1)
                        deepest=max(deepest,float(max(0.,-signed.min())))
                        intersect=[int(i) for i,t in zip(indices,local) if clipped_triangle(t,h.planes,args.shrink)]
                        if intersect:hits.append(dict(side=side,link=link,hull=hi,faces=intersect))
            samples.append(dict(step=row['step'],intersecting_faces_by_hull=hits,max_node_penetration_m=deepest))
    out=dict(kind='offline_native_robot_contact_integrity_check',shrink_m=args.shrink,samples=samples,
        trace_sha256=hashlib.sha256((args.trial/'trace.jsonl.gz').read_bytes()).hexdigest(),score=None,
        limitation='Recorded samples only; native collider hull source must match the pinned runtime. No continuous-time or grasp-success claim.')
    args.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(sample_count=len(samples),max_node_penetration_m=max(s['max_node_penetration_m'] for s in samples),intersecting_hull_samples=sum(len(s['intersecting_faces_by_hull']) for s in samples)),indent=2))


if __name__=='__main__':main()
