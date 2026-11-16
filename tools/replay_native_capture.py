"""Diagnostic offline views of exact recorded native actor poses, without FK.

This tool never creates completed-task evidence. It preserves capture timing
and labels previews as partial/unscored offline replay, not native RGB.
"""
import argparse,hashlib,json,math,subprocess
from pathlib import Path
from pxr import Gf,Sdf,Usd,UsdGeom,UsdLux

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(value,message):
 if not value:raise ValueError(message)
def pose_ops(prim):
 require(bool(prim) and not prim.IsInstanceProxy(),'missing/noneditable native actor '+str(prim.GetPath()));x=UsdGeom.Xformable(prim);x.ClearXformOpOrder();x.SetResetXformStack(True);return x.AddTranslateOp(UsdGeom.XformOp.PrecisionDouble,'recorded'),x.AddOrientOp(UsdGeom.XformOp.PrecisionDouble,'recorded')
def build(capture,out,light_scale=1.,top_down=False):
 require(math.isfinite(light_scale) and light_scale>0,'invalid offline light scale')
 capture=Path(capture).resolve();out=Path(out).resolve();meta=json.loads((capture/'capture-manifest.json').read_text());scene=capture/meta['scene_file'];require(scene.parent==capture,'unsafe scene path');require(digest(scene)==meta['scene_sha256'],'scene hash mismatch');sources=json.loads((capture/'source-sha256.json').read_text());require(sources==meta['source_sha256'],'source manifests disagree')
 for name,sha in sources.items():require(Path(name).name==name and digest(capture/'source'/name)==sha,'source changed '+name)
 require(meta['quaternion_order']=='xyzw' and meta['capture_hz']==20 and meta['interpolated'] is False,'unsupported capture protocol');rows=[json.loads(s) for s in (capture/'trajectory.jsonl').read_text().splitlines()];require(bool(rows),'empty native capture');owners=meta['owners'];samples=[]
 for i,row in enumerate(rows):
  require(abs(row['time']-(i+1)/20)<1e-6,'incomplete post-step20Hz capture');poses=row.get('native_owner_poses',row.get('native_body_world_poses'));require(isinstance(poses,dict) and set(poses)==set(owners),'missing native actor poses')
  for p in poses.values():require(len(p)==7 and all(isinstance(v,(int,float)) and math.isfinite(v) for v in p) and abs(sum(v*v for v in p[3:])-1)<.002,'invalid pose')
  samples.append(poses)
 out.mkdir(parents=True,exist_ok=False);layer=Sdf.Layer.CreateNew(str(out/'replay.usdc'));layer.subLayerPaths=[str(scene)];layer.customLayerData={'label':'DIAGNOSTIC OFFLINE NATIVE-POSE REPLAY','sourceTraceSha256':digest(capture/'trajectory.jsonl'),'noPhysicsOrFK':True};stage=Usd.Stage.Open(layer);stage.SetInterpolationType(Usd.InterpolationTypeHeld);stage.SetFramesPerSecond(20);stage.SetTimeCodesPerSecond(20);stage.SetStartTimeCode(0);stage.SetEndTimeCode(len(rows)-1);operations={p:pose_ops(stage.GetPrimAtPath(p)) for p in owners}
 for i,poses in enumerate(samples):
  for path,p in poses.items():
   t,r=operations[path];t.Set(Gf.Vec3d(*p[:3]),i);r.Set(Gf.Quatd(p[6],Gf.Vec3d(*p[3:6])),i)
 views=meta['virtual_review_views'];optics=views['optics'];cameras={}
 for name,spec in views['views'].items():
  path='/OfflineReview/'+name;cam=UsdGeom.Camera.Define(stage,path);t,r=pose_ops(cam.GetPrim());eye=Gf.Vec3d(*spec['eye_world_m']);target=Gf.Vec3d(*spec['target_world_m']);eye=target+Gf.Vec3d(.025,-.10,.80) if top_down and name=='review_top' else eye;t.Set(eye);r.Set(Gf.Matrix4d().SetLookAt(eye,target,Gf.Vec3d(0,0,1)).GetInverse().ExtractRotationQuat());cam.CreateFocalLengthAttr(optics['focal_length_mm']);horizontal=optics['horizontal_aperture_mm'];cam.CreateHorizontalApertureAttr(horizontal);cam.CreateVerticalApertureAttr(optics['vertical_aperture_mm'] or horizontal*views['height']/views['width']);cam.CreateClippingRangeAttr(Gf.Vec2f(*optics['clipping_range_m']));cameras[name]=path
 if light_scale!=1.:
  for prim in stage.Traverse():
   if prim.HasAPI(UsdLux.LightAPI):
    intensity=UsdLux.LightAPI(prim).GetIntensityAttr();intensity.Set(intensity.Get()*light_scale)
 layer.Save();manifest=dict(virtual_top_down_override=bool(top_down),preview_light_scale=light_scale,appearance='Captured geometry/materials; explicit offline Storm light normalization; not photometric native RGB', diagnostic=True,complete=False,native_rgb=False,trace_sha256=digest(capture/'trajectory.jsonl'),scene_sha256=meta['scene_sha256'],usd_sha256=digest(out/'replay.usdc'),frames=len(rows),fps=20,source_first_time_s=rows[0]['time'],source_last_time_s=rows[-1]['time'],native_owners=len(owners),cameras=cameras,label='PARTIAL/UNSCORED - OFFLINE NATIVE-POSE REPLAY');(out/'replay-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');return manifest

