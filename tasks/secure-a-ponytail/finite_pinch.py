"""Geometry-gated native vertex pinch, with an approximate elastic-tension slip guard.

The actual closing fingers must enclose the 3 mm cord. A native attachment then
binds that measured cord point to the real gripper link. Opening, estimated load
above 6 N, or 8 mm slip releases it. No task-body or material pose is assigned.
The tension estimate is uncalibrated; it is not a measured native force limit.
"""
import numpy as np


def candidate(point,radius,hand,thickness,half_width,z_range):
 local=(np.asarray(point)-hand['tcp'])@hand['rotation']
 q=np.asarray(hand.get('finger_joint_positions',[-hand['opening']*.04695]*2))
 left=q[0]+thickness;right=-q[1]-thickness
 if abs((local[0]-radius)-left)>.001 or abs((local[0]+radius)-right)>.001:return None
 if abs(local[1])>half_width or not z_range[0]<=local[2]<=z_range[1]:return None
 return float(np.linalg.norm(local))


class FinitePinch:
 def __init__(self,model,names,radius,thickness,half_width,z_range):
  from pxr import UsdPhysics
  self.m=model;self.names=list(names);self.radius=radius;self.thickness=thickness
  self.half_width=half_width;self.z_range=z_range;self.held={};self.history={s:[] for s in ['left','right']};self.blocked=set();self.serial=0
  self.grippers={};self.hand_bodies={s:[] for s in ["left","right"]};root=None
  for p in model.stage.Traverse():
   path=str(p.GetPath())
   if p.HasAPI(UsdPhysics.RigidBodyAPI) and p.GetName()=='gripper':
    for side,arm in [('left','LeftArm'),('right','RightArm')]:
     if arm in path:self.grippers[side]=path
   if p.HasAPI(UsdPhysics.RigidBodyAPI) and p.GetName() in ('gripper','tip_left','tip_right'):
    for side,arm in [('left','LeftArm'),('right','RightArm')]:
     if arm in path:self.hand_bodies[side].append(path)
   if '/materials/' in path and p.GetName()=='elastic':root=path.rsplit('/',1)[0]
  assert set(self.grippers)=={'left','right'} and root is not None
  self.root=root
 def release(self,side,reason):
  g=self.held.pop(side);g['attachment'].GetAttribute('omniphysics:attachmentEnabled').Set(False)
  for f in g['filters']:f.GetAttribute('omniphysics:filterEnabled').Set(False)
  g['patch_pairs'].SetTargets(g['old_patch_pairs'])
  self.m.events.append(dict(event='pinch_released' if reason=='opened' else 'pinch_slipped',side=side,body=g['body'],time=self.m.time,reason=reason))
  if reason!='opened':self.blocked.add(side)
 def tension(self,index):
  from geometry import M,POINTS
  p=self.m.nodes[M+index];force=np.zeros(3)
  # Two adjacent cord segments supply the local tensile load estimate.
  for j in [(index-1)%M,(index+1)%M]:
   v=self.m.nodes[M+j]-p;length=np.linalg.norm(v);rest=np.linalg.norm(POINTS[M+j]-POINTS[M+index])
   strain=max(0.,length/rest-1.);force+=3e5*np.pi*.0015**2*strain*v/max(length,1e-12)
  return float(np.linalg.norm(force))
 def update(self,hands):
  from pxr import Sdf,Vt,UsdPhysics
  from geometry import M,TRIS
  from yam_arena.constants import TCP_OFFSET
  for side,h in hands.items():
   history=self.history[side];history.append(float(h['opening']));del history[:-8]
   q=np.asarray(h.get('finger_joint_positions',[-h['opening']*.04695]*2));aperture=-q.sum()-2*self.thickness
   if aperture>2*self.radius+.002:
    if side in self.held:self.release(side,'opened')
    if h['opening']>.30:self.blocked.discard(side)
    continue
   if side in self.held:
    g=self.held[side];point=self.m.nodes[M+g['index']];local=(point-h['tcp'])@h['rotation'];g['estimated_load_n']=self.tension(g['index'])
    if g['estimated_load_n']>6.:self.release(side,'estimated local cord tension exceeded 6 N')
    elif np.linalg.norm(local-g['local_point'])>.008:self.release(side,'material moved 8 mm through the grip')
   if side in self.held or side in self.blocked or max(history)-h['opening']<.008:continue
   used={g['body'] for g in self.held.values()};choices=[]
   for name in self.names:
    if name in used:continue
    index=int(name.rsplit('_',1)[1]);point=self.m.nodes[M+index]
    distance=candidate(point,self.radius,h,self.thickness,self.half_width,self.z_range)
    if distance is not None:choices.append((distance,name,index,point.copy()))
   if not choices:continue
   _,name,index,point=min(choices,key=lambda x:x[0]);self.serial+=1
   a=self.m.stage.DefinePrim(self.root+f'/finger_pinch_{side}_{self.serial}','OmniPhysicsVtxXformAttachment')
   a.GetAttribute('omniphysics:attachmentEnabled').Set(False)
   local=(point-h['tcp'])@h['rotation']
   with Sdf.ChangeBlock():
    a.GetRelationship('omniphysics:src0').SetTargets([Sdf.Path(self.root+'/elastic')])
    a.GetRelationship('omniphysics:src1').SetTargets([Sdf.Path(self.grippers[side])])
    a.GetAttribute('omniphysics:vtxIndicesSrc0').Set([M+index])
    a.GetAttribute('omniphysics:localPositionsSrc1').Set(Vt.Vec3fArray([(local+np.asarray(TCP_OFFSET)).astype(np.float32).tolist()]))
    a.GetAttribute('omniphysics:attachmentEnabled').Set(True)
   # The pinch attachment represents local friction. Avoid contradictory
   # collision constraints only at this held mesh patch, as PhysX recommends.
   triangles=np.flatnonzero(np.any(TRIS==M+index,axis=1)).tolist();filters=[]
   for n,hand_path in enumerate(self.hand_bodies[side]):
    f=self.m.stage.DefinePrim(self.root+f'/pinch_filter_{side}_{self.serial}_{n}','OmniPhysicsElementCollisionFilter')
    f.GetAttribute('omniphysics:filterEnabled').Set(False)
    with Sdf.ChangeBlock():
     f.GetRelationship('omniphysics:src0').SetTargets([Sdf.Path(self.root+'/elastic')])
     f.GetRelationship('omniphysics:src1').SetTargets([Sdf.Path(hand_path)])
     f.GetAttribute('omniphysics:groupElemCounts0').Set([len(triangles)])
     f.GetAttribute('omniphysics:groupElemIndices0').Set(triangles)
     f.GetAttribute('omniphysics:groupElemCounts1').Set([0])
     f.GetAttribute('omniphysics:groupElemIndices1').Set([])
     f.GetAttribute('omniphysics:filterEnabled').Set(True)
    filters.append(f)
   patch=self.m.stage.GetPrimAtPath(self.root+'/'+name)
   pairs=UsdPhysics.FilteredPairsAPI.Apply(patch).CreateFilteredPairsRel();old_pairs=pairs.GetTargets()
   pairs.SetTargets(old_pairs+[Sdf.Path(p) for p in self.hand_bodies[side]])
   self.held[side]=dict(body=name,index=index,attachment=a,local_point=local.copy(),estimated_load_n=0.,filters=filters,patch_pairs=pairs,old_patch_pairs=old_pairs)
   self.m.events.append(dict(event='pinch_captured',side=side,body=name,time=self.m.time,slip_estimate_limit_n=6.,source='native vertex attachment to actual gripper link'))
  self.m.grasp_state={side:dict(body=g['body'],estimated_load_n=g['estimated_load_n'],slip_estimate_limit_n=6.) for side,g in self.held.items()}
