"""Independent thread/fabric tunnelling guard; never a release controller.

A thread centreline may pass through an existing needle hole, but not an intact
cloth triangle. Check both current capsules and swept endpoints in each moving
triangle's frame. This detects clear native-contact failures; it does not claim
to resolve grazing fibres, finite-radius contact accuracy or fracture.
"""
import numpy as np


def match_capsule_order(initial_poses,threads,tolerance_m=1e-6):
    """Identify native tensor order once at reset, without steering the policy."""
    expected=np.concatenate([(t['nodes']+np.roll(t['nodes'],-1,axis=0))/2 for t in threads])
    native=np.asarray(initial_poses,float)[:,:3]
    if native.shape!=expected.shape:raise ValueError('Missing native thread bodies')
    distance=np.linalg.norm(expected[:,None,:]-native[None,:,:],axis=2)
    order=distance.argmin(axis=1)
    if len(np.unique(order))!=len(order) or np.max(distance[np.arange(len(order)),order])>tolerance_m:
        raise ValueError('Cannot identify initial native thread order unambiguously')
    return order


def capsule_endpoints(poses,lengths):
    p=np.asarray(poses,float);lengths=np.asarray(lengths,float)
    if p.shape!=(len(lengths),7) or not np.isfinite(p).all():
        raise ValueError('Invalid native thread capsule transforms')
    q=p[:,3:];norm=np.linalg.norm(q,axis=1)
    if np.any(norm<1e-9):raise ValueError('Invalid native thread rotation')
    x,y,z,w=(q/norm[:,None]).T
    axis=np.column_stack((1-2*(y*y+z*z),2*(x*y+w*z),2*(x*z-w*y)))
    half=axis*lengths[:,None]/2
    return np.stack((p[:,:3]-half,p[:,:3]+half),axis=1)


def _hits(start,end,triangles):
    """Matched segment/triangle intersection, after an AABB broad phase."""
    e1=triangles[:,1]-triangles[:,0];e2=triangles[:,2]-triangles[:,0]
    d=end-start;s=start-triangles[:,0]
    h=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,h)
    good=np.abs(det)>1e-20
    inv=np.divide(1.,det,out=np.zeros_like(det),where=good)
    u=np.einsum('ij,ij->i',s,h)*inv
    q=np.cross(s,e1);v=np.einsum('ij,ij->i',d,q)*inv
    t=np.einsum('ij,ij->i',e2,q)*inv
    eps=1e-7
    return good&(u>=-eps)&(v>=-eps)&(u+v<=1+eps)&(t>=-eps)&(t<=1+eps)


class ThreadClothAudit:
    def __init__(self,faces):
        self.faces=np.asarray(faces,int);self.previous=None;self.previous_triangles=None
        self.first_failure=None;self.steps=0

    def update(self,points,segments,time_s):
        self.steps+=1
        segments=np.asarray(segments,float);triangles=np.asarray(points,float)[self.faces]
        if (segments.ndim!=3 or segments.shape[1:]!=(2,3) or
                not np.isfinite(segments).all() or not np.isfinite(triangles).all()):
            raise ValueError('Invalid measured thread/fabric geometry')
        low,high=segments.min(1),segments.max(1)
        tl,th=triangles.min(1),triangles.max(1)
        if self.previous is not None:
            low=np.minimum(low,self.previous.min(1));high=np.maximum(high,self.previous.max(1))
            tl=np.minimum(tl,self.previous_triangles.min(1));th=np.maximum(th,self.previous_triangles.max(1))
        # Two-level exact AABB broad phase. Consecutive blocks cover one
        # authored 28-link tack; broad bounds never discard a possible hit.
        # This avoids allocating all 168 x 2492 x 3 candidate comparisons on
        # every physics step when each short thread touches a small mesh area.
        segment_ids=[];face_ids=[]
        for start in range(0,len(low),28):
            stop=min(start+28,len(low));lo=low[start:stop].min(0);hi=high[start:stop].max(0)
            candidates=np.flatnonzero(np.all((hi>=tl-1e-10)&(lo<=th+1e-10),axis=1))
            if not len(candidates):continue
            hit=np.all((high[start:stop,None]>=tl[candidates][None]-1e-10)&
                       (low[start:stop,None]<=th[candidates][None]+1e-10),axis=2)
            si,fi=np.nonzero(hit);segment_ids.extend(si+start);face_ids.extend(candidates[fi])
        segment=np.asarray(segment_ids,int);face=np.asarray(face_ids,int)
        current=triangles[face]
        static=_hits(segments[segment,0],segments[segment,1],current)
        swept=np.zeros(len(segment),dtype=bool)
        if self.previous is not None:
            old=self.previous_triangles[face]
            displacement=current[:,0]-old[:,0]
            for endpoint in (0,1):
                # Check translation in both old and new triangle shape. The
                # elastic-domain audit separately bounds large deformation.
                a=self.previous[segment,endpoint];b=segments[segment,endpoint]
                swept|=_hits(a,b-displacement,old)|_hits(a+displacement,b,current)
        if (static|swept).any() and self.first_failure is None:
            self.first_failure={'step':self.steps,'time_s':float(time_s),
                                'reason':'thread crosses intact fabric',
                                'static_intersections':int(static.sum()),
                                'swept_intersections':int(swept.sum())}
        self.previous=segments.copy();self.previous_triangles=triangles.copy()
        return self.first_failure is None

    def summary(self):
        return {'valid':self.first_failure is None,'steps':self.steps,'first_failure':self.first_failure}
