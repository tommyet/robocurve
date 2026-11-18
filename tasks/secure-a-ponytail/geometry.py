"""Loose synthetic hair and a small, plain elastic; no hair is pre-tied."""
from geometry_helpers import *
BODIES=[];JOINTS=[]
HEAD=np.array([.39,0,TABLE+.305]);ELASTIC=np.array([.27,0,TABLE+.063])
head=[sphere((.090,.078,.115)),sphere((.015,.012,.023),(.091,0,-.015)),cylinder(.038,.19,(0,0,-.205)),box((.15,.15,.015),(0,0,-.2975))]
head += [sphere((.004,.008,.005),(.084,y,.020),(.12,.12,.13)) for y in [-.030,.030]]
BODIES.append(body('styling_head',HEAD,head,fixed=True,mass=1.5,color=(.75,.62,.50),friction=.5))
STRANDS=12;SEGMENTS=18
# Each flexible lock groups fine fibres into a 5 mm contact envelope.
# The 36 g total mass includes voids between fibres; no locks are joined together.
for s in range(STRANDS):
 y=(s-5.5)*.0065;z=.035+.015*np.cos(s);back=-.0915*np.sqrt(1-(y/.078)**2-(z/.115)**2);root=HEAD+[back,y,z]
 pts=[]
 for j in range(SEGMENTS+1):
  u=j/SEGMENTS;p=root+[-.035*u+.004*np.sin(2*np.pi*u+s*.25),.002*np.sin(3*np.pi*u+s),-.245*u]
  local=p-HEAD
  if (local[1]/.078)**2+(local[2]/.115)**2<1:
   scalp=HEAD[0]-.090*np.sqrt(1-(local[1]/.078)**2-(local[2]/.115)**2)
   p[0]=min(p[0],scalp-.003)
  pts.append(p)
 for i,(a,b) in enumerate(zip(pts[:-1],pts[1:])):
  a,b=np.array(a),np.array(b);v=b-a;length=np.linalg.norm(v);rot=Rotation.align_vectors([v/length],[[0,0,1]])[0];name=f'hair_{s}_{i}'
  part=body(name,(a+b)/2,[cylinder(.0025,length)],mass=.003/SEGMENTS,quat=rot.as_quat().tolist(),color=(.20+.015*(s%3),.095,.040),friction=.5,contact_offset=.0001,linear_damping=.2,angular_damping=.3)
  I=part['mass']*length*length/12;part['inertia']=[max(I,1e-10),max(I,1e-10),max(I/10,1e-10)];part['visible']=False;BODIES.append(part)
  if i:
   prev=next(b for b in BODIES if b['name']==f'hair_{s}_{i-1}')
   axes={axis:dict(limits=(-180,180),stiffness=.000015,damping=.000002) for axis in ('rotX','rotY','rotZ')}
   JOINTS.append(joint(f'hair_join_{s}_{i}',prev['name'],name,[0,0,prev['shapes'][0]['length']/2],[0,0,-length/2],axes=axes,break_force=15.))
  else:JOINTS.append(joint(f'root_{s}','styling_head',name,a-HEAD,[0,0,-length/2],axes=bend_axes(.0002,.00002),break_force=20.))
# Two wooden rails support four arcs while leaving the central pickup lane clear.
for sx in [-1,1]:
 BODIES.append(body(f'elastic_rest_{sx+1}',[ELASTIC[0]+sx*.012,0,TABLE+.030],[box((.004,.032,.060))],mass=.010,fixed=True,color=(.59,.44,.28)))
# A plain 3 mm cord elastic, 30 mm inside diameter. Native passive
# stretch joints connect contact-bearing segments into a closed loop.
M=64;radius=.0165;theta=np.arange(M)*2*np.pi/M
vertices=ELASTIC+np.c_[radius*np.cos(theta),radius*np.sin(theta),np.zeros(M)]
centres=(vertices+np.roll(vertices,-1,axis=0))/2
lengths=np.linalg.norm(np.roll(vertices,-1,axis=0)-vertices,axis=1)
for i in range(M):
 tangent=(vertices[(i+1)%M]-vertices[i])/lengths[i];radial=centres[i]-ELASTIC;radial/=np.linalg.norm(radial);rot=Rotation.from_matrix(np.column_stack([radial,np.cross(tangent,radial),tangent]))
 shape=dict(kind='capsule',radius=.0015,length=float(lengths[i]),pos=[0,0,0],quat=[0,0,0,1])
 BODIES.append(body(f'band_segment_{i:03d}',centres[i],[shape],mass=.001/M,quat=rot.as_quat().tolist(),color=(.64,.12,.27),friction=1.2,contact_offset=.0002,torsional_patch_radius=.0015,min_torsional_patch_radius=.001,exclude=[f'band_segment_{(i+d)%M:03d}' for d in [-2,-1,1,2]],visible=False))
for i in range(M):
 axes={**fixed_axes(),**bend_axes(.000005,.0000001,180),'transZ':dict(limits=(-lengths[i]*.2,lengths[i]*4),stiffness=1.4/lengths[i],damping=.02)}
 JOINTS.append(joint(f'band_stretch_{i:03d}',f'band_segment_{i:03d}',f'band_segment_{(i+1)%M:03d}',[0,0,lengths[i]/2],[0,0,-lengths[(i+1)%M]/2],axes=axes,break_force=8.))
radial=centres-ELASTIC;radial/=np.linalg.norm(radial,axis=1)[:,None]
POINTS=np.vstack([centres+offset*radial for offset in [-.0015,0,.0015]])
TRIS=[]
for row in range(2):
 for i in range(M):
  a=row*M+i;b=row*M+(i+1)%M;c=a+M;d=b+M;TRIS.extend([[a,b,c],[b,d,c]])
TRIS=np.asarray(TRIS);RIM=np.arange(M)
EDGES=np.unique(np.sort(np.concatenate([TRIS[:,[0,1]],TRIS[:,[1,2]],TRIS[:,[2,0]]]),axis=1),axis=0)
REST_LENGTHS=np.linalg.norm(POINTS[EDGES[:,1]]-POINTS[EDGES[:,0]],axis=1)
finalize(BODIES,JOINTS)

def spawn_surface(stage,root):
 # All band physics is native rigid contact and passive elastic joints.
 pass
