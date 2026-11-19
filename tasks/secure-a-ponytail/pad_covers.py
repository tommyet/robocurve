"""Narrow steel finger extensions with silicone contact faces.

Each extension is 40 x 4 x 3 mm and leaves the original finger bodies 13 mm
behind the working point, giving access to the thin elastic. A shallow transverse V groove centres the cord.
They are rigid robot hardware in both demo and Dream runs, never grasp joints.
"""
import numpy as np
from scipy.spatial.transform import Rotation


def configure_kinematics():
    from yam_arena import constants, ik
    constants.TCP_OFFSET=(0.,0.,.160)
    ik.TCP_OFFSET=constants.TCP_OFFSET
    import sys
    if 'yam_arena.runtime' in sys.modules:sys.modules['yam_arena.runtime'].TCP_OFFSET=constants.TCP_OFFSET


def install():
    configure_kinematics()
    from yam_arena import embodiment, robot
    from yam_arena.constants import GRIPPER
    from isaaclab.sim.utils import clone
    GRIPPER.update(stiffness=5000., effort=40.)
    original = embodiment.yam_arm_cfg
    if getattr(original, '_task_pad_covers', False):
        return

    def covered_config(*args, **kwargs):
        config = original(*args, **kwargs)
        config.spawn.articulation_props.solver_position_iteration_count=64
        config.spawn.articulation_props.solver_velocity_iteration_count=16
        original_spawn = config.spawn.func

        @clone
        def spawn(path, cfg, **spawn_kwargs):
            prim = original_spawn(path, cfg, **spawn_kwargs)
            from pxr import UsdGeom, UsdPhysics, PhysxSchema, Gf, Vt
            import isaaclab.sim as sim
            from isaaclab.sim.utils import bind_physics_material, bind_visual_material
            from isaaclab.sim.utils.stage import get_current_stage
            stage = get_current_stage()
            paths = robot.asset_link_paths()
            # The 3 mm contact faces touch at a 6 mm nominal jaw gap. The pinned
            # model lacks a cover-to-cover closing stop, so represent that ordinary
            # physical stop with the two prismatic joint limits.
            stops=[]
            for joint_prim in stage.Traverse():
                if str(joint_prim.GetPath()).startswith(path+'/') and joint_prim.GetName() in ('joint7','joint8') and joint_prim.IsA(UsdPhysics.PrismaticJoint):
                    UsdPhysics.PrismaticJoint(joint_prim).CreateUpperLimitAttr(-.003)
                    stops.append(joint_prim.GetName())
            if sorted(stops)!=['joint7','joint8']:
                raise RuntimeError('Could not apply the two physical pad-cover closing stops.')
            physics_path = path + '/SiliconeCoverPhysics'
            material = sim.RigidBodyMaterialCfg(static_friction=1.2, dynamic_friction=1.0, restitution=0.)
            material.func(physics_path, material)
            visual_path = path + '/SiliconeCoverVisual'
            visual = sim.PreviewSurfaceCfg(diffuse_color=(.15, .15, .15), roughness=.85)
            visual.func(visual_path, visual)
            rotation = Rotation.from_euler('xyz', [-np.pi, 0., np.pi/2])
            q = rotation.inv().as_quat()
            for name, sign in [('tip_left', 1.), ('tip_right', -1.)]:
                # joint7 opens toward negative gripper X; its cover protrudes
                # toward positive X. joint8 is the mirror image.
                # Nominal closed-link origins from the pinned YAM URDF.
                origin = np.array([sign*.0445119, -sign*.0239931, .0566829])
                centre = rotation.inv().apply(np.array([sign*.0015, 0., .152])-origin)
                PhysxSchema.PhysxRigidBodyAPI.Apply(stage.GetPrimAtPath(path+paths[name])).CreateEnableSpeculativeCCDAttr(True)
                # Four convex pieces form a continuous steel fingertip with a
                # 0.6 mm-deep, 4 mm-wide transverse V groove at the working point.
                # This is fixed hardware: the cord still enters, is pinched and
                # can slip out. No joint ever attaches it to the gripper.
                for j,(z0,z1,h0,h1) in enumerate([
                    (.132,.158,.003,.003),(.158,.160,.003,.0024),
                    (.160,.162,.0024,.003),(.162,.172,.003,.003)]):
                    points=[]
                    for z,h in [(z0,h0),(z1,h1)]:
                        for x,y in [(0,-.002),(sign*h,-.002),(sign*h,.002),(0,.002)]:
                            points.append(rotation.inv().apply(np.array([x,y,z])-origin))
                    shape=UsdGeom.Mesh.Define(stage,path+paths[name]+f'/grooved_finger_{j}')
                    shape.CreatePointsAttr(Vt.Vec3fArray(np.asarray(points,dtype=np.float32).tolist()))
                    shape.CreateFaceVertexCountsAttr([4]*6)
                    shape.CreateFaceVertexIndicesAttr([0,3,2,1,4,5,6,7,0,1,5,4,1,2,6,5,2,3,7,6,3,0,4,7])
                    UsdPhysics.CollisionAPI.Apply(shape.GetPrim())
                    UsdPhysics.MeshCollisionAPI.Apply(shape.GetPrim()).CreateApproximationAttr('convexHull')
                    collision=PhysxSchema.PhysxCollisionAPI.Apply(shape.GetPrim())
                    collision.CreateContactOffsetAttr(.0003);collision.CreateRestOffsetAttr(0.)
                    collision.CreateTorsionalPatchRadiusAttr(.003);collision.CreateMinTorsionalPatchRadiusAttr(.001)
                    bind_physics_material(str(shape.GetPath()),physics_path,stage=stage)
                    bind_visual_material(str(shape.GetPath()),visual_path,stage=stage)
            return prim

        config.spawn.make_uninstanceable = True
        config.spawn.func = spawn
        return config

    covered_config._task_pad_covers = True
    embodiment.yam_arm_cfg = covered_config
