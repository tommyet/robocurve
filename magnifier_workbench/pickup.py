"""Bounded physical pickup pilot. Uses robot joint commands and contact only.

Counterfactual baseline images are rendered after the episode with physics
frozen. They are evaluation evidence, never a policy observation during control.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import numpy as np
from probe import array, author_card


def review_camera(embodiment):
    import isaaclab.sim as sim_utils
    from isaaclab.sensors import CameraCfg
    from isaaclab_arena.utils.cameras import ArenaCameraCfg
    from isaaclab_arena.utils.configclass import make_configclass
    from pxr import Gf
    from yam_arena.embodiment import RENDERER
    q = Gf.Matrix4d().SetLookAt(Gf.Vec3d(.85,-.90,1.65),
                               Gf.Vec3d(.30,0.,.87),Gf.Vec3d(0,0,1)).GetInverse().ExtractRotationQuat()
    config=CameraCfg(prim_path="{ENV_REGEX_NS}/MagnifierReviewCam",height=720,width=960,
        data_types=["rgb"],spawn=sim_utils.PinholeCameraCfg(focal_length=20.,horizontal_aperture=20.955,
            clipping_range=(.01,20.)),offset=CameraCfg.OffsetCfg(pos=(.85,-.90,1.65),
            rot=(*q.GetImaginary(),q.GetReal()),convention="opengl"),renderer_cfg=RENDERER)
    fields=[(name,CameraCfg,value) for name,value in vars(embodiment.camera_config).items()
            if isinstance(value,CameraCfg)]
    fields.append(("review_cam",CameraCfg,config))
    embodiment.camera_config=make_configclass("MagnifierReviewCameraCfg",fields,bases=(ArenaCameraCfg,))()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--target-dir",type=Path,required=True)
    parser.add_argument("--plan",type=Path,required=True)
    parser.add_argument("--align-steps",type=int,default=60)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    source=Path(__file__).resolve().parent
    plan=json.loads(args.plan.read_text())
    record={"scope":"Physical scripted pilot; no Dream inference.",
            "source_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source.glob("*.py")},
            "plan_sha256":hashlib.sha256(args.plan.read_bytes()).hexdigest(),"complete":False}
    def save():
        record["wall_seconds"]=time.monotonic()-started
        (args.out/"pickup.json").write_text(json.dumps(record,indent=2)+"\n")
    save()
    os.environ.setdefault("OMNI_KIT_ACCEPT_EULA","YES")
    from isaaclab.app import AppLauncher
    app=AppLauncher(headless=True,enable_cameras=True).app
    video=None; wrist_video=None; trace=None
    try:
        import carb, cv2, omni.usd, torch
        import imageio.v2 as imageio
        from PIL import Image
        from pxr import UsdGeom, UsdPhysics, Usd
        from isaaclab_physx.renderers import IsaacRtxRendererCfg,IsaacRtxRendererGlobalSettingsCfg
        from yam_arena import embodiment as env_module, inspect_embodiment as wrapper, scene
        from yam_arena.analysis import pose7_to_matrix
        from yam_arena.urdf import quat_xyzw_to_matrix
        from tool import attach_tool
        settings=carb.settings.get_settings()
        settings.set_bool("/isaaclab/render/deterministic",False)
        overrides={"/rtx/rendermode":"RealTimePathTracing","/rtx/rtpt/maxBounces":6,
                   "/rtx/rtpt/maxSpecularAndTransmissionBounces":6,
                   "/rtx/translucency/enabled":True,"/rtx/translucency/maxRefractionBounces":6}
        env_module.RENDERER=IsaacRtxRendererCfg(global_settings=IsaacRtxRendererGlobalSettingsCfg(
            ambient_light_intensity=0.,antialiasing_mode=None,enable_dlssg=False,carb_settings=overrides))
        wrapper._APP=app
        original_object=scene.task_object; original_env=scene.make_env
        def task_object(spec):
            obj=original_object(spec)
            if spec.name=="magnifier":
                spawn=obj.spawner_cfg.func
                def physical_spawn(prim_path,cfg,*a,**kw):
                    prim=spawn(prim_path,cfg,*a,**kw)
                    record["tool"]=attach_tool(omni.usd.get_context().get_stage(),str(prim.GetPath()))
                    record["tool_root_path"]=str(prim.GetPath())
                    return prim
                obj.spawner_cfg.func=physical_spawn
                # Object.__init__ already built a copied RigidObjectCfg.
                obj.object_cfg.spawn.func=physical_spawn
            return obj
        def make_env(embodiment,**kw):
            review_camera(embodiment)
            return original_env(embodiment,**kw)
        scene.task_object=task_object;scene.make_env=make_env
        emb=wrapper.YamArenaEmbodiment(task=str(source/"pickup_scene.py"),object_jitter=0.,control_hz=20.)
        try:emb._ensure_sim(None)
        finally:scene.task_object=original_object;scene.make_env=original_env
        base=emb._base
        stage=omni.usd.get_context().get_stage()
        author_card(stage,"/World/InspectionPrint",args.target_dir/"target.png",.120,.100,
                    (.35,.05,.7551),np.diag([-1.,-1.,1.]))
        emb._instruction="Pick up the magnifying glass and hold it above the printed target so the left wrist camera sees the fine lines enlarged and clearly."
        emb._env.reset()
        for _ in range(10):emb._env.step(emb._ready)
        root=stage.GetPrimAtPath(record["tool_root_path"])
        record["rigid_bodies"]=[str(p.GetPath()) for p in Usd.PrimRange(root) if p.HasAPI(UsdPhysics.RigidBodyAPI)]
        record["joints_in_tool"]=[str(p.GetPath()) for p in Usd.PrimRange(root) if p.IsA(UsdPhysics.Joint)]
        assert len(record["rigid_bodies"])==1 and not record["joints_in_tool"]
        record["renderer_settings"]={k:settings.get(k) for k in overrides}
        assert settings.get("/rtx/rendermode")=="RealTimePathTracing"
        assert np.allclose(array(base.arena_world.get_pose_w("magnifier")),
                           array(base.scene["magnifier"].data.root_pose_w))
        video=imageio.get_writer(args.out/"demo.mp4",fps=20,codec="libx264",pixelformat="yuv420p",
                                 ffmpeg_params=["-movflags","+faststart"],macro_block_size=1)
        wrist_video=imageio.get_writer(args.out/"wrist.mp4",fps=20,codec="libx264",pixelformat="yuv420p",
                                 ffmpeg_params=["-movflags","+faststart"],macro_block_size=1)
        trace=(args.out/"trace.jsonl").open("w")
        def snapshot(step,phase,action):
            pose=array(base.arena_world.get_pose_w("magnifier"))[0].tolist()
            robots={name:array(base.scene[name].data.joint_pos)[0].tolist() for name in ("left_robot","right_robot")}
            g=pose7_to_matrix(array(base.scene["left_robot"].data.body_link_pose_w)[0,
                base.scene["left_robot"].body_names.index("gripper")])
            c=emb.rig.wrist_cams["left"]
            r=g[:3,:3]@quat_xyzw_to_matrix(np.asarray(c.rot_xyzw))
            eye=g[:3,:3]@np.asarray(c.pos)+g[:3,3]
            state={"step":step,"time_s":step/20,"phase":phase,"action":action,
                "tool_pose_xyzw":pose,"joints":robots,"camera_eye":eye.tolist(),"camera_rotation":r.tolist()}
            trace.write(json.dumps(state)+"\n");trace.flush()
            review=array(base.scene["review_cam"].data.output["rgb"])[0,:,:,:3].astype(np.uint8)
            video.append_data(review)
            wrist=emb._observation().images["left_cam"]
            wrist_video.append_data(wrist)
            if step==0:Image.fromarray(review).save(args.out/"setup.png")
            return state
        snapshot(0,"settled",emb._ready[0].cpu().tolist())
        actions=plan["frames"][1:]
        for i,frame in enumerate(actions,1):
            action=frame["action14"]
            emb._env.step(torch.tensor([action],device=base.device,dtype=torch.float32))
            state=snapshot(i,frame["phase"],action)
            if i%20==0:
                print(json.dumps({"step":i,"phase":frame["phase"],"tool_pose":state["tool_pose_xyzw"]}),flush=True)
            if i%5==0 and i>=len(actions)-60:
                raw=array(base.scene["left_cam"].data.output["rgb"])[0,:,:,:3].astype(np.uint8)
                policy=emb._observation().images["left_cam"]
                assert np.array_equal(policy,cv2.resize(raw,(224,224)))
                Image.fromarray(raw).save(args.out/f"hold-{i:04d}-raw.png")
                Image.fromarray(policy).save(args.out/f"hold-{i:04d}-policy.png")
        if args.align_steps:
            from align import action14
            # Five seconds stationary: allow settling, then audit the final three.
            for j in range(args.align_steps+100):
                if j<args.align_steps:
                    action=action14(action,state["tool_pose_xyzw"])
                i+=1
                emb._env.step(torch.tensor([action],device=base.device,dtype=torch.float32))
                state=snapshot(i,"centre measured lens" if j<args.align_steps else "hold centred view",action)
                if j%20==0:print(json.dumps({"step":i,"phase":state["phase"],"tool_pose":state["tool_pose_xyzw"]}),flush=True)
                if j>=args.align_steps-1:
                    raw=array(base.scene["left_cam"].data.output["rgb"])[0,:,:,:3].astype(np.uint8)
                    policy=emb._observation().images["left_cam"]
                    assert np.array_equal(policy,cv2.resize(raw,(224,224)))
                    Image.fromarray(raw).save(args.out/f"hold-{i:04d}-raw.png")
                    Image.fromarray(policy).save(args.out/f"hold-{i:04d}-policy.png")
        video.close();video=None
        wrist_video.close();wrist_video=None
        Image.fromarray(array(base.scene["review_cam"].data.output["rgb"])[0,:,:,:3].astype(np.uint8)).save(args.out/"final-review.png")
        # Controlled optical comparison at identical final actual robot/camera pose.
        physics_before=base.sim._physics_step_count
        joint_before=array(base.scene["left_robot"].data.joint_pos).copy()
        lens=stage.GetPrimAtPath(record["tool_root_path"]+"/MagnifierHead/Lens")
        for label,visible in [("final",True),("baseline",False)]:
            (UsdGeom.Imageable(lens).MakeVisible if visible else UsdGeom.Imageable(lens).MakeInvisible)()
            for _ in range(32):
                base.sim.render();base.scene["left_cam"].update(.05,force_recompute=True)
            raw=array(base.scene["left_cam"].data.output["rgb"])[0,:,:,:3].astype(np.uint8)
            policy=emb._observation().images["left_cam"]
            assert np.array_equal(policy,cv2.resize(raw,(224,224)))
            assert base.sim._physics_step_count==physics_before
            assert np.array_equal(joint_before,array(base.scene["left_robot"].data.joint_pos))
            Image.fromarray(raw).save(args.out/(label+"-raw.png"))
            Image.fromarray(policy).save(args.out/(label+"-policy.png"))
            np.savez_compressed(args.out/(label+".npz"),raw=raw,policy=policy)
        UsdGeom.Imageable(lens).MakeVisible()
        record.update(complete=True,steps=i,final_state=state,
                      optical_comparison={"same_camera_pose":True,"same_physics_step":physics_before,
                          "counterfactual":"Only glass hidden after control; frame and handle remain.",
                          "actual_policy_resize_verified":True})
        save()
    except BaseException as error:
        record["error"]=type(error).__name__+": "+str(error);save();raise
    finally:
        if video is not None:video.close()
        if wrist_video is not None:wrist_video.close()
        if trace is not None:trace.close()
        app.close()


if __name__=="__main__":main()
