"""Conforming cloth refinement at the measured wide-end grip.

Only numerical resolution changes. New rest, reset and diagnostic checkpoint
nodes use the same linear interpolation; no contact projection is performed.
"""
import copy
import numpy as np
from cloth_mesh import Mesh


def refine(base, maximum_edge=.00125):
    points=base.rest.tolist();faces=base.faces.tolist();midpoints=[]
    for _ in range(6):
        p=np.asarray(points);f=np.asarray(faces);tri=p[f]
        selected=(tri[:,:,1].max(1)>=.16)&(tri[:,:,1].min(1)<=.24)
        edges={tuple(sorted((int(a),int(b)))) for row in f[selected]
               for a,b in zip(row,np.roll(row,-1))
               if np.linalg.norm(p[a]-p[b])>maximum_edge*1.000001}
        if not edges:break
        mid={}
        for a,b in sorted(edges):
            mid[a,b]=len(points);midpoints.append((a,b));points.append(((p[a]+p[b])/2).tolist())
        updated=[]
        for row in faces:
            a,b,c=row;m=[mid.get(tuple(sorted(e))) for e in ((a,b),(b,c),(c,a))];n=sum(x is not None for x in m)
            if n==0:updated.append(row)
            elif n==3:
                ab,bc,ca=m;updated.extend(((a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)))
            elif n==1:
                k=next(i for i,x in enumerate(m) if x is not None);a,b,c=[row[(k+i)%3] for i in range(3)];ab=m[k];updated.extend(((a,ab,c),(ab,b,c)))
            else:
                k=next(i for i in range(3) if m[i] is not None and m[(i+1)%3] is not None)
                a,b,c=[row[(k+i)%3] for i in range(3)];ab,bc=m[k],m[(k+1)%3];updated.extend(((b,bc,ab),(a,ab,c),(ab,bc,c)))
        faces=updated
    else:raise RuntimeError('Grip refinement did not converge')
    p=np.asarray(points);order=np.lexsort((p[:,0],p[:,1]));inverse=np.empty(len(order),int);inverse[order]=np.arange(len(order));p=p[order]
    levels=np.unique(p[:,1]);rows=[np.flatnonzero(abs(p[:,1]-s)<1e-10).tolist() for s in levels]
    markers=copy.deepcopy(base.markers)
    markers.update(row_nodes=rows,centreline=[r[int(np.argmin(abs(p[r,0])))] for r in rows],
        wide_tip=rows[0][0],narrow_tip=rows[-1][0],
        grip_refinement=dict(longitudinal_region_m=[.16,.24],maximum_edge_m=maximum_edge))
    mesh=Mesh(p,inverse[np.asarray(faces,int)],markers)
    a,b=mesh.audit(),base.audit()
    if len(a['boundary_loops'])!=len(b['boundary_loops']) or abs(a['surface_area_m2']-b['surface_area_m2'])>1e-12:
        raise ValueError('Refinement changed cloth area or topology')
    return mesh,np.asarray(midpoints,int),order


def interpolate(values,midpoints,order):
    original=np.asarray(values)
    result=np.empty((len(order),*original.shape[1:]),dtype=original.dtype)
    result[:len(original)]=original
    for index,(a,b) in enumerate(midpoints,len(original)):
        if max(a,b)>=index:raise ValueError('Refinement interpolation is not acyclic')
        result[index]=(result[a]+result[b])/2
    return result[order]
