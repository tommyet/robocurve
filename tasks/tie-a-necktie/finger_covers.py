"""Smooth convex finger covers for broad-cloth handling.

Each cover approximates the convex envelope of the original finger geometry
on a 0.25 mm geometry grid.
It fills the lattice openings and internal decomposition seams, like a smooth
rigid sleeve. It is visible and moves with the original finger joint. Native
contact and the same contact-gated pinch law apply to both policies.
"""
import json
from pathlib import Path


def collision_hulls():
    """The same smooth envelopes for offline commanded-pose collision checks."""
    import numpy as np
    from scipy.spatial import ConvexHull
    from yam_arena.analysis import Hull, link_hulls
    hulls = dict(link_hulls())
    shapes = json.loads(Path(__file__).with_name('finger-covers.json').read_text())
    for name, data in shapes.items():
        points = np.asarray(data['points'])
        equations = ConvexHull(points).equations
        hulls[name] = [Hull(points, np.c_[equations[:, :3], -equations[:, 3]])]
    return hulls


def install(stage):
    from pxr import Gf, Vt, UsdGeom, UsdPhysics, PhysxSchema
    shapes = json.loads(Path(__file__).with_name('finger-covers.json').read_text())
    records = []
    for link in list(stage.Traverse()):
        name = link.GetName()
        if name not in shapes or not link.HasAPI(UsdPhysics.RigidBodyAPI):
            continue
        prefix = str(link.GetPath()) + '/'
        original = [p for p in stage.Traverse()
                    if str(p.GetPath()).startswith(prefix)
                    and p.HasAPI(UsdPhysics.CollisionAPI)]
        if not original:
            raise RuntimeError('Finger has no original collision geometry')
        for prim in original:
            UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Set(False)
        data = shapes[name]
        mesh = UsdGeom.Mesh.Define(stage, prefix + 'smooth_cloth_cover')
        mesh.CreatePointsAttr(Vt.Vec3fArray(data['points']))
        mesh.CreateFaceVertexCountsAttr([3] * len(data['faces']))
        mesh.CreateFaceVertexIndicesAttr([i for face in data['faces'] for i in face])
        mesh.CreateSubdivisionSchemeAttr('none')
        mesh.CreateDisplayColorAttr([Gf.Vec3f(.18, .20, .22)])
        UsdPhysics.CollisionAPI.Apply(mesh.GetPrim()).CreateCollisionEnabledAttr(True)
        UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim()).CreateApproximationAttr('convexHull')
        PhysxSchema.PhysxConvexHullCollisionAPI.Apply(mesh.GetPrim()).CreateHullVertexLimitAttr(256)
        collision = PhysxSchema.PhysxCollisionAPI.Apply(mesh.GetPrim())
        collision.CreateContactOffsetAttr(.001)
        collision.CreateRestOffsetAttr(0.)
        records.append(dict(link=str(link.GetPath()), disabled_parts=len(original),
                            cover=str(mesh.GetPath()), bounds=data['bounds']))
    if len(records) != 4:
        raise RuntimeError('Expected four covered fingers')
    return dict(model='smooth convex covers of the original finger envelope',
                covers=records, mass_note='Original robot mass and motors retained; cover mass is neglected.')
