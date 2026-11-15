"""Ideal static friction at the rear of the collar form.

The native surface solver supplies sliding friction but not static friction.
This optional material approximation retains a 10 mm contact patch already
touching the back of the form. The rest of the ribbon remains native flexible
cloth with self-contact. It neither creates a crossing nor tightens a knot.
Force-limited slip is not calibrated; a failed native binding is released.
The rule is geometric and identical for every policy.
"""
import numpy as np


def contact_patch(points):
    p = np.asarray(points)
    radius = np.linalg.norm(p[:, :2] - [.40, 0.], axis=1)
    candidates = np.flatnonzero((p[:, 0] > .450) & (abs(p[:, 1]) < .010) &
        (p[:, 2] > 1.240) & (p[:, 2] < 1.270) &
        (radius >= .0545) & (radius <= .0570))
    if len(candidates) < 3:
        return np.empty(0, dtype=int)
    centre = candidates[np.argmin(np.linalg.norm(p[candidates] - [.456, 0., 1.250], axis=1))]
    return candidates[np.linalg.norm(p[candidates] - p[centre], axis=1) <= .005]


def install(base):
    import omni.usd
    from pxr import Sdf, Vt, UsdGeom
    stage = omni.usd.get_context().get_stage()
    cloth = base.scene['tie']
    paths = [str(p.GetPath()) for p in stage.Traverse()
        if str(p.GetPath()).endswith('/tie') and
        'OmniPhysicsDeformableBodyAPI' in p.GetAppliedSchemas()]
    if len(paths) != 1:
        raise RuntimeError('Expected one native tie')
    anchor = '/World/tie_collar_static_anchor'
    UsdGeom.Xform.Define(stage, anchor)
    prim = stage.DefinePrim(paths[0] + '_collar_static_friction', 'OmniPhysicsVtxXformAttachment')
    prim.CreateRelationship('omniphysics:src0').SetTargets([Sdf.Path(paths[0])])
    prim.CreateRelationship('omniphysics:src1').SetTargets([Sdf.Path(anchor)])
    enabled = prim.CreateAttribute('omniphysics:attachmentEnabled', Sdf.ValueTypeNames.Bool)
    enabled.Set(False)
    indices = prim.CreateAttribute('omniphysics:vtxIndicesSrc0', Sdf.ValueTypeNames.IntArray)
    positions = prim.CreateAttribute('omniphysics:localPositionsSrc1', Sdf.ValueTypeNames.Point3fArray)
    indices.Set([]); positions.Set([])
    state = dict(indices=[], events=[], residual_m=0., model='ideal rear collar static contact')
    targets = None
    attempted = False
    original = base.scene.write_data_to_sim
    def apply(*args, **kwargs):
        nonlocal targets, attempted
        result = original(*args, **kwargs)
        value = cloth.data.nodal_pos_w
        p = getattr(value, 'torch', value).detach().cpu().numpy()[0]
        if not attempted:
            attempted = True
            selected = contact_patch(p)
            if len(selected) >= 3:
                state['indices'] = selected.tolist()
                targets = p[selected].copy()
                indices.Set(state['indices'])
                positions.Set(Vt.Vec3fArray(targets.tolist()))
                enabled.Set(True)
                state['events'].append(dict(event='static_contact', count=len(selected)))
        elif state['indices']:
            state['residual_m'] = float(np.max(np.linalg.norm(p[state['indices']] - targets, axis=1)))
            if state['residual_m'] > .020:
                enabled.Set(False)
                state['events'].append(dict(event='binding_failed', residual_m=state['residual_m']))
                state['indices'] = []
        return result
    base.scene.write_data_to_sim = apply
    return state
