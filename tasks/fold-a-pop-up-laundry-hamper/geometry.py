"""A coupled approximation of the flattened spring frames and flexible sewn mesh.

The remaining task is the characteristic twist-and-nest fold. No hinges select
its final shape and no stage variable changes the frame rest angles.
"""
from geometry_helpers import *
BODIES=[];JOINTS=[]
N=12;A=.165;B=.265;CENTER=np.array([.29,0,TABLE+.112])
BODIES.append(body("folding_board",[.29,0,TABLE+.050],[box((.220,.380,.100))],mass=1.,fixed=True,color=(.58,.40,.25)))
# A rounded rectangle sampled at equal arclength, 33 x 53 cm overall.
def rounded_rect(a,b,r=.025):
 points=[]
 for cx,cy,start in [(a-r,b-r,0),(-a+r,b-r,90),(-a+r,-b+r,180),(a-r,-b+r,270)]:
  for angle in np.linspace(start,start+90,50,endpoint=False):
   t=np.radians(angle);points.append([cx+r*np.cos(t),cy+r*np.sin(t)])
 p=np.array(points);p=np.vstack([p,p[0]]);length=np.linalg.norm(np.diff(p,axis=0),axis=1);arc=np.r_[0,np.cumsum(length)];u=(np.linspace(0,arc[-1],N,endpoint=False)-.0304)%arc[-1]
 return np.c_[np.interp(u,arc,p[:,0]),np.interp(u,arc,p[:,1])]
P=rounded_rect(A,B)
FRAMES=[np.c_[P,np.full(N,face*.004)]+CENTER for face in range(4)]
# Aggregate the four flattened frame layers into one elastic strip. Its mass
# and rotational stiffness are the sums of the four parallel frames. Relative
# inter-layer slip is omitted; twisting, bending, collisions and spring-back remain.
for face in range(1):
 points=np.c_[P,np.full(N,.006)]+CENTER
 for i in range(N):
  a,b=points[i],points[(i+1)%N];v=b-a;length=np.linalg.norm(v);x=v/length;z=np.array([0,0,1]);y=np.cross(z,x);R=np.column_stack([x,y,z]);name=f'wire_{face}_{i:02d}'
  BODIES.append(body(name,(a+b)/2,[box((length,.008,.015))],mass=4*(8000*length*.004*.00045+300*length*.008*.003),color=(.13,.29,.44),quat=list(Rotation.from_matrix(R).as_quat()),friction=1.,contact_offset=.0001))
 for i in range(N):
  a=f'wire_{face}_{i:02d}';b=f'wire_{face}_{(i+1)%N:02d}';aa=next(q for q in BODIES if q['name']==a);bb=next(q for q in BODIES if q['name']==b)
  axes={k:dict(limits=(-179,179),stiffness=4*s,damping=.0005) for k,s in [('rotX',.015),('rotY',.020),('rotZ',.75)]}
  JOINTS.append(joint(f'wire_joint_{face}_{i}',a,b,[aa['shapes'][0]['size'][0]/2,0,0],[-bb['shapes'][0]['size'][0]/2,0,0],axes=axes,break_force=400.,break_torque=6.))
# Flattened mesh layers share a flexible bar-and-node net. Its 60 g mass
# equals the four earlier cloth layers. Links preserve thread lengths while
# freely rotating nodes permit folding and shear. Inter-layer slip and mesh
# shear resistance are omitted; the frame still supplies bending resistance.
NX,NY=3,5;DX=.31/NX;DY=.51/NY
for i in range(NX+1):
 for j in range(NY+1):
  name=f'mesh_0_{i}_{j}';pos=CENTER+[(i-NX/2)*DX,(j-NY/2)*DY,.006]
  BODIES.append(body(name,pos,[box((.004,.004,.004))],mass=.0006,color=(.26,.46,.61),friction=.6,contact_offset=.00025))
