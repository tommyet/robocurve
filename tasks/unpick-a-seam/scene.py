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

SCENE='station'
FABRIC=Fabric(thickness=.0004,density=350.,youngs_modulus=2e6,bend_modulus=8e4,
              contact_offset=.00025,rest_offset=.0002,solver_iterations=64)
MESHES=[patch(True),patch(False)]
OBJECTS=[
    Cloth('cloth_left',pos=(0.,0.,0.),size=(.13,.08,.004),mesh=MESHES[0],initial=MESHES[0].rest,
          fabric=FABRIC,color=(.76,.68,.47)),
    Cloth('cloth_right',pos=(0.,0.,0.),size=(.13,.08,.004),mesh=MESHES[1],initial=MESHES[1].rest,
          fabric=FABRIC,color=(.25,.42,.66)),
    *[Thread(f'stitch_{i}',pos=(0.,0.,0.),size=(.011,.0004,.003),nodes=stitch_loop(y)) for i,y in enumerate(STITCH_Y)],
    Box('ripper_handle',pos=(.20,-.12,TABLE_TOP+.008),size=(.070,.012,.012),mass=.018,color=(.2,.45,.25)),
    Box('ripper_blade',pos=(.25,-.12,TABLE_TOP+.008),size=(.001,.004,.0005),mass=.001,color=(.7,.72,.74)),
]

ROOTS={}
original_task_object=adapter.task_object


def task_object(spec):
    obj=original_task_object(spec)
    if spec.name not in ('ripper_handle','ripper_blade'):return obj
    spawn=obj.spawner_cfg.func
    def physical_spawn(prim_path,cfg,*a,**kw):
        import omni.usd
        from pxr import Gf,Sdf,UsdGeom,UsdPhysics
        stage=omni.usd.get_context().get_stage()
        ROOTS[spec.name]=str(prim_path)
        prim=spawn(prim_path,cfg,*a,**kw)
        if spec.name=='ripper_handle':return prim
        h,b=ROOTS['ripper_handle'],ROOTS['ripper_blade']
        joint=UsdPhysics.FixedJoint.Define(stage,h+'/BladeMount')
        joint.CreateBody0Rel().SetTargets([Sdf.Path(h)])
        joint.CreateBody1Rel().SetTargets([Sdf.Path(b)])
        joint.CreateLocalPos0Attr(Gf.Vec3f(.05,0.,0.));joint.CreateLocalPos1Attr(Gf.Vec3f(0.))
        # A long point and a shorter protected point flank the actual cutting
        # edge. They are ordinary child colliders of the handle rigid body.
        for i,(y,length) in enumerate(((-.0026,.014),(.0026,.009))):
            guard=UsdGeom.Capsule.Define(stage,h+f'/Guard{i}')
            guard.CreateAxisAttr('X');guard.CreateRadiusAttr(.0005);guard.CreateHeightAttr(length)
            guard.AddTranslateOp().Set(Gf.Vec3d(.048+length/2,y,0.))
            guard.CreateDisplayColorAttr([Gf.Vec3f(.7,.72,.74)])
            UsdPhysics.CollisionAPI.Apply(guard.GetPrim())
        return prim
    obj.spawner_cfg.func=physical_spawn
    obj.object_cfg.spawn.func=physical_spawn
    return obj


adapter.task_object=task_object
SCORE_OVER='end'
def score(objects):return 0.
def success(objects):return False
