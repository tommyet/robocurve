"""Record genuine native simulator RGB of draft layouts; never task success."""
import argparse,os,json,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('kind',choices=['ethernet','hair','carton-breakdown','carton-packing']);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=False)
os.environ.setdefault('OMNI_KIT_ACCEPT_EULA','YES')
from isaaclab.app import AppLauncher
app=AppLauncher(headless=True,enable_cameras=True).app
try:
 import numpy as np,torch,cv2,imageio.v2 as imageio
 from yam_arena import inspect_embodiment as wrapper
 import scenes
 scenes.build(a.kind)
 # Load generated fixed geometry through the same adapter as actual trials.
 task=a.out/'layout.py'
 task.write_text('from yam_arena.task_file import Box,Cylinder,Sphere\nSCENE="station"\nOBJECTS='+repr(scenes.OBJECTS)+'\ndef success(objects):return False\ndef score(objects):return 0.\n')
 wrapper._APP=app
 env=wrapper.YamArenaEmbodiment(task=str(task.resolve()),object_jitter=0.,control_hz=20,cam_width=320,cam_height=180,headless=True)
 env._ensure_sim(None);env._env.reset();env._instruction='Unscored layout preview';env._t=0.
 base=env._base
 # Review cameras are independent from a model trial; move only cameras.
 target=(.42,0.,1.00) if a.kind=='hair' else ((.43,0.,.88) if a.kind=='ethernet' else (.34,0.,.82))
 eyes=[(.06,-.30,1.30),(.10,.25,1.13),(.10,-.22,1.10)]
 for name,eye in zip(['top_cam','left_cam','right_cam'],eyes):
  base.scene[name].set_world_poses_from_view(torch.tensor([eye],device=base.device),torch.tensor([target],device=base.device))
 if a.kind=='ethernet':
  from pxr import UsdGeom,Gf
  for i in range(8):
   if i==6:continue
   row,col=divmod(i,4);y=(col-1.5)*.032;z=.7475+.11+row*.035
   color=(1.,.39,.03) if i==1 else ((.05,.30,.85) if i%2 else (.09,.60,.34))
   curve=UsdGeom.BasisCurves.Define(base.scene.stage,'/World/preview_cable_'+str(i))
   curve.CreateTypeAttr('linear');curve.CreateCurveVertexCountsAttr([41])
   curve.CreatePointsAttr([Gf.Vec3f(.398-.19*u,y+.018*np.sin(u*np.pi*2+i),z-.075*u) for u in np.linspace(0,1,41)])
   curve.CreateWidthsAttr([.0064]);curve.SetWidthsInterpolation('constant');curve.CreateDisplayColorAttr([Gf.Vec3f(*color)])
 if a.kind=='carton-packing':
  # Replace solid proxy visually with an open annular mesh; no mechanics claim.
  from pxr import UsdGeom,Gf,Usd
  stage=base.scene.stage
  root='/World/envs/env_0/tape_roll_proxy'
  for prim in list(Usd.PrimRange(stage.GetPrimAtPath(root))):
   if prim.IsA(UsdGeom.Gprim):UsdGeom.Imageable(prim).MakeInvisible()
  mesh=UsdGeom.Mesh.Define(stage,'/World/preview_tape_ring')
  points=[];faces=[]
  for z in [.7475,.7955]:
   for r in [.0381,.05]:
    points.extend([(.18+r*np.cos(t),-.19+r*np.sin(t),z) for t in np.linspace(0,2*np.pi,64,endpoint=False)])
  for i in range(64):
   j=(i+1)%64
   faces.extend([[i,j,64+j,64+i],[128+i,192+i,192+j,128+j],[64+i,64+j,192+j,192+i],[i,128+i,128+j,j]])
  mesh.CreatePointsAttr([Gf.Vec3f(*v) for v in points]);mesh.CreateFaceVertexCountsAttr([4]*len(faces));mesh.CreateFaceVertexIndicesAttr([i for f in faces for i in f]);mesh.CreateDisplayColorAttr([Gf.Vec3f(.76,.59,.28)]);mesh.CreateSubdivisionSchemeAttr('none')
 for _ in range(8):base.sim.render()
 def arr(v):
  v=v.torch if hasattr(v,'torch') else v
  return v.detach().cpu().numpy()
 writer=imageio.get_writer(str(a.out/'preview.mp4'),fps=20,codec='libx264',pixelformat='yuv420p',macro_block_size=1,ffmpeg_params=['-movflags','+faststart'])
 try:
  for step in range(160):
   # Hold normal READY joint commands; do not animate object state or fake work.
   env._env.step(env._ready);env._t=step*.05
   panels=[cv2.resize(np.asarray(arr(base.scene[n].data.output['rgb'])[0,:,:,:3],dtype=np.uint8),(480,270)) for n in ['top_cam','left_cam','right_cam']]
   canvas=np.zeros((594,960,3),dtype=np.uint8)
   canvas[36:306,240:720]=panels[0];canvas[306:576,:480]=panels[1];canvas[306:576,480:]=panels[2]
   cv2.putText(canvas,a.kind.upper()+' | DRAFT SCENE PREVIEW',(18,25),cv2.FONT_HERSHEY_SIMPLEX,.65,(255,255,255),1,cv2.LINE_AA)
   cv2.putText(canvas,'Layout only - robot holds still - task mechanics not demonstrated',(18,590),cv2.FONT_HERSHEY_SIMPLEX,.48,(255,205,120),1,cv2.LINE_AA)
   writer.append_data(canvas)
   if step==80:imageio.imwrite(a.out/'setup.png',canvas)
 finally:writer.close()
 (a.out/'result.json').write_text(json.dumps({'kind':a.kind,'purpose':'unscored native draft layout preview','frames':160,'fps':20,'task_completed':False,'robot_policy':'hold READY','fixed_geometry':True},indent=2)+'\n')
finally:app.close()
