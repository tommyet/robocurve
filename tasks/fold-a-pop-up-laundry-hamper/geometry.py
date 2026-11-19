"""Native elastic frame, sewn flexible mesh and an attached retaining band.

The four flattened spring frames are aggregated: their bending stiffness and
mass add. Inter-layer slip is omitted. No rest shape changes during the trial.
"""
from geometry_helpers import *
BODIES=[];JOINTS=[]
for side,y in [("left",.305),("right",-.305)]:
 BODIES.append(body(side+"_arm_riser",[0,y,TABLE+.025],[box((.12,.12,.050))],fixed=True,mass=5.,color=(.25,.27,.29)))
CENTER=np.array([.39,0,TABLE+.112]);N=96
# Four short-edge rests support the pickup areas and leave the centre clear.
for sx in [-1,1]:
 for sy in [-1,1]:
  BODIES.append(body(f'folding_rest_{sx+1}_{sy+1}',[.39+sx*.065,sy*.265,TABLE+.050],[box((.020,.020,.100))],mass=.08,fixed=True,color=(.58,.40,.25)))
def rounded_rect(a,b,r=.025):
 pts=[]
 for cx,cy,start in [(a-r,b-r,0),(-a+r,b-r,90),(-a+r,-b+r,180),(a-r,-b+r,270)]:
  for angle in np.linspace(start,start+90,60,endpoint=False):
   t=np.radians(angle);pts.append([cx+r*np.cos(t),cy+r*np.sin(t)])
 p=np.array(pts);p=np.vstack([p,p[0]]);length=np.linalg.norm(np.diff(p,axis=0),axis=1);arc=np.r_[0,np.cumsum(length)];u=(np.linspace(0,arc[-1],N,endpoint=False)-.0304)%arc[-1]
 return np.c_[np.interp(u,arc,p[:,0]),np.interp(u,arc,p[:,1])]
P=rounded_rect(.165,.265);t=np.roll(P,-1,axis=0)-np.roll(P,1,axis=0);t/=np.linalg.norm(t,axis=1)[:,None];inside=np.c_[-t[:,1],t[:,0]]
FRAME_POINTS=np.vstack([np.c_[P+inside*.002,np.full(N,.006)],np.c_[P-inside*.002,np.full(N,.006)]])+CENTER
FRAME_TRIS=[]
for i in range(N):
 j=(i+1)%N;FRAME_TRIS += [[i,j,N+i],[j,N+j,N+i]]
LEVELS=6;CLOTH_POINTS=[CENTER+[0,0,.006]];CLOTH_TRIS=[]
for level in range(1,LEVELS+1):
 for xy in (P+inside*.002)*level/LEVELS:CLOTH_POINTS.append(CENTER+[*xy,.006])
for i in range(N):CLOTH_TRIS.append([0,1+i,1+(i+1)%N])
for level in range(LEVELS-1):
 for i in range(N):
  a=1+level*N+i;b=1+level*N+(i+1)%N;c=a+N;d=b+N;CLOTH_TRIS += [[a,c,d],[a,d,b]]
M=64;radius=.300/(2*np.pi);anchor=FRAME_POINTS[N];out=np.r_[-inside[0],0.];tangent=np.cross([0,0,1],out);centre=anchor+out*(radius+.012)
TAB_POINTS=np.array([anchor,anchor+out*.006+tangent*.002,anchor+out*.012,anchor+out*.006-tangent*.002])
TAB_TRIS=[[0,1,2],[0,2,3]]
BAND_POINTS=[];BAND_TRIS=[]
for r in [radius-.0025,radius,radius+.0025]:
 for i in range(M):
  angle=i*2*np.pi/M;BAND_POINTS.append(centre+r*(out*np.cos(angle)+tangent*np.sin(angle)))
for row in range(2):
 for i in range(M):
  a=row*M+i;b=row*M+(i+1)%M;c=a+M;d=b+M;BAND_TRIS += [[a,b,c],[b,d,c]]
