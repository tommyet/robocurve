"""Offline USD protocol tests; require usd-core, never initialize physics."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
try:
    from pxr import Usd,UsdGeom,UsdLux,Gf,Vt
except ModuleNotFoundError:
    raise unittest.SkipTest('offline writer tests require the dedicated usd-core environment')
spec=importlib.util.spec_from_file_location('_offline_replay',Path(__file__).with_name('replay_usd.py'))
writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)


class ReplayUsdTests(unittest.TestCase):
    def fixture(self,root):
        root.mkdir();(root/'source').mkdir();(root/'source'/'capture.py').write_text('# captured source\n')
        stage=Usd.Stage.CreateNew(str(root/'replay-scene.usdc'))
        paths=['/World/b0','/World/b0/b1']+[f'/World/b{i}' for i in range(2,21)]
        for path in paths:
            x=UsdGeom.Xform.Define(stage,path);x.AddTranslateOp().Set(Gf.Vec3d(10,0,0))
            child=UsdGeom.Cube.Define(stage,path+'/mesh');child.CreateSizeAttr(.02);child.AddTranslateOp().Set(Gf.Vec3d(.1,0,0))
        cell=UsdGeom.Cube.Define(stage,'/World/cell');cell.CreateDisplayColorAttr([Gf.Vec3f(.95,.95,.95)])
        mist=UsdGeom.Points.Define(stage,'/World/spray_mist');mist.CreatePointsAttr([]);mist.CreateWidthsAttr([])
        UsdLux.DomeLight.Define(stage,'/World/Light').CreateIntensityAttr(250.)
        stage.GetRootLayer().Save()
        camera=dict(parent_body_owner=None,pose_space='world',pos=[0,0,5],rot_xyzw=[0,0,0,1],convention='opengl',
                    lens=dict(fx=320.,fy=300.,cx=310.,cy=170.,width=640,height=360))
        wrist={**camera,'parent_body_owner':paths[0],'pose_space':'parent_body_actor_frame','pos':[.2,0,0]}
        source={'capture.py':writer.sha(root/'source'/'capture.py')}
        manifest=dict(scene_file='replay-scene.usdc',scene_sha256=writer.sha(root/'replay-scene.usdc'),source_sha256=source,
                      capture_hz=20,quaternion_order='xyzw',pose_space='simulation_world',owners={path:{} for path in paths},
                      surface_cells=[dict(index=0,prim_path='/World/cell')],cameras={'cameras':{'top_cam':camera,'left_cam':wrist}})
        (root/'source-sha256.json').write_text(json.dumps(source));(root/'replay-manifest.json').write_text(json.dumps(manifest))
        rows=[]
        for frame in range(3):
            poses={path:[i*.05,0.,0.,0.,0.,0.,1.] for i,path in enumerate(paths)}
            poses[paths[0]][0]=frame;poses[paths[1]][0]=7+frame
            rows.append(dict(time=frame/20,native_pose_quaternion_order='xyzw',native_body_world_poses=poses,
                             spray_surface_dose=[.08 if frame==2 else 0.],spray_mist_points=[[.1,.2,.3]] if frame else [],
                             spray_surface_updates=[dict(index=0,color=[.08,.3,.85])] if frame==2 else [],metrics={'score':0.},controller={'failure':None}))
        self.write_rows(root,rows)
        return manifest,rows,paths

    def write_rows(self,root,rows):
        (root/'trajectory.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in rows))
        return writer.sha(root/'trajectory.jsonl')

    def test_exact_world_samples_reset_parents_and_keep_child_mesh_and_paint(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'input';manifest,rows,paths=self.fixture(root)
            original=writer.sha(root/'replay-scene.usdc')
            result=writer.build_replay(root,Path(directory)/'out',writer.sha(root/'trajectory.jsonl'),True)
            stage=Usd.Stage.Open(str(Path(directory)/'out/replay.usdc'))
            self.assertEqual(stage.GetTimeCodesPerSecond(),20);self.assertEqual(stage.GetEndTimeCode(),2)
            for frame in range(3):
                cache=UsdGeom.XformCache(frame)
                for path in paths:
                    self.assertTrue(UsdGeom.Xformable(stage.GetPrimAtPath(path)).GetResetXformStack())
                    actual=cache.GetLocalToWorldTransform(stage.GetPrimAtPath(path)).ExtractTranslation()
                    self.assertEqual(list(actual),rows[frame]['native_body_world_poses'][path][:3])
                child=cache.GetLocalToWorldTransform(stage.GetPrimAtPath(paths[1]+'/mesh')).ExtractTranslation()
                self.assertAlmostEqual(child[0],7+frame+.1)
            color=stage.GetPrimAtPath('/World/cell').GetAttribute('primvars:displayColor')
            self.assertAlmostEqual(color.Get(0)[0][0],.95,places=6);self.assertAlmostEqual(color.Get(1)[0][0],.95,places=6)
            self.assertAlmostEqual(color.Get(2)[0][0],.08,places=6)
            self.assertEqual(len(UsdGeom.Points(stage.GetPrimAtPath('/World/spray_mist')).GetPointsAttr().Get(0)),0)
            self.assertEqual(len(UsdGeom.Points(stage.GetPrimAtPath('/World/spray_mist')).GetPointsAttr().Get(1)),1)
            self.assertEqual(writer.sha(root/'replay-scene.usdc'),original)
            self.assertTrue(result['diagnostic']);self.assertFalse(result['native_rtx_capture']);self.assertIn('NOT NATIVE RTX',result['label'])

    def test_camera_intrinsics_conventions_and_native_parent(self):
        for convention,forward,up in (('opengl',(0,0,-1),(0,1,0)),('ros',(0,0,1),(0,-1,0)),('world',(1,0,0),(0,0,1))):
            q=writer.quaternion([0,0,0,1],convention)
            self.assertLess((q.Transform(Gf.Vec3d(0,0,-1))-Gf.Vec3d(*forward)).GetLength(),1e-12)
            self.assertLess((q.Transform(Gf.Vec3d(0,1,0))-Gf.Vec3d(*up)).GetLength(),1e-12)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'input';manifest,rows,paths=self.fixture(root)
            result=writer.build_replay(root,Path(directory)/'out',writer.sha(root/'trajectory.jsonl'),True)
            stage=Usd.Stage.Open(str(Path(directory)/'out/replay.usdc'));cam=UsdGeom.Camera(stage.GetPrimAtPath(result['cameras']['top_cam']))
            f=cam.GetFocalLengthAttr().Get();ha=cam.GetHorizontalApertureAttr().Get();va=cam.GetVerticalApertureAttr().Get()
            self.assertAlmostEqual(f/ha*640,320,places=4);self.assertAlmostEqual(f/va*360,300,places=4)
            self.assertAlmostEqual(320-cam.GetHorizontalApertureOffsetAttr().Get()/ha*640,310,places=4)
            self.assertAlmostEqual(180+cam.GetVerticalApertureOffsetAttr().Get()/va*360,170,places=4)
            wrist=stage.GetPrimAtPath(result['cameras']['left_cam'])
            self.assertFalse(UsdGeom.Xformable(wrist).GetResetXformStack())
            self.assertAlmostEqual(UsdGeom.XformCache(2).GetLocalToWorldTransform(wrist).ExtractTranslation()[0],2.2)

    def test_strict_hash_owner_time_and_source_rejection(self):
        for change in ('hash','owner','time','source'):
            with self.subTest(change=change),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)/'input';manifest,rows,paths=self.fixture(root)
                if change=='owner':del rows[1]['native_body_world_poses'][paths[0]]
                if change=='time':rows[1]['time']=.2
                expected=self.write_rows(root,rows)
                if change=='hash':expected='0'*64
                if change=='source':(root/'source/capture.py').write_text('modified')
                with self.assertRaises(ValueError):writer.build_replay(root,Path(directory)/'out',expected,True)

    def test_default_final_label_requires_completed_score_and_matching_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'input';manifest,rows,paths=self.fixture(root)
            (root/'score-summary.json').write_text(json.dumps({'score':0.}))
            (root/'audit.json').write_text(json.dumps({'passed':False}))
            with self.assertRaises(ValueError):writer.build_replay(root,Path(directory)/'bad',writer.sha(root/'trajectory.jsonl'))
            rows[-1]['metrics']['score']=1.;expected=self.write_rows(root,rows)
            (root/'score-summary.json').write_text(json.dumps({'score':1.}))
            (root/'audit.json').write_text(json.dumps({'passed':True,'trace_sha256':'0'*64,'score':1.,'samples':3,'duration':.1}))
            with self.assertRaisesRegex(ValueError,'audit missing or mismatched'):
                writer.build_replay(root,Path(directory)/'wrong-audit',expected)
            (root/'audit.json').write_text(json.dumps({'passed':True,'trace_sha256':expected,'score':1.,'samples':3,'duration':.1}))
            result=writer.build_replay(root,Path(directory)/'valid',expected)
            self.assertFalse(result['diagnostic']);self.assertFalse(result['native_rtx_capture'])

    def test_optional_storm_light_normalization_is_explicit_and_output_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'input';manifest,rows,paths=self.fixture(root)
            result=writer.build_replay(root,Path(directory)/'out',writer.sha(root/'trajectory.jsonl'),True,preview_light_scale=.001)
            output=Usd.Stage.Open(str(Path(directory)/'out/replay.usdc'));original=Usd.Stage.Open(str(root/'replay-scene.usdc'))
            self.assertAlmostEqual(UsdLux.LightAPI(output.GetPrimAtPath('/World/Light')).GetIntensityAttr().Get(),.25)
            self.assertAlmostEqual(UsdLux.LightAPI(original.GetPrimAtPath('/World/Light')).GetIntensityAttr().Get(),250.)
            self.assertEqual(result['preview_light_scale'],.001)
            self.assertEqual(output.GetRootLayer().customLayerData['previewLightScale'],.001)

if __name__=='__main__':unittest.main()
