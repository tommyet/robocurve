"""Offline collision screening of a fixed joint plan, not native contact proof.

The desired joint targets are placed using the URDF. A held wrench is assumed
to follow its proposed grasp; native slip, deflection and contact response are
not predicted. Positive convex intersection identifies a planning problem;
absence at sampled poses does not establish continuous-time clearance.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
from scipy.spatial import ConvexHull
from motion_plan import load, TOOL_TCP, GRIP
from wheel_scene import (stand_boxes,wheel_world_frame,wrench_jaw_mesh,x_frame,
    WRENCH_ORIGIN_M,WRENCH_HANDLE_CENTER_M,WRENCH_HANDLE_SIZE_M,
    WRENCH_NECK_CENTER_M,WRENCH_NECK_SIZE_M)
from rim_geometry import sector_mesh
from mechanics import WheelSpec
from plan_turns import nominal_nipple


SIGNS=np.asarray(list(itertools.product((-1.,1.),repeat=3)))


def convex(name,points):
    points=np.asarray(points)
    h=ConvexHull(points)
    planes=np.unique(np.round(h.equations,12),axis=0)
    return dict(name=name,vertices=points,planes=planes,low=points.min(0),high=points.max(0))


def box(name,center,size,rotation=None):
    rotation=np.eye(3) if rotation is None else rotation
    return convex(name,(SIGNS*np.asarray(size)/2)@rotation.T+center)


def overlap(a,b,margin=.0002):
    if np.any(np.minimum(a['high'],b['high'])-np.maximum(a['low'],b['low'])<2*margin):return None
    # Largest ball inside the intersection: both plane sets have unit normals.
    planes=np.vstack((a['planes'],b['planes']))
    result=linprog([0.,0.,0.,-1.],A_ub=np.c_[planes[:,:3],np.ones(len(planes))],
                   b_ub=-planes[:,3],bounds=[(None,None)]*3+[(0.,None)],method='highs')
    if result.success and result.x[3]>margin:return float(result.x[3])
    return None


def candidate_pairs(a,b,margin):
    """Batch the same positive-overlap AABB predicate before convex solving."""
    low_a=np.asarray([h['low'] for h in a]);high_a=np.asarray([h['high'] for h in a])
    low_b=np.asarray([h['low'] for h in b]);high_b=np.asarray([h['high'] for h in b])
    return np.argwhere(np.all(np.minimum(high_a[:,None,:],high_b[None,:,:])-np.maximum(low_a[:,None,:],low_b[None,:,:])>=2*margin,axis=2))


def wheel_props(clocking,flat_phase):
    s=WheelSpec();W=wheel_world_frame(clocking);origin=np.array((.35,0.,1.005));props=[]
    props.append(box('table',(.35,0.,.7175),(1.10,1.30,.06)))
    props.extend(box('stand/'+name,center,size) for name,center,size in stand_boxes())
    props.append(box('stand/pointer',(.373,0.,.785),(.020,.002,.002)))
    theta=np.arange(s.spokes)*2*np.pi/s.spokes
    verts=np.c_[s.rim_radius_m*np.cos(theta),s.rim_radius_m*np.sin(theta),np.zeros(s.spokes)]
    for i in range(s.spokes):
        center=(verts[i]+verts[(i+1)%s.spokes])/2;R=x_frame(verts[(i+1)%s.spokes]-verts[i])
        points,_=sector_mesh(index=i)
        props.append(convex(f'rim/{i}',(points@R.T+center)@W.T+origin))
        pos,rot=nominal_nipple(i,flat_phase,clocking)
        props.append(box(f'nipple/{i}',pos,(.006,.00323,.00323),rot))
        side=1 if i%2==0 else -1;angle=theta[i]+side*s.cross_angle_rad
        anchor=np.array((s.hub_flange_radius_m*np.cos(angle),s.hub_flange_radius_m*np.sin(angle),side*s.hub_half_width_m))
        # A square2mm enclosure conservatively bounds each circular shaft.
        length=np.linalg.norm(verts[i]-anchor);rot=W@x_frame(verts[i]-anchor)
        props.append(box(f'spoke_enclosure/{i}',origin+W@((verts[i]+anchor)/2),(length+.002,.002,.002),rot))
    props.append(box('hub/axle',origin+W@np.array((0.,0.,.015)),(.010,.010,.100),W))
    props.append(box('hub/barrel',origin,(.035,.035,.050),W))
    return props


def tool_props(center,R):
    props=[box('wrench/handle',center+R@np.array(WRENCH_HANDLE_CENTER_M),WRENCH_HANDLE_SIZE_M,R),
           box('wrench/neck',center+R@np.array(WRENCH_NECK_CENTER_M),WRENCH_NECK_SIZE_M,R),
           box('wrench/back',center+R@np.array((0.,-.005,0.)),(.00725,.002,.004),R)]
    for side in (-1,1):
        points,_=wrench_jaw_mesh(side);props.append(convex(f'wrench/jaw{side}',points@R.T+center))
    return props


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('plan',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--stride',type=int,default=1);p.add_argument('--margin',type=float,default=.0002)
    p.add_argument('--from-step',type=int,default=1,help='One-based start for independently checking an unchanged-plan suffix')
    args=p.parse_args();plan,actions=load(args.plan)
    from yam_arena import ik,station,YAM_URDF
    from yam_arena.analysis import link_hulls,fk_link_poses_world
    from yam_arena.constants import ARM_JOINTS,FINGER_JOINTS,FINGER_OPEN
    hulls=link_hulls();props=wheel_props(np.deg2rad(plan['wheel_clocking_deg']),np.deg2rad(plan['nipple_flat_phase_deg']))
    if not 1<=args.from_step<=len(actions):p.error('Start step outside plan')
    samples=[];grasp_assumed=any(f['stage']=='Lift the free wrench' for f in plan['frames'][:args.from_step-1])
    for index in range(args.from_step-1,len(actions),args.stride):
        action=actions[index];stage=plan['frames'][index]['stage'];robots={}
        props=wheel_props(np.deg2rad(plan['frames'][index].get('nominal_wheel_clocking_deg',plan['wheel_clocking_deg'])),np.deg2rad(plan['nipple_flat_phase_deg']))
        if stage=='Lift the free wrench':grasp_assumed=True
        for side,offset in (('left',0),('right',7)):
            q=dict(zip(ARM_JOINTS,action[offset:offset+6]));q.update({name:action[offset+6]*FINGER_OPEN for name in FINGER_JOINTS})
            links=fk_link_poses_world(q,station.BASES[side]);robot=[]
            for name,T in links.items():
                for hi,h in enumerate(hulls.get(name,[])):
                    verts=h.vertices@T[:3,:3].T+T[:3,3];normals=h.planes[:,:3]@T[:3,:3].T
                    robot.append(dict(name=f'{side}/{name}/{hi}',vertices=verts,planes=np.c_[normals,-h.planes[:,3]-normals@T[:3,3]],low=verts.min(0),high=verts.max(0)))
            robots[side]=robot
        if grasp_assumed:
            pos,R=ik.tcp_pose(action[7:13],station.BASES['right'])
            calibration=plan.get('held_grasp_calibration',{})
            calibrated=index+1>=calibration.get('applies_from_step',float('inf'))
            grip=np.asarray(calibration['tcp_rotation_in_tool']) if calibrated else GRIP
            tcp=np.asarray(calibration['tcp_position_in_tool_m']) if calibrated else TOOL_TCP
            R=R@grip.T;center=pos-R@tcp
        else:center=np.array(WRENCH_ORIGIN_M);R=np.eye(3)
        released=plan.get('released_tool',{})
        if index+1>=released.get('from_step',float('inf')):
            center=np.asarray(released['position_m']);R=np.asarray(released['rotation'])
        wrench=tool_props(center,R);hits=[];expected=[]
        for side,robot in robots.items():
            all_props=props+wrench
            for hi,pi in candidate_pairs(robot,all_props,args.margin):
                h,prop=robot[hi],all_props[pi]
                depth=overlap(h,prop,args.margin)
                if depth is None:continue
                record=dict(body=h['name'],prop=prop['name'],intersection_ball_radius_m=depth)
                intentional=('/tip_' in h['name']) and ((side=='left' and prop['name'].startswith('rim/')) or(side=='right' and prop['name']=='wrench/handle'))
                (expected if intentional else hits).append(record)
        for ai,bi in candidate_pairs(robots['left'],robots['right'],args.margin):
            a,b=robots['left'][ai],robots['right'][bi];depth=overlap(a,b,args.margin)
            if depth is not None:hits.append(dict(body=a['name'],prop=b['name'],intersection_ball_radius_m=depth))
        # Wrench/rim clearance is essential even when hand reach is good.
        for hi,pi in candidate_pairs(wrench,props,args.margin):
            h,prop=wrench[hi],props[pi]
            if prop['name']=='table' and (not grasp_assumed or index+1>=released.get('from_step',float('inf'))):continue
            depth=overlap(h,prop,args.margin)
            if depth is None:continue
            record=dict(body=h['name'],prop=prop['name'],intersection_ball_radius_m=depth)
            intended=h['name'].startswith(('wrench/jaw','wrench/back')) and prop['name'].startswith('nipple/')
            (expected if intended else hits).append(record)
        samples.append(dict(step=index+1,stage=stage,unintended_intersections=hits,intended_contact_targets=expected))
    report=dict(kind='offline_commanded_pose_collision_screen',plan_sha256=hashlib.sha256(args.plan.read_bytes()).hexdigest(),
        urdf_sha256=hashlib.sha256(Path(YAM_URDF).read_bytes()).hexdigest(),margin_m=args.margin,stride=args.stride,from_step=args.from_step,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),samples=samples,score=None,
        limitations=['Desired joints and an assumed fixed wrench grasp, not measured native poses','Nominal rigid wheel geometry, before elastic deflection',
                     'Spoke colliders use conservative square enclosures','Inter-arm hulls checked; no within-arm self-collision or continuous-time audit',
                     'Recorded URDF and collider sources must match the pinned native runtime'])
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2)+'\n')
    hits=[h for s in samples for h in s['unintended_intersections']]
    print(json.dumps(dict(samples=len(samples),unintended_intersections=len(hits),max_intersection_radius_m=max((h['intersection_ball_radius_m'] for h in hits),default=0.)),indent=2))


if __name__=='__main__':main()