SURFACES=[dict(name='tab',points=TAB_POINTS,tris=TAB_TRIS,mass=.0002,youngs=2e7,poisson=.3,thickness=.0005,friction=.5,rest_offset=.00025,contact_offset=.0006,color=(.13,.29,.44)),
 dict(name='frame',points=FRAME_POINTS,tris=FRAME_TRIS,mass=.041,youngs=8e11,poisson=.3,thickness=.00020,friction=1.2,rest_offset=.0035,contact_offset=.0045,color=(.13,.29,.44)),
 dict(name='cloth',points=CLOTH_POINTS,tris=CLOTH_TRIS,mass=.060,youngs=8e6,poisson=.3,thickness=.0003,friction=.4,rest_offset=.00015,contact_offset=.0007,color=(.28,.47,.62)),
 dict(name='band',points=BAND_POINTS,tris=BAND_TRIS,mass=.004,youngs=4e5,poisson=.45,thickness=.001,friction=1.,rest_offset=.0005,contact_offset=.001,color=(.10,.11,.13))]
for s in SURFACES:
 s['points']=np.asarray(s['points']);s['tris']=np.asarray(s['tris']);s['edges']=np.unique(np.sort(np.concatenate([s['tris'][:,[0,1]],s['tris'][:,[1,2]],s['tris'][:,[2,0]]]),axis=1),axis=0);s['rest_lengths']=np.linalg.norm(s['points'][s['edges'][:,0]]-s['points'][s['edges'][:,1]],axis=1)
# Overlapping capsule ends keep the 7 mm binding continuous at segment joins.
# USD capsule height is its cylinder length, excluding its hemispherical ends.
# They are passive task material, attached to the elastic frame, never to a hand.
HEM_ATTACHMENTS=[]
for i in range(N):
 j=(i+1)%N;a=(FRAME_POINTS[i]+FRAME_POINTS[N+i])/2;b=(FRAME_POINTS[j]+FRAME_POINTS[N+j])/2
 tangent=(b-a)/np.linalg.norm(b-a);orientation=Rotation.align_vectors([tangent],[[0,0,1]])[0];centre=(a+b)/2;name=f'bound_edge_{i:03d}'
 spec=body(name,centre,[dict(kind='capsule',radius=.0035,length=float(np.linalg.norm(b-a)),pos=[0,0,0],quat=[0,0,0,1])],mass=.038/N,quat=orientation.as_quat().tolist(),color=(.13,.29,.44),friction=1.2,contact_offset=.0004,torsional_patch_radius=.004,min_torsional_patch_radius=.002)
 spec['exclude']=['frame','cloth','tab',f'bound_edge_{(i-1)%N:03d}',f'bound_edge_{j:03d}'];BODIES.append(spec)
 ids=[i,j,N+i];local=orientation.inv().apply(FRAME_POINTS[ids]-centre)
 HEM_ATTACHMENTS.append((name,ids,local))
GRIP_INDICES=(11,60);GRIP_BODIES=tuple(f'bound_edge_{i:03d}' for i in GRIP_INDICES)
GRIP_POINTS=np.asarray([next(b['pos'] for b in BODIES if b['name']==name) for name in GRIP_BODIES])
finalize(BODIES,JOINTS)

