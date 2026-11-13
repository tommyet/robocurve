"""YAM scene preview for contact validation; no task demo has been validated.

All task objects are native dynamic bodies/surfaces. The preview score is zero
because released-stitch inspection and robot evidence are not integrated yet.
"""
from yam_arena.task_file import Box
from yam_arena import scene as adapter
from geometry import TABLE_TOP,patch,stitch_loop,STITCH_Y
from arena_cloth import Cloth
from arena_thread import Thread
from native_cloth import Fabric
from native_cloth import ensure_gpu_scene
from runtime_config import CONFIG
from tool_geometry import HANDLE_SIZE,BLADE_SIZE,BLADE_OFFSET,METAL_PARTS,GUARDS

SCENE='station'
FABRIC=Fabric(thickness=.0004,density=350.,youngs_modulus=2e6,bend_modulus=8e4,
              contact_offset=.00025,rest_offset=.0002,solver_iterations=64)
if CONFIG.quality_mesh:
    if abs(CONFIG.hole_half_m-.0008)>1e-12 or CONFIG.hole_mesh_spacing_m is not None:
        raise ValueError('Quality mesh requires the fixed 1.6 mm hole diagnostic')
    from quality_mesh import quality_patch
    MESHES=[quality_patch(left) for left in (True,False)]
else:
    MESHES=[patch(left,hole_half=CONFIG.hole_half_m,hole_mesh_spacing=CONFIG.hole_mesh_spacing_m)
            for left in (True,False)]
# A resting-reset diagnostic translates both patches and every thread equally.
# Intrinsic rest shape is unchanged; no vertex is attached or moved at runtime.
# The lowest spherical/capsule surface is tangent to the physical tabletop.
if CONFIG.seam_lowering_m not in (0.,.0024-CONFIG.thread_radius_m):
    raise ValueError('Unsupported seam reset height')
for mesh in MESHES:mesh.rest[:,2]-=CONFIG.seam_lowering_m
if CONFIG.sewing_clamp:
    if (CONFIG.pre_draped_seam or CONFIG.seam_lowering_m!=0. or
            abs(CONFIG.thread_radius_m-.0004)>1e-12 or
            (not CONFIG.quality_mesh and CONFIG.hole_mesh_spacing_m!=.0004)):
        raise ValueError('Sewing clamp requires coarse thread and locally refined or graded hole mesh')
    from clamp_layout import transform
    for mesh in MESHES:mesh.rest=transform(mesh.rest)
if CONFIG.pre_draped_seam:
    if (not CONFIG.quality_mesh or abs(CONFIG.thread_radius_m-.0004)>1e-12 or
            abs(CONFIG.seam_lowering_m-.002)>1e-12):
        raise ValueError('Pre-drape requires the quality mesh and coarse resting thread')
    from draped_reset import initial_drape,cylindrical_drape
    if CONFIG.drape_shape not in ('gaussian','cylindrical'):raise ValueError('Unknown initial drape')
    drape=initial_drape if CONFIG.drape_shape=='gaussian' else cylindrical_drape
    INITIAL=[drape(mesh,upper) for mesh,upper in zip(MESHES,(True,False))]
else:
    INITIAL=[mesh.rest.copy() for mesh in MESHES]

def thread_nodes(y):
    nodes=stitch_loop(y);nodes[:,2]-=CONFIG.seam_lowering_m
    if CONFIG.sewing_clamp:
        from clamp_layout import transform
        nodes=transform(nodes)
    return nodes

FIXTURE=[]
if CONFIG.passive_clamp and not CONFIG.sewing_clamp:
    raise ValueError('Passive jaw requires the sewing-clamp layout')
if CONFIG.sewing_clamp:
    if CONFIG.passive_clamp:
        from passive_clamp import fixture_boxes,MOVING_NAME,PARAMETERS
    else:
        from clamp_layout import fixture_boxes
    FIXTURE=[Box(name,pos=position,size=size,color=(.32,.34,.36),
                 mass=PARAMETERS.mass_kg if CONFIG.passive_clamp and name==MOVING_NAME else None)
             for name,size,position in fixture_boxes()]

OBJECTS=[
    Cloth('cloth_left',pos=(0.,0.,0.),size=(.13,.08,.004),mesh=MESHES[0],initial=INITIAL[0],
          fabric=FABRIC,color=(.76,.68,.47),contact_refinement=CONFIG.contact_refinement),
    Cloth('cloth_right',pos=(0.,0.,0.),size=(.13,.08,.004),mesh=MESHES[1],initial=INITIAL[1],
          fabric=FABRIC,color=(.25,.42,.66),contact_refinement=CONFIG.contact_refinement),
    *[Thread(f'stitch_{i}',pos=(0.,0.,0.),size=(.011,2*CONFIG.thread_radius_m,.003),
             nodes=thread_nodes(y),radius_m=CONFIG.thread_radius_m) for i,y in enumerate(STITCH_Y)],
    *FIXTURE,
    Box('ripper_handle',pos=(.20,-.12,TABLE_TOP+.008),size=HANDLE_SIZE,mass=.018,color=(.2,.45,.25)),
    Box('ripper_blade',pos=(.25,-.12,TABLE_TOP+.008),size=BLADE_SIZE,mass=.001,color=(.7,.72,.74)),
]

