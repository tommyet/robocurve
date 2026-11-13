"""Offline native line/jaw coupon integrity audit; never a policy or score."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from fixture_clearance import fixture_intersections,triangle_box_intersects,_clip_z
from interpret_motion import rotation_xyzw


def radial_penetration(triangle,center,radius,height):
    poly=(np.asarray(triangle)-np.asarray(center))[:,[0,2,1]]
    if poly[:,2].max() < -height/2 or poly[:,2].min() > height/2:return 0.
    poly=_clip_z(poly,-height/2,True)
    if not len(poly):return 0.
    poly=_clip_z(poly,height/2,False)
    if not len(poly):return 0.
    xy=poly[:,:2];ends=np.roll(xy,-1,axis=0)
    cross=xy[:,0]*ends[:,1]-xy[:,1]*ends[:,0]
    if abs(cross.sum())>1e-16 and (np.all(cross>=-1e-12) or np.all(cross<=1e-12)):
        distance=0.
    else:
        delta=ends-xy;length2=(delta*delta).sum(1)
        fraction=np.divide(-(xy*delta).sum(1),length2,out=np.zeros_like(length2),where=length2>1e-24)
        closest=xy+np.clip(fraction,0.,1.)[:,None]*delta
        distance=float(np.sqrt(np.min((closest*closest).sum(1))))
    return max(0.,radius-distance)


def box_triangle_penetration(triangles,center,size):
    """Maximum uniform box inset reached by a triangle, to sub-micrometre precision."""
    low=0.;high=min(size)/2
    if not any(triangle_box_intersects(t,center,size) for t in triangles):return 0.
    for _ in range(14):
        mid=(low+high)/2
        if any(triangle_box_intersects(t,center,size,margin=-mid) for t in triangles):low=mid
        else:high=mid
    return low


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('trial',type=Path);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();report=json.loads((args.trial/'probe.json').read_text())
    if report['mode']!='line-clamp' or report['status']!='complete':raise ValueError('Requires a complete native line-clamp diagnostic')
    data=np.load(args.trial/'nodes.npz');jaw=np.load(args.trial/'pegs.npz');line=report['line_fixture'];faces=data['faces'];records=[]
    if not np.array_equal(data['times_s'],jaw['times_s']):raise ValueError('Cloth and jaw sample times differ')
    for time,nodes,poses in zip(data['times_s'],data['positions'],jaw['poses_xyzw']):
        hits=fixture_intersections(nodes,faces,{'line':line},margin=0.)['line']
        penetration=max((radial_penetration(nodes[faces[i]],line['center'],line['radius'],line['height']) for i in hits),default=0.)
        jaw_hits={};jaw_node_penetration=0.;jaw_triangle_penetration=0.
        for index,label in enumerate(('lower','upper')):
            pose=poses[index];rotation=rotation_xyzw(pose[3:]);local=(nodes-pose[:3])@rotation;sign=-1 if index==0 else 1
            shapes={label+':jaw':dict(kind='box',size=(.035,.010,.006),center=(.0175,0,sign*.0035)),
                    label+':handle':dict(kind='box',size=(.035,.010,.006),center=(-.0175,0,sign*.008))}
            all_hits=fixture_intersections(local,faces,shapes,margin=0.)
            jaw_hits.update({k:v for k,v in fixture_intersections(local,faces,shapes,margin=-.0002).items() if v})
            for name,shape in shapes.items():
                inside=np.asarray(shape['size'])/2-abs(local-np.asarray(shape['center']))
                jaw_node_penetration=max(jaw_node_penetration,float(np.maximum(inside.min(1),0.).max()))
                if all_hits[name]:
                    jaw_triangle_penetration=max(jaw_triangle_penetration,box_triangle_penetration(local[faces[all_hits[name]]],shape['center'],shape['size']))
        records.append(dict(time_s=float(time),line_intersecting_faces=hits,max_radial_penetration_m=penetration,
                            jaw_intersecting_faces=jaw_hits,max_jaw_node_penetration_m=jaw_node_penetration,
                            max_jaw_triangle_penetration_m=jaw_triangle_penetration,
                            cloth_z_range_m=[float(nodes[:,2].min()),float(nodes[:,2].max())]))
    result=dict(kind='native_coupon_offline_integrity_check',score=None,line_fixture=line,
                hashes={f:hashlib.sha256((args.trial/f).read_bytes()).hexdigest() for f in ('probe.json','nodes.npz','pegs.npz')},
                max_line_penetration_m=max(r['max_radial_penetration_m'] for r in records),
                final_line_penetration_m=records[-1]['max_radial_penetration_m'],
                line_axis_crossing_samples=sum(r['max_radial_penetration_m']>=line['radius']-1e-12 for r in records),
                jaw_overlap_samples=sum(bool(r['jaw_intersecting_faces']) for r in records),samples=records,
                max_jaw_node_penetration_m=max(r['max_jaw_node_penetration_m'] for r in records),
                max_jaw_triangle_penetration_m=max(r['max_jaw_triangle_penetration_m'] for r in records),
                limitation='Discrete native states; fixed lower jaw is a diagnostic fixture, not a task attachment. No robot or task feasibility demonstrated.')
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('samples','hashes')},indent=2))


if __name__=='__main__':main()
