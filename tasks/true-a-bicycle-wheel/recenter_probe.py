"""Translate the complete standalone fixture before native physics attaches.

This is a coordinate precision diagnostic, not a runtime body-state edit. Every
body and collider moves together; only world-ended joint positions also need an
explicit translation. Body-local joint anchors, rotations and materials stay put.
"""
import numpy as np


def recenter(stage, metadata, table_path='/Bench'):
    from pxr import Gf, UsdGeom, UsdPhysics
    from thread_coupling import body_paths
    root=metadata['hub_path'].split('/wheel/')[0]
    roots=(root,table_path)
    cache=UsdGeom.XformCache()
    origin=np.asarray(cache.GetLocalToWorldTransform(stage.GetPrimAtPath(metadata['hub_path'])).ExtractTranslation(),float)
    offset=-origin
    # Check every transformable descendant, including static stand/bench and
    # collider meshes, rather than only the130 dynamic body origins.
    before={}
    joints=[]
    for prim in stage.Traverse():
        path=str(prim.GetPath())
        if not any(path==r or path.startswith(r+'/') for r in roots):continue
        if prim.IsA(UsdGeom.Xformable):
            before[path]=np.asarray(cache.GetLocalToWorldTransform(prim),float)
        if not prim.IsA(UsdPhysics.Joint):continue
        joint=UsdPhysics.Joint(prim)
        for side in (0,1):
            targets=getattr(joint,f'GetBody{side}Rel')().GetTargets()
            if targets:
                if len(targets)!=1 or not str(targets[0]).startswith(root+'/'):
                    raise ValueError('Joint reaches outside translated fixture: '+path)
                continue
            attr=getattr(joint,f'GetLocalPos{side}Attr')()
            old=np.asarray(attr.Get(),float)
            if old.shape!=(3,) or not np.isfinite(old).all():
                raise ValueError('Invalid world-ended joint position: '+path)
            joints.append((path,side,attr,old))
    for path in roots:
        prim=stage.GetPrimAtPath(path)
        if not prim:raise ValueError('Missing fixture root '+path)
        xf=UsdGeom.Xformable(prim)
        old_ops=list(xf.GetOrderedXformOps())
        translation=xf.AddTranslateOp(opSuffix='precisionOrigin')
        translation.Set(Gf.Vec3d(*map(float,offset)))
        # Prepend in parent coordinates; scaling on the bench must not scale
        # this coordinate translation.
        xf.SetXformOpOrder([translation,*old_ops])
    world_joints=[]
    for path,side,attr,old in joints:
        attr.Set(Gf.Vec3f(*map(float,old+offset)))
        new=np.asarray(attr.Get(),float)
        world_joints.append(dict(path=path,side=side,original_anchor_m=old.tolist(),
            native_anchor_m=new.tolist(),float_roundoff_m=float(np.linalg.norm(new-(old+offset)))))
    cache=UsdGeom.XformCache();error=0.;rotation_error=0.
    for path,old in before.items():
        new=np.asarray(cache.GetLocalToWorldTransform(stage.GetPrimAtPath(path)),float)
        expected=old.copy();expected[3,:3]+=offset
        error=max(error,float(np.max(np.abs(new-expected))))
        rotation_error=max(rotation_error,float(np.max(np.abs(new[:3,:3]-old[:3,:3]))))
    if error>1e-12 or rotation_error>1e-12:
        raise RuntimeError('Coordinate translation changed fixture relative geometry')
    if not set(body_paths(metadata)).issubset(before):
        raise RuntimeError('Coordinate audit missed native rigid bodies')
    return dict(native_origin_in_station_m=origin.tolist(),station_to_native_offset_m=offset.tolist(),
        transformable_prims_checked=len(before),maximum_world_matrix_error=error,
        maximum_rotation_matrix_error=rotation_error,world_joint_ends=world_joints,
        stage='Authored before native attachment; no live state writes',
        reporting='Native poses use the translated frame. Add native_origin_in_station_m to recover station coordinates.')
