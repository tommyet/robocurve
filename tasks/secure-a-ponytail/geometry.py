"""Loose synthetic hair and a small, plain elastic; no hair is pre-tied."""
from geometry_helpers import *
BODIES=[];JOINTS=[]
HEAD=np.array([.39,0,TABLE+.305]);ELASTIC=np.array([.27,0,TABLE+.060])
head=[sphere((.090,.078,.115)),sphere((.015,.012,.023),(.091,0,-.015)),cylinder(.038,.19,(0,0,-.205)),box((.15,.15,.015),(0,0,-.2975))]
head += [sphere((.004,.008,.005),(.084,y,.020),(.12,.12,.13)) for y in [-.030,.030]]
BODIES.append(body('styling_head',HEAD,head,fixed=True,mass=1.5,color=(.75,.62,.50),friction=.5))
STRANDS=12;SEGMENTS=18
# Each flexible lock groups fine fibres into a 10 mm contact envelope.
# The 36 g total mass includes voids between fibres; no locks are joined together.
for s in range(STRANDS):
 y=(s-5.5)*.0065;root=HEAD+[-.073,y,.035+.015*np.cos(s)]
 pts=[]
 for j in range(SEGMENTS+1):
  u=j/SEGMENTS;pts.append(root+[-.035*u+.004*np.sin(2*np.pi*u+s*.25),.002*np.sin(3*np.pi*u+s),-.245*u])
 for i,(a,b) in enumerate(zip(pts[:-1],pts[1:])):
  a,b=np.array(a),np.array(b);v=b-a;length=np.linalg.norm(v);rot=Rotation.align_vectors([v/length],[[0,0,1]])[0];name=f'hair_{s}_{i}'
  part=body(name,(a+b)/2,[cylinder(.0045,length)],mass=.003/SEGMENTS,quat=rot.as_quat().tolist(),color=(.20+.015*(s%3),.095,.040),friction=.5,contact_offset=.0001,linear_damping=.2,angular_damping=.3)
  I=part['mass']*length*length/12;part['inertia']=[max(I,1e-10),max(I,1e-10),max(I/10,1e-10)];part['visible']=False;BODIES.append(part)
  if i:
   prev=next(b for b in BODIES if b['name']==f'hair_{s}_{i-1}')
   axes={axis:dict(limits=(-180,180),stiffness=.000015,damping=.000002) for axis in ('rotX','rotY','rotZ')}
   JOINTS.append(joint(f'hair_join_{s}_{i}',prev['name'],name,[0,0,prev['shapes'][0]['length']/2],[0,0,-length/2],axes=axes,break_force=15.))
  else:JOINTS.append(joint(f'root_{s}','styling_head',name,a-HEAD,[0,0,-length/2],axes=bend_axes(.0002,.00002),break_force=20.))
# Two plain 8 mm wooden blocks support the loose band without filling its
# opening or obstructing the underside of either pickup point.
for side in [-1,1]:
 BODIES.append(body('elastic_rest_'+('left' if side<0 else 'right'),[ELASTIC[0]+side*.0175,0,TABLE+.025],[box((.008,.008,.050))],mass=.005,fixed=True,color=(.59,.44,.28)))
# A standard small seamless elastic: 30 mm inside diameter, 5 mm flat width.
M=64;POINTS=[]
for radius in [.015,.0175,.020]:
 for i in range(M):
  t=2*np.pi*i/M;POINTS.append(ELASTIC+[radius*np.cos(t),radius*np.sin(t),0])
POINTS=np.asarray(POINTS);TRIS=[]
for row in range(2):
 for i in range(M):
  a=row*M+i;b=row*M+(i+1)%M;c=a+M;d=b+M;TRIS.extend([[a,b,c],[b,d,c]])
TRIS=np.asarray(TRIS);RIM=np.arange(M)
EDGES=np.unique(np.sort(np.concatenate([TRIS[:,[0,1]],TRIS[:,[1,2]],TRIS[:,[2,0]]]),axis=1),axis=0);REST_LENGTHS=np.linalg.norm(POINTS[EDGES[:,1]]-POINTS[EDGES[:,0]],axis=1)
finalize(BODIES,JOINTS)

def spawn_surface(stage,root):
 from pxr import UsdGeom,UsdPhysics,PhysxSchema,UsdShade,Gf,Vt,Sdf
 mesh=UsdGeom.Mesh.Define(stage,root+'/elastic');mesh.CreatePointsAttr(Vt.Vec3fArray(POINTS.astype(np.float32).tolist()));mesh.CreateFaceVertexCountsAttr([3]*len(TRIS));mesh.CreateFaceVertexIndicesAttr(TRIS.ravel().tolist());mesh.CreateSubdivisionSchemeAttr('none');mesh.CreateDoubleSidedAttr(True)
 p=mesh.GetPrim()
 for api in ['OmniPhysicsDeformableBodyAPI','OmniPhysicsSurfaceDeformableSimAPI','PhysxSurfaceDeformableBodyAPI']:
  if not p.ApplyAPI(api):raise RuntimeError('Required native surface API unavailable: '+api)
 p.GetAttribute('omniphysics:mass').Set(.0006)
 p.GetAttribute('omniphysics:restShapePoints').Set(Vt.Vec3fArray(POINTS.astype(np.float32).tolist()))
 p.GetAttribute('omniphysics:restTriVtxIndices').Set(Vt.Vec3iArray(TRIS.tolist()))
 p.GetAttribute('physxDeformableBody:selfCollision').Set(True)
 p.GetAttribute('physxDeformableBody:solverPositionIterationCount').Set(64)
 p.GetAttribute('physxDeformableBody:enableSpeculativeCCD').Set(True)
 p.GetAttribute('physxDeformableBody:linearDamping').Set(.1)
 UsdPhysics.CollisionAPI.Apply(p);col=PhysxSchema.PhysxCollisionAPI.Apply(p);col.CreateContactOffsetAttr(.001);col.CreateRestOffsetAttr(.0004)
 mat=UsdShade.Material.Define(stage,root+'/elasticMaterial');q=mat.GetPrim()
 for api in ['OmniPhysicsBaseMaterialAPI','OmniPhysicsDeformableMaterialAPI','OmniPhysicsSurfaceDeformableMaterialAPI','PhysxSurfaceDeformableMaterialAPI']:q.ApplyAPI(api)
 for key,value in {'omniphysics:dynamicFriction':1.2,'omniphysics:density':1100.,'omniphysics:youngsModulus':2e5,'omniphysics:poissonsRatio':.45,'omniphysics:surfaceThickness':.001,'omniphysics:surfaceBendStiffness':2e5/(12*(1-.45**2)),'physxDeformableMaterial:elasticityDamping':.02,'physxDeformableMaterial:bendDamping':.01}.items():
  attr=q.GetAttribute(key)
  if not attr:raise RuntimeError('Required elastic material attribute unavailable: '+key)
  attr.Set(value)
 shader=UsdShade.Shader.Define(stage,root+'/elasticMaterial/Surface');shader.CreateIdAttr('UsdPreviewSurface');shader.CreateInput('diffuseColor',Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(.64,.12,.27));shader.CreateInput('roughness',Sdf.ValueTypeNames.Float).Set(.5);mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(),'surface')
 bind=UsdShade.MaterialBindingAPI.Apply(p);bind.Bind(mat);bind.Bind(mat,UsdShade.Tokens.weakerThanDescendants,'physics')