for i in range(NX+1):
 for j in range(NY+1):
  name=f'mesh_0_{i}_{j}';node=next(b for b in BODIES if b['name']==name)
  for di,dj in [(1,0),(0,1)]:
   if i+di>NX or j+dj>NY:continue
   other=f'mesh_0_{i+di}_{j+dj}';end=next(b for b in BODIES if b['name']==other)
   a,b=np.array(node['pos']),np.array(end['pos']);v=b-a;length=np.linalg.norm(v)
   rot=Rotation.align_vectors([v/length],[[1,0,0]])[0];link=f'cloth_link_{i}_{j}_{di}_{dj}'
   BODIES.append(body(link,(a+b)/2,[box((length,.0024,.0024))],mass=.0012,color=(.26,.46,.61),quat=rot.as_quat().tolist(),friction=.6))
   for side,target,x in [(0,name,-length/2),(1,other,length/2)]:
    JOINTS.append(joint(f'fabric_{i}_{j}_{di}_{dj}_{side}',link,target,[x,0,0],[0,0,0],axes=bend_axes(0.,.000001,179),break_force=40.))
  if i in [0,NX] or j in [0,NY]:
   pos=np.array(node['pos']);wires=[b for b in BODIES if b['name'].startswith('wire_')]
   wire=min(wires,key=lambda b:np.linalg.norm(pos-np.asarray(b['pos'])))
   JOINTS.append(joint(f'edge_0_{i}_{j}',wire['name'],name,Rotation.from_quat(wire['quat']).inv().apply(pos-wire['pos']),[0,0,0],axes=bend_axes(0.,.000001,179),break_force=50.))
# Links incident on the same sewn node overlap at that shared endpoint.
# Ignore only those local neighbour contacts; non-neighbour fabric and frame
# pieces still collide when folded.
from collections import defaultdict
incident=defaultdict(set)
for j in JOINTS:
 if j['name'].startswith(('fabric_','edge_')):
  a,b=j['a'],j['b']
  if a.startswith('mesh_'):incident[a].add(b)
  if b.startswith('mesh_'):incident[b].add(a)
for neighbours in incident.values():
 for name in neighbours:
  part=next(b for b in BODIES if b['name']==name)
  part.setdefault('exclude',[]).extend(sorted(neighbours-{name}))
# Attached elastic retaining loop; it must be stretched over the folded packet.
EN=32;ER=.300/(2*np.pi)
anchor=next(b for b in BODIES if b['name']=='wire_0_00')
t=np.pi;E=np.array(anchor['pos'])-np.array([ER*(np.cos(t)+np.cos(t+2*np.pi/EN))/2,ER*(np.sin(t)+np.sin(t+2*np.pi/EN))/2,0])
for i,t in enumerate(np.arange(EN)*2*np.pi/EN):
 a=E+[ER*np.cos(t),ER*np.sin(t),0];b=E+[ER*np.cos(t+2*np.pi/EN),ER*np.sin(t+2*np.pi/EN),0];v=b-a;R=Rotation.align_vectors([v/np.linalg.norm(v)],[[1,0,0]])[0]
 BODIES.append(body(f'elastic_{i:02d}',(a+b)/2,[box((np.linalg.norm(v),.005,.001))],mass=.00015,color=(.08,.10,.14),quat=list(R.as_quat()),friction=1.,contact_offset=.0001))
for i in range(EN):
 a=next(b for b in BODIES if b['name']==f'elastic_{i:02d}');b=next(b for b in BODIES if b['name']==f'elastic_{(i+1)%EN:02d}')
 axes=bend_axes(.0000005,.0000002);axes['transX']=dict(limits=(-.001,.010),stiffness=1280.,damping=.01)
 JOINTS.append(joint('elastic_joint_'+str(i),a['name'],b['name'],[a['shapes'][0]['size'][0]/2,0,0],[-b['shapes'][0]['size'][0]/2,0,0],axes=axes,break_force=25.))
# A single sewn attachment to the frame. Layout is folded back through this point.
a=next(b for b in BODIES if b['name']=='wire_0_00');b=next(b for b in BODIES if b['name']=='elastic_16');point=(np.array(a['pos'])+b['pos'])/2
JOINTS.append(joint('retainer_attachment',a['name'],b['name'],Rotation.from_quat(a['quat']).inv().apply(point-a['pos']),Rotation.from_quat(b['quat']).inv().apply(point-b['pos']),axes=bend_axes(.000001,.000001),break_force=25.))
# Face the long dimension toward the arms for short-edge pickup.
layout=Rotation.from_euler('z',0,degrees=True)
for part in BODIES:
 part['pos']=(CENTER+layout.apply(np.asarray(part['pos'])-CENTER)).tolist()
 part['quat']=(layout*Rotation.from_quat(part.get('quat',[0,0,0,1]))).as_quat().tolist()
GRIP_ENDS=(1,7)
FRAME_LAYERS=(0,)
# Finite rubber-pad contact area supplies native spin friction at a grip.
for part in BODIES:
 if part['name'].startswith('wire_'):part.update(torsional_patch_radius=.004,min_torsional_patch_radius=.0015,contact_offset=.0005,max_angular_velocity=10.,speculative_ccd=True)
finalize(BODIES,JOINTS)
