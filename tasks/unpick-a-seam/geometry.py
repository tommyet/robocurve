"""Two flexible canvas patches and six closed tacking stitches, in SI units.

Needle holes are openings in both cloth meshes. Thread passes through them;
there are no attachments between thread and cloth. Each closed thread loop
approximates a tied tack. It is not a machine lockstitch or a running seam.
"""
from collections import Counter,defaultdict
from dataclasses import dataclass
import numpy as np

TABLE_TOP=.7475
HOLE_HALF=.0006
STITCH_Y=np.linspace(-.030,.030,6)


@dataclass
class Mesh:
    rest: np.ndarray
    faces: np.ndarray

    def audit(self):
        p,f=self.rest,self.faces
        if not np.isfinite(p).all() or p.ndim!=2 or p.shape[1]!=3 or f.ndim!=2 or f.shape[1]!=3:
            raise ValueError('Invalid cloth geometry')
        areas=np.linalg.norm(np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]]),axis=1)/2
        if np.any(areas<1e-12):raise ValueError('Degenerate cloth triangles')
        edges=Counter(tuple(sorted((int(a),int(b)))) for tri in f for a,b in zip(tri,np.roll(tri,-1)))
        if max(edges.values())>2:raise ValueError('Nonmanifold cloth mesh')
        adjacency=defaultdict(set);boundary=defaultdict(set)
        for (a,b),n in edges.items():
            adjacency[a].add(b);adjacency[b].add(a)
            if n==1:boundary[a].add(b);boundary[b].add(a)
        def components(graph):
            unseen=set(graph);result=[]
            while unseen:
                first=unseen.pop();todo=[first];seen={first}
                while todo:
                    for n in graph[todo.pop()]:
                        if n not in seen:seen.add(n);unseen.discard(n);todo.append(n)
                result.append(seen)
            return result
        if len(components(adjacency))!=1 or len(adjacency)!=len(p):raise ValueError('Disconnected fabric')
        if any(len(v)!=2 for v in boundary.values()):raise ValueError('Branching hole boundary')
        return {'vertices':len(p),'triangles':len(f),'surface_area_m2':float(areas.sum()),
                'boundary_loops':len(components(boundary)),'connected':True}


def patch(left=True):
    xmin,xmax=(.235,.310) if left else (.290,.365)
    xs=np.unique(np.round(np.r_[np.linspace(xmin,xmax,26),
                                 .295-HOLE_HALF,.295+HOLE_HALF,.305-HOLE_HALF,.305+HOLE_HALF],9))
    ys=np.unique(np.round(np.r_[np.linspace(-.040,.040,33),STITCH_Y-HOLE_HALF,STITCH_Y+HOLE_HALF],9))
    vertices=[];faces=[];ids={}
    def vertex(i,j):
        if (i,j) not in ids:
            ids[i,j]=len(vertices)
            vertices.append((xs[i],ys[j],TABLE_TOP+(.004 if left else .0032)))
        return ids[i,j]
    for i in range(len(xs)-1):
        for j in range(len(ys)-1):
            x,y=(xs[i]+xs[i+1])/2,(ys[j]+ys[j+1])/2
            hole=any(abs(x-hx)<HOLE_HALF and abs(y-hy)<HOLE_HALF for hx in (.295,.305) for hy in STITCH_Y)
            if hole:continue
            a,b,c,d=vertex(i,j),vertex(i+1,j),vertex(i+1,j+1),vertex(i,j+1)
            faces.extend(((a,b,c),(a,c,d)))
    mesh=Mesh(np.asarray(vertices),np.asarray(faces,int));mesh.audit();return mesh


def stitch_loop(y,spacing=.001):
    """Closed 10 x 2.4 mm centreline; spans both layers through real holes."""
    points=np.array([[.295,y,TABLE_TOP+.0048],[.305,y,TABLE_TOP+.0048],
                     [.305,y,TABLE_TOP+.0024],[.295,y,TABLE_TOP+.0024]])
    nodes=[]
    for a,b in zip(points,np.roll(points,-1,axis=0)):
        n=max(1,int(np.ceil(np.linalg.norm(b-a)/spacing)))
        nodes.extend(a+(b-a)*s/n for s in range(n))
    return np.asarray(nodes)


def audit_scene():
    cloth=[patch(True),patch(False)]
    result={'cloth':[m.audit() for m in cloth],'stitches':[]}
    for y in STITCH_Y:
        nodes=stitch_loop(y)
        lengths=np.linalg.norm(np.roll(nodes,-1,axis=0)-nodes,axis=1)
        result['stitches'].append({'nodes':len(nodes),'length_m':float(lengths.sum()),
                                  'minimum_link_m':float(lengths.min()),'closed':True})
    # Both layers must have one outer boundary and twelve real needle holes.
    if any(row['boundary_loops']!=13 for row in result['cloth']):
        raise ValueError('The thread geometry requires twelve holes per patch')
    return result