def spawn_surface(stage,root):
 from pxr import UsdGeom,UsdPhysics,PhysxSchema,UsdShade,Gf,Vt,Sdf
 for s in SURFACES:
  path=root+'/'+s['name'];mesh=UsdGeom.Mesh.Define(stage,path);mesh.CreatePointsAttr(Vt.Vec3fArray(s['points'].astype(np.float32).tolist()));mesh.CreateFaceVertexCountsAttr([3]*len(s['tris']));mesh.CreateFaceVertexIndicesAttr(s['tris'].ravel().tolist());mesh.CreateSubdivisionSchemeAttr('none');mesh.CreateDoubleSidedAttr(True);p=mesh.GetPrim()
  for api in ['OmniPhysicsDeformableBodyAPI','OmniPhysicsSurfaceDeformableSimAPI','PhysxSurfaceDeformableBodyAPI']:
   if not p.ApplyAPI(api):raise RuntimeError('Required native surface API unavailable: '+api)
  p.GetAttribute('omniphysics:mass').Set(s['mass']);p.GetAttribute('omniphysics:restShapePoints').Set(Vt.Vec3fArray(s['points'].astype(np.float32).tolist()));p.GetAttribute('omniphysics:restTriVtxIndices').Set(Vt.Vec3iArray(s['tris'].tolist()));p.GetAttribute('physxDeformableBody:selfCollision').Set(True);p.GetAttribute('physxDeformableBody:solverPositionIterationCount').Set(64);p.GetAttribute('physxDeformableBody:enableSpeculativeCCD').Set(True);p.GetAttribute('physxDeformableBody:linearDamping').Set(.2)
  UsdPhysics.CollisionAPI.Apply(p);c=PhysxSchema.PhysxCollisionAPI.Apply(p);c.CreateContactOffsetAttr(s['contact_offset']);c.CreateRestOffsetAttr(s['rest_offset'])
  mat=UsdShade.Material.Define(stage,path+'Material');q=mat.GetPrim()
  for api in ['OmniPhysicsBaseMaterialAPI','OmniPhysicsDeformableMaterialAPI','OmniPhysicsSurfaceDeformableMaterialAPI','PhysxSurfaceDeformableMaterialAPI']:q.ApplyAPI(api)
  values={'omniphysics:dynamicFriction':s['friction'],'omniphysics:density':1100.,'omniphysics:youngsModulus':s['youngs'],'omniphysics:poissonsRatio':s['poisson'],'omniphysics:surfaceThickness':s['thickness'],'omniphysics:surfaceBendStiffness':s['youngs']/(12*(1-s['poisson']**2)),'physxDeformableMaterial:elasticityDamping':.02,'physxDeformableMaterial:bendDamping':.01}
  for key,value in values.items():q.GetAttribute(key).Set(value)
  sh=UsdShade.Shader.Define(stage,path+'Material/Surface');sh.CreateIdAttr('UsdPreviewSurface');sh.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*s['color']));sh.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(.8);mat.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(),'surface');binding=UsdShade.MaterialBindingAPI.Apply(p);binding.Bind(mat);binding.Bind(mat,UsdShade.Tokens.weakerThanDescendants,'physics')
 # Cloth is sewn to the inner edge. Exclude only this frame/cloth pair;
 # each surface still self-collides and the retaining band collides with both.
 UsdPhysics.FilteredPairsAPI.Apply(stage.GetPrimAtPath(root+'/frame')).CreateFilteredPairsRel().AddTarget(Sdf.Path(root+'/cloth'))
 def attach(name,a,b,ia,ib):
  p=stage.DefinePrim(root+'/'+name,'OmniPhysicsVtxVtxAttachment');p.GetRelationship('omniphysics:src0').SetTargets([Sdf.Path(root+'/'+a)]);p.GetRelationship('omniphysics:src1').SetTargets([Sdf.Path(root+'/'+b)]);p.GetAttribute('omniphysics:vtxIndicesSrc0').Set(ia);p.GetAttribute('omniphysics:vtxIndicesSrc1').Set(ib)
 attach('sewn_boundary','frame','cloth',list(range(N)),list(range(1+(LEVELS-1)*N,1+LEVELS*N)))
 # A 12 mm textile tab separates the sewn contact regions. The band still
 # collides with the packet, which is essential to its retaining function.
 for a,b in [('frame','tab'),('band','tab')]:
  UsdPhysics.FilteredPairsAPI.Apply(stage.GetPrimAtPath(root+'/'+a)).CreateFilteredPairsRel().AddTarget(Sdf.Path(root+'/'+b))
 attach('tab_seam','frame','tab',[N],[0])
 attach('band_seam','tab','band',[2],[M+M//2])

 # Native two-way coupling transfers sleeve contact forces to the spring strip.
 for name,ids,local in HEM_ATTACHMENTS:
  p=stage.DefinePrim(root+'/sewn_'+name,'OmniPhysicsVtxXformAttachment')
  p.GetRelationship('omniphysics:src0').SetTargets([Sdf.Path(root+'/frame')])
  p.GetRelationship('omniphysics:src1').SetTargets([Sdf.Path(root+'/'+name)])
  p.GetAttribute('omniphysics:vtxIndicesSrc0').Set(ids)
  p.GetAttribute('omniphysics:localPositionsSrc1').Set(Vt.Vec3fArray(local.astype(np.float32).tolist()))
