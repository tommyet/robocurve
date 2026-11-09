"""Render a real refractive lens through the unchanged YAM wrist-camera pipeline.

This is a static optics experiment, not a robot manipulation demonstration.
The target and lens are fixed visual geometry. No Dream calls are made.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import time

import numpy as np


def array(value):
    value = value.torch if hasattr(value, "torch") else value
    return value.detach().cpu().numpy() if hasattr(value, "detach") else np.asarray(value)


def author_card(stage, path, texture, width, height, center, rotation):
    from pxr import Gf, Sdf, UsdGeom, UsdShade
    from yam_arena.ik import matrix_to_quat_xyzw
    mesh = UsdGeom.Mesh.Define(stage, path)
    mesh.CreatePointsAttr([(-width/2,-height/2,0),(width/2,-height/2,0),
                          (width/2,height/2,0),(-width/2,height/2,0)])
    mesh.CreateFaceVertexCountsAttr([4])
    mesh.CreateFaceVertexIndicesAttr([0,1,2,3])
    mesh.CreateSubdivisionSchemeAttr("none")
    mesh.CreateDoubleSidedAttr(True)
    uv = UsdGeom.PrimvarsAPI(mesh).CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray, "vertex")
    uv.Set([(0,0),(1,0),(1,1),(0,1)])
    x = UsdGeom.Xformable(mesh)
    x.AddTranslateOp().Set(Gf.Vec3d(*center))
    q = matrix_to_quat_xyzw(rotation)
    x.AddOrientOp().Set(Gf.Quatf(float(q[3]),Gf.Vec3f(*q[:3])))
    material = UsdShade.Material.Define(stage,path+"/Material")
    shader = UsdShade.Shader.Define(stage,path+"/Material/Surface")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("roughness",Sdf.ValueTypeNames.Float).Set(1.)
    shader.CreateInput("metallic",Sdf.ValueTypeNames.Float).Set(0.)
    reader = UsdShade.Shader.Define(stage,path+"/Material/UV")
    reader.CreateIdAttr("UsdPrimvarReader_float2")
    reader.CreateInput("varname",Sdf.ValueTypeNames.Token).Set("st")
    reader.CreateOutput("result",Sdf.ValueTypeNames.Float2)
    tex = UsdShade.Shader.Define(stage,path+"/Material/Texture")
    tex.CreateIdAttr("UsdUVTexture")
    tex.CreateInput("file",Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath(str(texture.resolve())))
    tex.CreateInput("sourceColorSpace",Sdf.ValueTypeNames.Token).Set("sRGB")
    tex.CreateInput("st",Sdf.ValueTypeNames.Float2).ConnectToSource(reader.ConnectableAPI(),"result")
    tex.CreateOutput("rgb",Sdf.ValueTypeNames.Float3)
    shader.CreateInput("diffuseColor",Sdf.ValueTypeNames.Color3f).ConnectToSource(tex.ConnectableAPI(),"rgb")
    shader.CreateOutput("surface",Sdf.ValueTypeNames.Token)
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(),"surface")
    UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(material)
    return mesh.GetPrim()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--target-dir",type=Path,required=True)
    parser.add_argument("--mode",choices=["RealTimePathTracing","PathTracing","RaytracedLighting"],default="RealTimePathTracing")
    parser.add_argument("--renders",type=int,default=32)
    parser.add_argument("--target-distance",type=float,default=.200)
    parser.add_argument("--lens-distance",type=float,default=.125)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    record={"scope":"Static optical proof only; no manipulation, no paid inference.",
            "arguments":{k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()},"cases":[]}
    source=Path(__file__).resolve().parent
    record["source_sha256"]={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source.glob("*.py")}
    def save():
        record["elapsed_wall_seconds"]=time.monotonic()-started
        (args.out/"probe.json").write_text(json.dumps(record,indent=2)+"\n")
    save()
    os.environ.setdefault("OMNI_KIT_ACCEPT_EULA","YES")
    from isaaclab.app import AppLauncher
    app=AppLauncher(headless=True,enable_cameras=True).app
    try:
        import carb
        import cv2
        import omni.usd
        from PIL import Image
        from pxr import UsdGeom
        from isaaclab_physx.renderers import IsaacRtxRendererCfg, IsaacRtxRendererGlobalSettingsCfg
        from yam_arena import embodiment as env_module
        from yam_arena import inspect_embodiment as wrapper
        from yam_arena.analysis import pose7_to_matrix
        from yam_arena.urdf import quat_xyzw_to_matrix,axis_angle_matrix
        from lens import author_lens,generate_lens

        settings=carb.settings.get_settings()
        settings.set_bool("/isaaclab/render/deterministic",False)
        overrides={"/rtx/rendermode":args.mode,
                   "/rtx/rtpt/maxBounces":6,"/rtx/rtpt/maxSpecularAndTransmissionBounces":6,
                   "/rtx/pathtracing/maxBounces":6,"/rtx/pathtracing/maxSpecularAndTransmissionBounces":6,
                   "/rtx/translucency/enabled":True,"/rtx/translucency/maxRefractionBounces":6}
        env_module.RENDERER=IsaacRtxRendererCfg(global_settings=IsaacRtxRendererGlobalSettingsCfg(
            ambient_light_intensity=0.,antialiasing_mode=None,enable_dlssg=False,carb_settings=overrides))
        wrapper._APP=app
        emb=wrapper.YamArenaEmbodiment(task=str(source/"probe_scene.py"),object_jitter=0.,control_hz=20.)
        emb._ensure_sim(None)
        emb._env.reset()
        for _ in range(10): emb._env.step(emb._ready)
        base=emb._base; cam=base.scene["left_cam"]
        stage=omni.usd.get_context().get_stage()
        g=pose7_to_matrix(array(base.scene["left_robot"].data.body_link_pose_w)[0,
                             base.scene["left_robot"].body_names.index("gripper")])
        c=emb.rig.wrist_cams["left"]
        rotation=g[:3,:3]@quat_xyzw_to_matrix(np.asarray(c.rot_xyzw))
        eye=g[:3,:3]@np.asarray(c.pos)+g[:3,3]
        direction=-rotation[:,2]
        target_center=eye+args.target_distance*direction
        lens_center=eye+args.lens_distance*direction
        target=json.loads((args.target_dir/"target.json").read_text())
        author_card(stage,"/World/OpticalTarget",args.target_dir/"target.png",.120,.100,target_center,rotation)
        lenses={}
        for name,radius,ior in [("lens100",.100,1.5),("lens75",.075,1.5),("null_lens",.100,1.)]:
            lenses[name]=author_lens(stage,"/World/"+name,center=lens_center,rotation_matrix=rotation,
                                     curvature_radius_m=radius,glass_ior=ior)
            UsdGeom.Imageable(lenses[name]).MakeInvisible()
        record.update(camera={"name":"left_cam","eye_m":eye.tolist(),"rotation_opengl":rotation.tolist(),
                              "native_size":[640,360],"policy_size":[224,224],"intrinsics":asdict(c.lens),
                              "prim_path":cam.cfg.prim_path,"cfg":str(cam.cfg)},
                      target_center_m=target_center.tolist(),lens_center_m=lens_center.tolist(),
                      target_sha256=hashlib.sha256((args.target_dir/"target.png").read_bytes()).hexdigest(),
                      target=target,renderer_settings={k:settings.get(k) for k in overrides},
                      versions={k:importlib.metadata.version(k) for k in ["isaaclab","isaacsim","inspect-robots-yam"]})
        save()
        assert settings.get("/rtx/rendermode")==args.mode, "Renderer mode was overridden"
        actions_before=array(base.scene["left_robot"].data.joint_pos).copy()
        physics_before=base.sim._physics_step_count
        cases=[("baseline",None,0),("null_lens","null_lens",0),("aligned100","lens100",0),
               ("tilted100","lens100",35),("aligned75","lens75",0),("baseline_repeat",None,0)]
        for name,lens_name,angle in cases:
            before=time.monotonic()
            for lens in lenses.values(): UsdGeom.Imageable(lens).MakeInvisible()
            if lens_name:
                x=UsdGeom.Xformable(lenses[lens_name])
                from yam_arena.ik import matrix_to_quat_xyzw
                from pxr import Gf
                rr=rotation@axis_angle_matrix(np.array([0.,1.,0.]),np.radians(angle))
                q=matrix_to_quat_xyzw(rr)
                op=next(o for o in x.GetOrderedXformOps() if o.GetOpType()==UsdGeom.XformOp.TypeOrient)
                op.Set(Gf.Quatd(float(q[3]),Gf.Vec3d(*q[:3])))
                UsdGeom.Imageable(lenses[lens_name]).MakeVisible()
            raw=None
            # Rendering only: robot, target and camera poses do not advance.
            for k in range(args.renders):
                base.sim.render()
                cam.update(1/20,force_recompute=True)
                raw=array(cam.data.output["rgb"])[0,:,:,:3].astype(np.uint8)
            assert raw is not None and raw.shape==(360,640,3)
            obs=emb._observation()
            policy=obs.images["left_cam"]
            assert np.array_equal(policy,cv2.resize(raw,(emb.cam_width,emb.cam_height)))
            assert base.sim._physics_step_count==physics_before
            np.savez_compressed(args.out/(name+".npz"),raw=raw,policy=policy)
            Image.fromarray(raw).save(args.out/(name+"-raw.png"))
            Image.fromarray(policy).save(args.out/(name+"-policy.png"))
            entry={"name":name,"lens":lens_name,"tilt_deg":angle,
                   "wall_seconds":time.monotonic()-before,"raw_shape":list(raw.shape),
                   "raw_sha256":hashlib.sha256(raw.tobytes()).hexdigest(),
                   "policy_sha256":hashlib.sha256(policy.tobytes()).hexdigest(),
                   "camera_joint_state_unchanged":bool(np.array_equal(actions_before,array(base.scene["left_robot"].data.joint_pos))),
                   "physics_step_count":physics_before,"actual_wrapper_image_verified":True,
                   "renderer_mode":settings.get("/rtx/rendermode")}
            record["cases"].append(entry);save();print(json.dumps(entry),flush=True)
        record["complete"]=True;save()
        print(json.dumps({"complete":True,"wall_seconds":record["elapsed_wall_seconds"]}),flush=True)
    except BaseException as error:
        record["error"]=type(error).__name__+": "+str(error);save();raise
    finally:
        app.close()


if __name__=="__main__":main()
