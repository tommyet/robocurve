"""Non-colliding dose visualization: cells partitioned at a circular boundary."""
import math


def _split(polygon,n,limit):
    inside=[];outside=[]
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        da=sum(x*y for x,y in zip(a,n))-limit;db=sum(x*y for x,y in zip(b,n))-limit
        (inside if da<=0 else outside).append(a)
        if (da<=0)!=(db<=0):
            f=da/(da-db);p=tuple(x+f*(y-x) for x,y in zip(a,b))
            inside.append(p);outside.append(p)
    return inside,outside


def circle_cell_parts(y,z,half,center,radius,sides=128):
    """Partition one square into white/gray polygons; 128-sided inscribed circle.

    This affects appearance only. The scorer uses analytic circle/cell areas.
    Maximum radial visualization error is radius*(1-cos(pi/128)) < 13 microns.
    """
    local=[(y-center[0]+dy,z-center[1]+dz) for dy,dz in ((-half,-half),(half,-half),(half,half),(-half,half))]
    apothem=radius*math.cos(math.pi/sides)
    if max(a*a+b*b for a,b in local)<=apothem*apothem:parts=[(local,True)]
    elif max(0,abs(y-center[0])-half)**2+max(0,abs(z-center[1])-half)**2>=radius*radius:parts=[(local,False)]
    else:
        remaining=local;parts=[]
        for i in range(sides):
            angle=2*math.pi*(i+.5)/sides
            remaining,outside=_split(remaining,(math.cos(angle),math.sin(angle)),apothem)
            if len(outside)>=3:parts.append((outside,False))
            if not remaining:break
        if len(remaining)>=3:parts.append((remaining,True))
    return [([(a+center[0],b+center[1]) for a,b in polygon],target) for polygon,target in parts]
