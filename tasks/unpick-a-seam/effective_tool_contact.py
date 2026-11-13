"""Read-only native collider queries for the seam-ripper contact diagnostic.

Raycasts probe parsed PhysX geometry, independent of the authored USD sizes.
They are diagnostic evidence only; no state, material or collision filter changes.
"""
import numpy as np


def query_guards(pose, root):
    from scipy.spatial.transform import Rotation
    from omni.physx import get_physx_scene_query_interface
    from tool_geometry import GUARDS
    pose=np.asarray(pose,float);rotation=Rotation.from_quat(pose[3:]).as_matrix()
    query=get_physx_scene_query_interface();records=[]
    for index,(start,length,z,radius) in enumerate(GUARDS):
        for fraction in (.1,.5,.9):
            for sign in (-1.,1.):
                local=np.array((start+fraction*length,sign*.003,z))
                origin=pose[:3]+rotation@local
                direction=rotation@np.array((0.,-sign,0.))
                hits=[]
                def record(hit):
                    if str(hit.collision)==root+f'/Guard{index}':
                        hits.append(dict(collider=str(hit.collision),body=str(hit.rigid_body),
                            distance_m=float(hit.distance),position_m=list(hit.position)))
                    return True
                query.raycast_all(origin.tolist(),direction.tolist(),.006,record)
                records.append(dict(guard=index,axial_fraction=fraction,ray_side=sign,
                    expected_entry_distance_m=.003-radius,hits=hits))
    return records


def query_native_bounds(stage_id, root, app):
    """Query parsed collider bounds using an explicit cached stage identifier."""
    import time
    from pxr import PhysicsSchemaTools
    from omni.physx.bindings._physx import acquire_physx_property_query_interface
    report={'finished':False,'colliders':[],'rigid_bodies':[]}
    def finished():report['finished']=True
    def collider(value):
        report['colliders'].append(dict(path=str(PhysicsSchemaTools.intToSdfPath(value.path_id)),
            result=str(value.result),local_position_m=list(value.local_pos),local_rotation=list(value.local_rot),
            aabb_local_min_m=list(value.aabb_local_min),aabb_local_max_m=list(value.aabb_local_max),
            volume_m3=float(value.volume)))
    def body(value):
        report['rigid_bodies'].append(dict(path=str(PhysicsSchemaTools.intToSdfPath(value.path_id)),result=str(value.result)))
    acquire_physx_property_query_interface().query_prim(stage_id,PhysicsSchemaTools.sdfPathToInt(root),
        timeout_ms=2000,finished_fn=finished,rigid_body_fn=body,collider_fn=collider)
    deadline=time.monotonic()+3.
    while not report['finished'] and time.monotonic()<deadline:app.update()
    return report


def tool_contacts(physics, root):
    """Exact native collider-pair contact points; no assumptions about forces."""
    from pxr import PhysicsSchemaTools
    headers,data=physics.get_contact_report()
    rows=[]
    for h in headers:
        colliders=[str(PhysicsSchemaTools.intToSdfPath(x)) for x in (h.collider0,h.collider1)]
        if not any(c.startswith(root+'/ripper_') for c in colliders):continue
        if not any('/stitch_' in c for c in colliders):continue
        points=[]
        for k in range(h.contact_data_offset,h.contact_data_offset+h.num_contact_data):
            c=data[k];points.append(dict(position_m=list(c.position),normal=list(c.normal),
                separation_m=float(c.separation),impulse_ns=list(c.impulse)))
        rows.append(dict(colliders=colliders,points=points))
    return rows
