import importlib.util,json,tempfile,unittest
from pathlib import Path
from pxr import Usd,UsdGeom
spec=importlib.util.spec_from_file_location('replay',Path(__file__).with_name('replay_native_capture.py'));replay=importlib.util.module_from_spec(spec);spec.loader.exec_module(replay)
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.capture=self.root/'capture';self.capture.mkdir();(self.capture/'source').mkdir();(self.capture/'source-sha256.json').write_text('{}');stage=Usd.Stage.CreateNew(str(self.capture/'scene.usdc'));UsdGeom.Xform.Define(stage,'/body');stage.GetRootLayer().Save();meta=dict(scene_file='scene.usdc',scene_sha256=replay.digest(self.capture/'scene.usdc'),source_sha256={},quaternion_order='xyzw',capture_hz=20,interpolated=False,owners={'/body':{}},virtual_review_views={'optics':{},'views':{}});(self.capture/'capture-manifest.json').write_text(json.dumps(meta));self.row=dict(time=.05,native_body_world_poses={'/body':[1,2,3,0,0,0,1]});self.trace=self.capture/'trajectory.jsonl';self.trace.write_text(json.dumps(self.row)+'\n')
 def test_preserves_actual_world_pose_and_discloses_partial(self):
  meta=replay.build(self.capture,self.root/'replay');stage=Usd.Stage.Open(str(self.root/'replay/replay.usdc'));self.assertEqual(tuple(UsdGeom.Xformable(stage.GetPrimAtPath('/body')).ComputeLocalToWorldTransform(0).ExtractTranslation()),(1,2,3));self.assertFalse(meta['complete']);self.assertFalse(meta['native_rgb']);self.assertEqual(meta['source_first_time_s'],.05)
 def test_missing_sample_rejected(self):
  self.row['time']=.10;self.trace.write_text(json.dumps(self.row)+'\n')
  with self.assertRaisesRegex(ValueError,'incomplete post-step'):replay.build(self.capture,self.root/'bad')
 def test_missing_actor_rejected(self):
  self.row['native_body_world_poses']={};self.trace.write_text(json.dumps(self.row)+'\n')
  with self.assertRaisesRegex(ValueError,'missing native actor'):replay.build(self.capture,self.root/'bad')
if __name__=='__main__':unittest.main()
