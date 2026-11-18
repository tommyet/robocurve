"""Native elastic frame, sewn flexible mesh and an attached retaining band.

The four flattened spring frames are aggregated: their bending stiffness and
mass add. Inter-layer slip is omitted. No rest shape changes during the trial.
"""
from geometry_helpers import *
BODIES=[];JOINTS=[]
CENTER=np.array([.29,0,TABLE+.112]);N=96
BODIES.append(body('folding_stand',[.29,0,TABLE+.005],[box((.350,.380,.010)),box((.020,.380,.090),(-.165,0,.050)),box((.020,.380,.090),(.165,0,.050))],mass=1.6,fixed=True,color=(.58,.40,.25)))
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
M=64;radius=.300/(2*np.pi);anchor=FRAME_POINTS[N];out=np.r_[-inside[0],0.];tangent=np.cross([0,0,1],out);centre=anchor+out*radius
BAND_POINTS=[];BAND_TRIS=[]
for r in [radius-.0025,radius,radius+.0025]:
 for i in range(M):
  angle=i*2*np.pi/M;BAND_POINTS.append(centre+r*(out*np.cos(angle)+tangent*np.sin(angle)))
for row in range(2):
 for i in range(M):
  a=row*M+i;b=row*M+(i+1)%M;c=a+M;d=b+M;BAND_TRIS += [[a,b,c],[b,d,c]]
SURFACES=[dict(name='frame',points=FRAME_POINTS,tris=FRAME_TRIS,mass=.150,youngs=8e11,poisson=.3,thickness=.00045,friction=.8,rest_offset=.0035,contact_offset=.0045,color=(.13,.29,.44)),
 dict(name='cloth',points=CLOTH_POINTS,tris=CLOTH_TRIS,mass=.060,youngs=2e6,poisson=.3,thickness=.0003,friction=.4,rest_offset=.00015,contact_offset=.0007,color=(.28,.47,.62)),
 dict(name='band',points=BAND_POINTS,tris=BAND_TRIS,mass=.004,youngs=4e5,poisson=.45,thickness=.001,friction=1.,rest_offset=.0005,contact_offset=.001,color=(.10,.11,.13))]
for s in SURFACES:
 s['points']=np.asarray(s['points']);s['tris']=np.asarray(s['tris']);s['edges']=np.unique(np.sort(np.concatenate([s['tris'][:,[0,1]],s['tris'][:,[1,2]],s['tris'][:,[2,0]]]),axis=1),axis=0);s['rest_lengths']=np.linalg.norm(s['points'][s['edges'][:,0]]-s['points'][s['edges'][:,1]],axis=1)
GRIP_INDICES=(12,60);GRIP_POINTS=FRAME_POINTS[list(GRIP_INDICES)]
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
 attach('band_seam','frame','band',[N],[M+M//2])
