"""Read-only sampled geometry audit from measured native wheel/robot poses.

The rim and wrench jaws use their authored convex meshes. Circular rods and
barrels are conservatively enclosed by oriented boxes, so reported overlaps
there may be enclosure false positives. This is not a continuous-time contact
or native force audit, and it never assigns a task score.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from audit_robot_plan import box,convex,overlap,candidate_pairs,tool_props
from wheel_scene import stand_boxes,NIPPLE_FLAT_LENGTH_M
from rim_geometry import sector_mesh
from mechanics import WheelSpec
from thread_coupling import rotation


def measured_props(row):
    from fixture_layout import pointer_position
    fixture_layout=row.get('fixture_layout','reference')
    poses=dict(zip(row['body_names'],np.asarray(row['body_poses'],float)))
    props=[box('table',(.35,0.,.7175),(1.10,1.30,.06))]
    props.extend(box('stand/'+name,center,size) for name,center,size in stand_boxes(fixture_layout))
    props.append(box('stand/pointer',pointer_position(fixture_layout),(.020,.002,.002)))
    spec=WheelSpec()
    for i in range(spec.spokes):
        pose=poses[f'wheel/rim_{i:02d}'];points,_=sector_mesh(index=i)
        props.append(convex(f'rim/{i}',points@rotation(pose[3:]).T+pose[:3]))
        pose=poses[f'wheel/nipple_{i:02d}'];R=rotation(pose[3:])
        props.append(box(f'nipple/{i}/flats',pose[:3],(NIPPLE_FLAT_LENGTH_M,.00323,.00323),R))
        props.append(box(f'nipple/{i}/barrel_enclosure',pose[:3]+R@np.array((.006,0.,0.)),(.006,.003,.003),R))
        theta=i*2*np.pi/spec.spokes;side=1 if i%2==0 else-1
        angle=theta+side*spec.cross_angle_rad
        anchor=np.array((spec.hub_flange_radius_m*np.cos(angle),spec.hub_flange_radius_m*np.sin(angle),side*spec.hub_half_width_m))
        endpoint=np.array((spec.rim_radius_m*np.cos(theta),spec.rim_radius_m*np.sin(theta),0.))
        length=np.linalg.norm(endpoint-anchor)
        for half in ('inner','outer'):
            pose=poses[f'wheel/spoke_{i:02d}_{half}']
            props.append(box(f'spoke/{i}/{half}_enclosure',pose[:3],(length/2+.002,.002,.002),rotation(pose[3:])))
    pose=poses['wheel/hub'];R=rotation(pose[3:])
    props.extend((box('hub/axle',pose[:3]+R@np.array((0.,0.,.015)),(.010,.010,.100),R),
                  box('hub/barrel',pose[:3],(.035,.035,.050),R)))
    for side in (-1,1):
        props.append(box(f'hub/flange{side}_enclosure',pose[:3]+R@np.array((0.,0.,side*.025)),(.050,.050,.003),R))
    pose=poses['wrench']
    return props,tool_props(pose[:3],rotation(pose[3:]))


def robot_props(joints,hulls):
    from yam_arena import station
    from yam_arena.analysis import fk_link_poses_world
    from yam_arena.constants import ARM_JOINTS,FINGER_JOINTS,FINGER_OPEN
    joints=np.asarray(joints,float);robots={}
    for side,offset in (('left',0),('right',7)):
        q=dict(zip(ARM_JOINTS,joints[offset:offset+6]))
        q.update({name:joints[offset+6]*FINGER_OPEN for name in FINGER_JOINTS})
        links=fk_link_poses_world(q,station.BASES[side]);robot=[]
        for name,T in links.items():
            for index,hull in enumerate(hulls.get(name,[])):
                vertices=hull.vertices@T[:3,:3].T+T[:3,3]
                normals=hull.planes[:,:3]@T[:3,:3].T
                robot.append(dict(name=f'{side}/{name}/{index}',vertices=vertices,
                    planes=np.c_[normals,-hull.planes[:,3]-normals@T[:3,3]],
                    low=vertices.min(0),high=vertices.max(0)))
        robots[side]=robot
    return robots


def inspect(row,hulls,margin=.0002):
    props,wrench=measured_props(row);robots=robot_props(row['joint_pos'],hulls)
    unexpected=[];expected=[]
    def record(a,b,allowed):
        depth=overlap(a,b,margin)
        if depth is None:return
        item=dict(body=a['name'],prop=b['name'],intersection_ball_radius_m=depth)
        (expected if allowed else unexpected).append(item)
    for side,robot in robots.items():
        all_props=props+wrench
        for ai,bi in candidate_pairs(robot,all_props,margin):
            a,b=robot[ai],all_props[bi]
            intended='/tip_' in a['name'] and ((side=='left' and b['name'].startswith('rim/')) or
                (side=='right' and b['name']=='wrench/handle'))
            record(a,b,intended)
    for ai,bi in candidate_pairs(robots['left'],robots['right'],margin):
        record(robots['left'][ai],robots['right'][bi],False)
    for ai,bi in candidate_pairs(wrench,props,margin):
        a,b=wrench[ai],props[bi]
        intended=(b['name']=='table' or
            (a['name'].startswith(('wrench/jaw','wrench/back')) and b['name'].startswith('nipple/')))
        record(a,b,intended)
    return dict(step=row['step'],time_s=row['time_s'],stage=row.get('stage'),
                unexpected_intersections=unexpected,expected_contacts=expected)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--from-step',type=int,default=0);p.add_argument('--through-step',type=int)
    p.add_argument('--margin',type=float,default=.0002)
    a=p.parse_args()
    if a.from_step<0 or a.margin<0:p.error('Nonnegative sample start and margin required')
    from yam_arena import YAM_URDF
    from yam_arena.analysis import link_hulls
    native_report=json.loads((a.run/'preview.json').read_text())
    geometry_hashes={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in ('wheel_scene.py','fixture_layout.py','rim_geometry.py','mechanics.py')}
    if any(native_report.get('source_sha256',{}).get(name)!=digest for name,digest in geometry_hashes.items()):
        raise ValueError('Native run and current wheel geometry differ; use its frozen geometry source')
    hulls=link_hulls();trace=a.run/'trace.jsonl.gz';samples=[]
    with gzip.open(trace,'rt') as handle:
        for line in handle:
            row=json.loads(line)
            if row['step']<a.from_step or (a.through_step is not None and row['step']>a.through_step):continue
            samples.append(inspect(row,hulls,a.margin))
    report=dict(kind='measured_native_sampled_geometry_audit',score=None,margin_m=a.margin,
        trace_sha256=hashlib.sha256(trace.read_bytes()).hexdigest(),
        geometry_sha256=geometry_hashes,
        urdf_sha256=hashlib.sha256(Path(YAM_URDF).read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),samples=samples,
        limitations=['20Hz measured states, not continuous-time or native contact forces',
          'Conservative circular-body enclosures can overreport intersections',
          'No within-arm self-collision screen; native simulator remains responsible',
          'Intended contact intersections still need physical magnitude review'])
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n')
    hits=[hit for row in samples for hit in row['unexpected_intersections']]
    print(json.dumps(dict(samples=len(samples),unexpected_intersections=len(hits),
        maximum_intersection_ball_radius_m=max((h['intersection_ball_radius_m'] for h in hits),default=0.)),indent=2))


if __name__=='__main__':main()
