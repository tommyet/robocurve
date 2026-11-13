"""Independent paper/wire crossing audit, never a physics or release controller.

A centreline crossing an intact paper triangle is an invalid solver state even
if the sheet's final strain is small. Real withdrawal must use the existing
holes. Swept endpoints are checked in each triangle's translated frame against
both its previous and current shape; this catches translation tunnelling.
"""
import numpy as np


def _hits(start, end, e1, e2):
    direction=end-start
    h=np.cross(direction,e2)
    determinant=np.sum(e1*h,axis=-1)
    usable=np.abs(determinant)>1e-20
    inverse=np.zeros_like(determinant)
    np.divide(1.,determinant,out=inverse,where=usable)
    u=np.sum(start*h,axis=-1)*inverse
    q=np.cross(start,e1)
    v=np.sum(direction*q,axis=-1)*inverse
    t=np.sum(e2*q,axis=-1)*inverse
    eps=1e-7
    return usable&(u>=-eps)&(v>=-eps)&(u+v<=1+eps)&(t>=-eps)&(t<=1+eps)


def segment_triangle_intersections(segments, triangles):
    segments=np.asarray(segments,float);triangles=np.asarray(triangles,float)
    start=segments[:,None,0,:]-triangles[None,:,0,:]
    end=segments[:,None,1,:]-triangles[None,:,0,:]
    return _hits(start,end,(triangles[:,1]-triangles[:,0])[None],
                 (triangles[:,2]-triangles[:,0])[None])


def swept_endpoint_intersections(previous_segments,current_segments,previous_triangles,current_triangles):
    old=np.asarray(previous_segments,float).reshape(-1,3)
    new=np.asarray(current_segments,float).reshape(-1,3)
    old_tri=np.asarray(previous_triangles,float);new_tri=np.asarray(current_triangles,float)
    start=old[:,None,:]-old_tri[None,:,0,:]
    end=new[:,None,:]-new_tri[None,:,0,:]
    return (_hits(start,end,(old_tri[:,1]-old_tri[:,0])[None],(old_tri[:,2]-old_tri[:,0])[None]) |
            _hits(start,end,(new_tri[:,1]-new_tri[:,0])[None],(new_tri[:,2]-new_tri[:,0])[None]))


class PaperWireCrossingGuard:
    def __init__(self,faces):
        self.faces=np.asarray(faces,int)
        self.previous_segments=None;self.previous_triangles=None
        self.failed=False;self.first_failure=None;self.steps=0

    def update(self,points,segments):
        self.steps+=1
        points=np.asarray(points,float);segments=np.asarray(segments,float)
        if not np.isfinite(points).all() or not np.isfinite(segments).all():
            self.failed=True
            self.first_failure=self.first_failure or {'step':self.steps,'reason':'nonfinite contact geometry'}
            return self.summary()
        triangles=points[self.faces]
        wire_low=segments.min(axis=(0,1));wire_high=segments.max(axis=(0,1))
        tri_low=triangles.min(1);tri_high=triangles.max(1)
        if self.previous_segments is not None:
            wire_low=np.minimum(wire_low,self.previous_segments.min(axis=(0,1)))
            wire_high=np.maximum(wire_high,self.previous_segments.max(axis=(0,1)))
            tri_low=np.minimum(tri_low,self.previous_triangles.min(1))
            tri_high=np.maximum(tri_high,self.previous_triangles.max(1))
        candidate=np.all((tri_high>=wire_low-1e-10)&(tri_low<=wire_high+1e-10),axis=1)
        current=triangles[candidate]
        static_hits=int(segment_triangle_intersections(segments,current).sum()) if len(current) else 0
        swept_hits=0
        if self.previous_segments is not None and len(current):
            swept_hits=int(swept_endpoint_intersections(self.previous_segments,segments,
                          self.previous_triangles[candidate],current).sum())
        if static_hits or swept_hits:
            self.failed=True
            self.first_failure=self.first_failure or {'step':self.steps,'reason':'wire crosses intact paper triangles',
                    'static_intersections':static_hits,'swept_intersections':swept_hits}
        self.previous_segments=segments.copy();self.previous_triangles=triangles.copy()
        return self.summary()

    def summary(self):
        return {'valid':not self.failed,'steps':self.steps,'first_failure':self.first_failure}


def wire_chain_continuity(segments, maximum_gap_m=.00003):
    """Check the intact steel chain independently of paper contact.

    The30µm numerical envelope is one tenth of the300µm wire thickness. A
    disconnected chain cannot count as an intact extracted staple. This is
    an assessor guard, not a force, joint repair or a break/release controller.
    """
    segments=np.asarray(segments,float)
    if segments.ndim!=3 or segments.shape[1:]!=(2,3) or len(segments)<2 or not np.isfinite(segments).all():
        raise ValueError('A finite ordered chain of steel segments is required')
    gap=float(np.linalg.norm(segments[:-1,1]-segments[1:,0],axis=1).max(initial=0.))
    return dict(maximum_endpoint_gap_m=gap,maximum_allowed_gap_m=maximum_gap_m,valid=gap<=maximum_gap_m)