def render(out,label):
 out=Path(out).resolve();meta=json.loads((out/'replay-manifest.json').read_text());require(digest(out/'replay.usdc')==meta['usd_sha256'],'replay changed');paths=[]
 for name,camera in meta['cameras'].items():
  folder=out/name;folder.mkdir(exist_ok=False)
  with (out/(name+'.log')).open('w') as log:subprocess.run(['/usr/bin/usdrecord','--renderer','Storm','--frames',f"0:{meta['frames']-1}",'--imageWidth','480','--camera',camera,str(out/'replay.usdc'),str(folder/'frame-####.#########.png')],check=True,stdout=log,stderr=subprocess.STDOUT)
  images=list(folder.glob('frame-*.png'));require(len(images)==meta['frames'],'incomplete rendered frame count');paths.append(folder)
 from PIL import Image,ImageDraw,ImageFont
 try:font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',16)
 except OSError:font=ImageFont.load_default()
 video=out/'composite-preview.mp4'
 import numpy as np
 encoder=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','960x600','-r','20','-i','pipe:0','-an','-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],stdin=subprocess.PIPE)
 try:
  indexed=[]
  for folder in paths:
   files={int(float(p.stem.removeprefix('frame-'))):p for p in folder.glob('frame-*.png')}
   require(set(files)==set(range(meta['frames'])),'missing or duplicate rendered sample');indexed.append(files)
  for i in range(meta['frames']):
   canvas=Image.new('RGB',(960,600),(20,20,23));draw=ImageDraw.Draw(canvas);draw.text((12,5),label,fill='white',font=font);draw.text((12,26),'PARTIAL / UNSCORED - OFFLINE NATIVE-POSE REPLAY',fill=(255,201,100),font=font)
   for files,xy in zip(indexed,((240,50),(0,320),(480,320))):
    image=Image.open(files[i]).convert('RGB');canvas.paste(image,xy)
   encoder.stdin.write(np.asarray(canvas).tobytes())
 finally:
  encoder.stdin.close()
  if encoder.wait()!=0:raise RuntimeError('preview encoder failed')
 return video
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('capture',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--render',action='store_true');p.add_argument('--top-down',action='store_true');p.add_argument('--preview-light-scale',type=float,default=1.);p.add_argument('--label',default='Diagnostic task preview');a=p.parse_args();print(json.dumps(build(a.capture,a.out,a.preview_light_scale,a.top_down),indent=2),flush=True)
 if a.render:print(render(a.out,a.label),flush=True)
