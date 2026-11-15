"""Write an explicitly labelled offline USD replay; never run physics or FK."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from pxr import Gf,Sdf,Usd,UsdGeom,UsdLux,Vt

LABEL='OFFLINE PHYSICS REPLAY - NOT NATIVE RTX'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def require(condition,message):
    if not condition:raise ValueError(message)

def vector(value,size):
    require(isinstance(value,(list,tuple)) and len(value)==size and all(isinstance(v,(int,float)) and math.isfinite(v) for v in value),'invalid native vector')
    return value

def quaternion(value,convention='opengl'):
    x,y,z,w=vector(value,4)
    require(abs(math.sqrt(x*x+y*y+z*z+w*w)-1)<.001,'invalid native quaternion norm')
    q=Gf.Quatd(w,Gf.Vec3d(x,y,z))
    if convention=='ros':q=q*Gf.Quatd(0.,Gf.Vec3d(1,0,0))
    elif convention=='world':q=q*Gf.Matrix3d(0,-1,0,0,0,1,-1,0,0).ExtractRotation().GetQuat()
    else:require(convention=='opengl','unknown optical convention')
    return q

def pose_ops(prim,reset):
    require(bool(prim) and not prim.IsInstanceProxy(),'missing or instanced replay owner '+str(prim.GetPath()))
    x=UsdGeom.Xformable(prim);x.ClearXformOpOrder()
    position=x.AddTranslateOp(UsdGeom.XformOp.PrecisionDouble,'nativeReplay')
    rotation=x.AddOrientOp(UsdGeom.XformOp.PrecisionDouble,'nativeReplay')
    x.SetResetXformStack(reset)
    return position,rotation

def load_capture(directory,trace_hash,diagnostic,audit_path=None):
    directory=Path(directory);manifest=json.loads((directory/'replay-manifest.json').read_text())
    trace=directory/'trajectory.jsonl'
    require(sha(trace)==trace_hash,'native pose trace SHA-256 mismatch')
    source=json.loads((directory/'source-sha256.json').read_text())
    require(source==manifest['source_sha256'],'capture source manifests disagree')
    for name,expected in source.items():
        require(Path(name).name==name and sha(directory/'source'/name)==expected,'captured source hash mismatch: '+name)
    require(Path(manifest['scene_file']).name==manifest['scene_file'],'unsafe scene path')
    scene=directory/manifest['scene_file'];require(sha(scene)==manifest['scene_sha256'],'composed scene hash mismatch')
    require(manifest['capture_hz']==20 and manifest['quaternion_order']=='xyzw' and manifest['pose_space']=='simulation_world','unsupported capture pose protocol')
    owners=manifest['owners'];require(len(owners)==21,'capture must contain all 21 native owners')
    rows=[json.loads(line) for line in trace.read_text().splitlines()]
    require(bool(rows),'empty capture')
    for frame,row in enumerate(rows):
        require(abs(row['time']-frame/20)<1e-6,'missing/nonmonotonic 20 Hz capture row')
        require(row['native_pose_quaternion_order']=='xyzw' and set(row['native_body_world_poses'])==set(owners),'missing or extra native pose owner')
        for pose in row['native_body_world_poses'].values():vector(pose,7);quaternion(pose[3:])
        require(len(row['spray_surface_dose'])==len(manifest['surface_cells']) and all(math.isfinite(v) and v>=0 for v in row['spray_surface_dose']),'invalid captured surface dose')
        for point in row['spray_mist_points']:vector(point,3)
    if not diagnostic:
        summary=json.loads((directory/'score-summary.json').read_text())
        audit=json.loads(Path(audit_path or directory/'audit.json').read_text())
        require(summary['score']==1 and rows[-1]['metrics']['score']==1 and not (rows[-1].get('controller') or {}).get('failure'),'capture did not complete the measured task')
        require(audit.get('passed') is True and audit.get('trace_sha256')==trace_hash and audit.get('score')==1 and audit.get('samples')==len(rows) and abs(audit.get('duration',-1)-rows[-1]['time'])<1e-6,'completed capture audit missing or mismatched')
    return manifest,rows,scene

def add_cameras(stage,metadata):
    paths={}
    for name,camera in metadata['cameras'].items():
        parent=camera['parent_body_owner']
        require(parent is None or bool(stage.GetPrimAtPath(parent)),'missing wrist camera parent')
        path=(parent+'/Replay_'+name) if parent else '/ReplayCameras/'+name
        cam=UsdGeom.Camera.Define(stage,path);position,rotation=pose_ops(cam.GetPrim(),parent is None)
        position.Set(Gf.Vec3d(*vector(camera['pos'],3)));rotation.Set(quaternion(camera['rot_xyzw'],camera['convention']))
        k=camera['lens'];w,h=k['width'],k['height'];fx,fy,cx,cy=(k[key] for key in ('fx','fy','cx','cy'))
        require(all(math.isfinite(v) for v in (w,h,fx,fy,cx,cy)) and min(w,h,fx,fy)>0,'invalid optical intrinsics')
        horizontal=20.955;focal=fx*horizontal/w;vertical=focal*h/fy
        cam.CreateFocalLengthAttr(focal);cam.CreateHorizontalApertureAttr(horizontal);cam.CreateVerticalApertureAttr(vertical)
        cam.CreateHorizontalApertureOffsetAttr((w/2-cx)*horizontal/w);cam.CreateVerticalApertureOffsetAttr((cy-h/2)*vertical/h)
        cam.CreateClippingRangeAttr(Gf.Vec2f(.05 if parent is None else .01,20.));paths[name]=path
    return paths

def build_replay(directory,out,trace_hash,diagnostic=False,audit_path=None,preview_light_scale=1.):
    require(math.isfinite(preview_light_scale) and preview_light_scale>0,'invalid preview light scale')
    manifest,rows,scene=load_capture(directory,trace_hash,diagnostic,audit_path)
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    layer=Sdf.Layer.CreateNew(str((out/'replay.usdc').resolve()));layer.subLayerPaths=[str(scene.resolve())]
    layer.customLayerData={'replayLabel':LABEL,'diagnostic':diagnostic,'nativeTraceSha256':trace_hash,'integerSamplesOnly':True,'consumerInterpolation':'held','previewLightScale':preview_light_scale}
    stage=Usd.Stage.Open(layer);stage.SetInterpolationType(Usd.InterpolationTypeHeld)
    stage.SetTimeCodesPerSecond(20);stage.SetFramesPerSecond(20);stage.SetStartTimeCode(0);stage.SetEndTimeCode(len(rows)-1)
    if preview_light_scale!=1.:
        for prim in stage.Traverse():
            if prim.HasAPI(UsdLux.LightAPI):
                intensity=UsdLux.LightAPI(prim).GetIntensityAttr();intensity.Set(intensity.Get()*preview_light_scale)
    operations={path:pose_ops(stage.GetPrimAtPath(path),True) for path in manifest['owners']}
    cameras=add_cameras(stage,manifest['cameras'])
    colors={};attributes={}
    for cell in manifest['surface_cells']:
        index=cell['index'];require(index not in colors,'duplicate surface cell index')
        prim=stage.GetPrimAtPath(cell['prim_path']);require(bool(prim),'missing surface cell')
        attr=prim.GetAttribute('primvars:displayColor');color=attr.Get(Usd.TimeCode.Default())
        require(color is not None and len(color)>0,'missing captured base surface color')
        for value in color:vector(list(value),3)
        interpolation=UsdGeom.Primvar(attr).GetInterpolation()
        require(interpolation in ('constant','uniform'),'unsupported captured color interpolation')
        if interpolation=='uniform':
            require(prim.IsA(UsdGeom.Mesh),'uniform surface colors require captured Mesh topology')
            counts=list(UsdGeom.Mesh(prim).GetFaceVertexCountsAttr().Get())
            require(len(color)==len(counts),'color count does not match captured face topology')
            if 'face_vertex_counts' in cell:require(cell['face_vertex_counts']==counts,'capture face topology metadata mismatch')
        else:require(len(color)==1,'constant color must contain one value')
        if 'display_color_interpolation' in cell:require(cell['display_color_interpolation']==interpolation,'capture color interpolation metadata mismatch')
        attributes[index]=attr;colors[index]=color;attr.Set(color,0)
    mist=UsdGeom.Points(stage.GetPrimAtPath('/World/spray_mist'));require(bool(mist),'missing captured mist prim')
    for frame,row in enumerate(rows):
        for path,pose in row['native_body_world_poses'].items():
            position,rotation=operations[path];position.Set(Gf.Vec3d(*pose[:3]),frame);rotation.Set(quaternion(pose[3:]),frame)
        changed=set()
        for update in row['spray_surface_updates']:
            index=update['index'];require(index in colors and index not in changed,'invalid/duplicate surface update');changed.add(index)
            require(('color' in update)!=('colors' in update),'surface update needs exactly one color protocol')
            values=update['colors'] if 'colors' in update else [update['color']]
            require(isinstance(values,list) and len(values)==len(colors[index]),'surface update color count mismatch')
            color=Vt.Vec3fArray([Gf.Vec3f(*vector(value,3)) for value in values]);attr=attributes[index]
            # USD consumers choose interpolation at runtime. Seed the previous
            # integer sample so even a reopened linear consumer cannot tween
            # colors at any actual captured 20 Hz frame.
            if frame:attr.Set(colors[index],frame-1)
            attr.Set(color,frame);colors[index]=color
        points=Vt.Vec3fArray([Gf.Vec3f(*point) for point in row['spray_mist_points']])
        mist.GetPointsAttr().Set(points,frame);mist.GetWidthsAttr().Set(Vt.FloatArray([.0015]*len(points)),frame)
    layer.Save()
    result=dict(label=LABEL,diagnostic=diagnostic,native_rtx_capture=False,source_scene_sha256=manifest['scene_sha256'],
                trace_sha256=trace_hash,source_sha256=manifest['source_sha256'],frames=len(rows),capture_hz=20,
                first_frame=0,last_frame=len(rows)-1,cameras=cameras,measured_score=rows[-1]['metrics']['score'],
                usd_file='replay.usdc',usd_sha256=sha(out/'replay.usdc'),writer_sha256=sha(__file__),
                interpolation='held in writer; reopened consumers must request held for fractional queries; render exact integer frames only',
                preview_light_scale=preview_light_scale,
                appearance='captured geometry/materials/displayColor/mist; equivalent calibrated pinhole, not photometric RTX equivalence; explicit optional Storm light normalization; mist widths from pinned source 1.5 mm')
    (out/'replay-output-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('capture',type=Path)
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--trace-sha256',required=True)
    parser.add_argument('--audit',type=Path);parser.add_argument('--diagnostic',action='store_true')
    parser.add_argument('--preview-light-scale',type=float,default=1.,help='Explicit offline appearance normalization; 1 preserves native lights')
    args=parser.parse_args();result=build_replay(args.capture,args.out,args.trace_sha256,args.diagnostic,args.audit,args.preview_light_scale)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
