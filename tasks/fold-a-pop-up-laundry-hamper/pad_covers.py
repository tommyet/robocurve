"""Ordinary 2 mm silicone pad covers, present in both demo and model runs.

The fixed covers are robot accessories, not constraints on task objects. They
supply native frictional contact only. Their soft material is approximated by
rigid collision surfaces; force is still capped at 40 N per finger.
"""
import numpy as np
from scipy.spatial.transform import Rotation


def install():
    from yam_arena import embodiment, robot
    from yam_arena.constants import GRIPPER
    from isaaclab.sim.utils import clone
    GRIPPER.update(stiffness=5000., effort=40.)
    original = embodiment.yam_arm_cfg
    if getattr(original, '_task_pad_covers', False):
        return

    def covered_config(*args, **kwargs):
        config = original(*args, **kwargs)
        original_spawn = config.spawn.func

        @clone
        def spawn(path, cfg, **spawn_kwargs):
            prim = original_spawn(path, cfg, **spawn_kwargs)
            from pxr import UsdGeom, UsdPhysics, PhysxSchema, Gf
            import isaaclab.sim as sim
            from isaaclab.sim.utils import bind_physics_material, bind_visual_material
            from isaaclab.sim.utils.stage import get_current_stage
            stage = get_current_stage()
            paths = robot.asset_link_paths()
            physics_path = path + '/SiliconeCoverPhysics'
            material = sim.RigidBodyMaterialCfg(static_friction=1.2, dynamic_friction=1.0, restitution=0.)
            material.func(physics_path, material)
            visual_path = path + '/SiliconeCoverVisual'
            visual = sim.PreviewSurfaceCfg(diffuse_color=(.15, .15, .15), roughness=.85)
            visual.func(visual_path, visual)
            rotation = Rotation.from_euler('xyz', [-np.pi, 0., np.pi/2])
            q = rotation.inv().as_quat()
            for name, sign in [('tip_left', 1.), ('tip_right', -1.)]:
                # Nominal closed-link origins from the pinned YAM URDF.
                origin = np.array([sign*.0445119, -sign*.0239931, .0566829])
                centre = rotation.inv().apply(np.array([-sign*.001, 0., .135])-origin)
                shape = UsdGeom.Cube.Define(stage, path+paths[name]+'/silicone_pad_cover')
                shape.CreateSizeAttr(1.)
                shape.AddTranslateOp().Set(Gf.Vec3d(*centre))
                shape.AddOrientOp().Set(Gf.Quatf(float(q[3]), Gf.Vec3f(*q[:3])))
                shape.AddScaleOp().Set(Gf.Vec3f(.002, .018, .024))
                UsdPhysics.CollisionAPI.Apply(shape.GetPrim())
                collision = PhysxSchema.PhysxCollisionAPI.Apply(shape.GetPrim())
                collision.CreateContactOffsetAttr(.0001)
                collision.CreateRestOffsetAttr(0.)
                collision.CreateTorsionalPatchRadiusAttr(.004)
                collision.CreateMinTorsionalPatchRadiusAttr(.002)
                bind_physics_material(str(shape.GetPath()), physics_path, stage=stage)
                bind_visual_material(str(shape.GetPath()), visual_path, stage=stage)
            return prim

        config.spawn.make_uninstanceable = True
        config.spawn.func = spawn
        return config

    covered_config._task_pad_covers = True
    embodiment.yam_arm_cfg = covered_config
