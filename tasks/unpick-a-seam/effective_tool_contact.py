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
