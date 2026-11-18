"""Four elastic spring-steel frames and sewn mesh, initially flattened but uncoiled.

The remaining task is the characteristic twist-and-nest fold. No hinges select
its final shape and no stage variable changes the frame rest angles.
"""
from geometry_helpers import *
BODIES=[];JOINTS=[]
N=48;A=.165;B=.265;CENTER=np.array([.29,0,TABLE+.112])
BODIES.append(body("folding_board",[.29,0,TABLE+.050],[box((.220,.380,.100))],mass=1.,fixed=True,color=(.58,.40,.25)))
# A rounded rectangle sampled at equal arclength, 33 x 53 cm overall.
def rounded_rect(a,b,r=.025):
 points=[]
 for cx,cy,start in [(a-r,b-r,0),(-a+r,b-r,90),(-a+r,-b+r,180),(a-r,-b+r,270)]:
  for angle in np.linspace(start,start+90,50,endpoint=False):
   t=np.radians(angle);points.append([cx+r*np.cos(t),cy+r*np.sin(t)])
 p=np.array(points);p=np.vstack([p,p[0]]);length=np.linalg.norm(np.diff(p,axis=0),axis=1);arc=np.r_[0,np.cumsum(length)];u=np.linspace(0,arc[-1],N,endpoint=False)
 return np.c_[np.interp(u,arc,p[:,0]),np.interp(u,arc,p[:,1])]
P=rounded_rect(A,B);FRAMES=[]
for face in range(4):
 points=np.c_[P,np.full(N,face*.004)]+CENTER;FRAMES.append(points)
 for i in range(N):
  a,b=points[i],points[(i+1)%N];v=b-a;length=np.linalg.norm(v);x=v/length;z=np.array([0,0,1]);y=np.cross(z,x);R=np.column_stack([x,y,z]);name=f'wire_{face}_{i:02d}'
  BODIES.append(body(name,(a+b)/2,[box((length,.008,.003))],mass=8000*length*.004*.00045+300*length*.008*.003,color=(.13,.29,.44),quat=list(Rotation.from_matrix(R).as_quat()),friction=1.,contact_offset=.0001))
 for i in range(N):
  a=f'wire_{face}_{i:02d}';b=f'wire_{face}_{(i+1)%N:02d}';aa=next(q for q in BODIES if q['name']==a);bb=next(q for q in BODIES if q['name']==b)
  axes={k:dict(limits=(-179,179),stiffness=s,damping=.0005) for k,s in [('rotX',.06),('rotY',.08),('rotZ',3.0)]}
  JOINTS.append(joint(f'wire_joint_{face}_{i}',a,b,[aa['shapes'][0]['size'][0]/2,0,0],[-bb['shapes'][0]['size'][0]/2,0,0],axes=axes,break_force=100.,break_torque=1.5))
# Each steel frame has a sewn 8 mm wide, 3 mm thick polyester binding.
# The binding supplies its native collision/grip surface; spring mechanics remain steel.
# Coarse flexible fabric panels span the frames. Native panels collide and fold.
NX,NY=6,10;DX=.31/NX;DY=.51/NY
for face in range(4):
 for i in range(NX):
  for j in range(NY):
   name=f'mesh_{face}_{i}_{j}';pos=CENTER+[(i-(NX-1)/2)*DX,(j-(NY-1)/2)*DY,face*.004]
   BODIES.append(body(name,pos,[box((DX*.98,DY*.98,.0006))],mass=.00025,color=(.26,.46,.61),friction=.6,contact_offset=.0001))
   for di,dj in [(-1,0),(0,-1)]:
    if i+di>=0 and j+dj>=0:
     a=np.array([-di*DX/2,-dj*DY/2,0]);JOINTS.append(joint(f'fabric_{face}_{i}_{j}_{di}_{dj}',f'mesh_{face}_{i+di}_{j+dj}',name,a,-a,axes=bend_axes(.000001,.000001),break_force=20.))
   if i in [0,NX-1] or j in [0,NY-1]:
    distances=[np.linalg.norm(pos-(FRAMES[face][k]+FRAMES[face][(k+1)%N])/2) for k in range(N)];k=int(np.argmin(distances));wire=next(b for b in BODIES if b['name']==f'wire_{face}_{k:02d}')
    # Sewing anchor is at the fabric edge; its local point can be along a frame.
    target=pos.copy()
    if i==0:target[0]-=DX/2
    if i==NX-1:target[0]+=DX/2
    if j==0:target[1]-=DY/2
    if j==NY-1:target[1]+=DY/2
    JOINTS.append(joint(f'edge_{face}_{i}_{j}',wire['name'],name,Rotation.from_quat(wire['quat']).inv().apply(target-wire['pos']),target-pos,axes=bend_axes(.000001,.000001),break_force=25.))
# Sewn common corners couple the four flattened sides without fixing their poses.
for face in range(1,4):
 for k in [0,N//4,N//2,3*N//4]:
  a=f'wire_{face-1}_{k:02d}';b=f'wire_{face}_{k:02d}'
  JOINTS.append(joint(f'corner_{face}_{k}',a,b,[0,0,.002],[0,0,-.002],axes=bend_axes(.000002,.000002),break_force=30.))
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
GRIP_ENDS=(5,29)
# Finite rubber-pad contact area supplies native spin friction at a grip.
for part in BODIES:
 if part['name'].startswith('wire_'):part.update(torsional_patch_radius=.004,min_torsional_patch_radius=.0015,contact_offset=.0005,max_angular_velocity=10.,speculative_ccd=True)
finalize(BODIES,JOINTS)