ROOTS={}
original_task_object=adapter.task_object


def task_object(spec):
    obj=original_task_object(spec)
    fixture=spec.name.startswith('clamp_')
    if not fixture and spec.name not in ('ripper_handle','ripper_blade'):return obj
    spawn=obj.spawner_cfg.func
    def physical_spawn(prim_path,cfg,*a,**kw):
        import omni.usd
        from pxr import Gf,Sdf,UsdGeom,UsdPhysics,UsdShade,PhysxSchema
        stage=omni.usd.get_context().get_stage()
        ROOTS[spec.name]=str(prim_path)
        prim=spawn(prim_path,cfg,*a,**kw)
        if fixture:
            mat=UsdShade.Material.Define(stage,str(prim_path)+'/ClampContact')
            material=UsdPhysics.MaterialAPI.Apply(mat.GetPrim())
            material.CreateStaticFrictionAttr(.8);material.CreateDynamicFrictionAttr(.8)
            material.CreateRestitutionAttr(0.)
            for child in stage.Traverse():
                path=str(child.GetPath())
                if (path==str(prim_path) or path.startswith(str(prim_path)+'/')) and child.HasAPI(UsdPhysics.CollisionAPI):
                    collision=PhysxSchema.PhysxCollisionAPI.Apply(child)
                    collision.CreateContactOffsetAttr(.0005);collision.CreateRestOffsetAttr(0.)
                    UsdShade.MaterialBindingAPI.Apply(child).Bind(mat,UsdShade.Tokens.weakerThanDescendants,'physics')
            if CONFIG.passive_clamp and spec.name==MOVING_NAME:
                from passive_clamp import author_guide
                author_guide(stage,str(prim_path),spec.pos)
            return prim
        if spec.name=='ripper_handle':return prim
        # Tensor contact forces require contact reporting before simulation
        # starts. Enable it on the actual blade body, never infer contact from
        # the handle/TCP distance.
        PhysxSchema.PhysxContactReportAPI.Apply(prim).CreateThresholdAttr(0.)
        # The generic box adapter uses millimetre-scale offsets intended for
        # household objects. The cutting edge needs its own thin-tool contact
        # envelope; this changes collision authoring, never object poses.
        for child in stage.Traverse():
            if str(child.GetPath()).startswith(str(prim_path)+'/') and child.HasAPI(UsdPhysics.CollisionAPI):
                api=PhysxSchema.PhysxCollisionAPI.Apply(child)
                api.CreateContactOffsetAttr(.00005);api.CreateRestOffsetAttr(0.)
        h,b=ROOTS['ripper_handle'],ROOTS['ripper_blade']
        joint=UsdPhysics.FixedJoint.Define(stage,h+'/BladeMount')
        joint.CreateBody0Rel().SetTargets([Sdf.Path(h)])
        joint.CreateBody1Rel().SetTargets([Sdf.Path(b)])
        joint.CreateLocalPos0Attr(Gf.Vec3f(*BLADE_OFFSET));joint.CreateLocalPos1Attr(Gf.Vec3f(0.))
        # Ordinary metal shank and fork root connect the handle to the edge.
        # All remain handle colliders; only the separate blade reports cutting
        # forces, so pushing with a guard/shank cannot sever thread.
        for label,size,position in METAL_PARTS:
            metal=UsdGeom.Cube.Define(stage,h+'/'+label)
            metal.CreateSizeAttr(1.)
            metal.AddTranslateOp().Set(Gf.Vec3d(*position))
            metal.AddScaleOp().Set(Gf.Vec3d(*size))
            metal.CreateDisplayColorAttr([Gf.Vec3f(.7,.72,.74)])
            UsdPhysics.CollisionAPI.Apply(metal.GetPrim())
            collision=PhysxSchema.PhysxCollisionAPI.Apply(metal.GetPrim())
            collision.CreateContactOffsetAttr(.00005);collision.CreateRestOffsetAttr(0.)
        # A long point and a shorter protected point flank the actual cutting
        # edge. They are ordinary child colliders of the handle rigid body.
        for i,(start,length,z,radius) in enumerate(GUARDS):
            guard=UsdGeom.Capsule.Define(stage,h+f'/Guard{i}')
            guard.CreateAxisAttr('X');guard.CreateRadiusAttr(radius);guard.CreateHeightAttr(length)
            guard.AddTranslateOp().Set(Gf.Vec3d(start+length/2,0.,z))
            guard.CreateDisplayColorAttr([Gf.Vec3f(.7,.72,.74)])
            UsdPhysics.CollisionAPI.Apply(guard.GetPrim())
            collision=PhysxSchema.PhysxCollisionAPI.Apply(guard.GetPrim())
            collision.CreateContactOffsetAttr(.00005);collision.CreateRestOffsetAttr(0.)
        return prim
    obj.spawner_cfg.func=physical_spawn
    obj.object_cfg.spawn.func=physical_spawn
    return obj


adapter.task_object=task_object
SCORE_OVER='end'
def score(objects):return 0.
def success(objects):return False
