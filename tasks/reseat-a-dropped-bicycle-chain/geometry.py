"""Full-size bicycle drivetrain. Connected rollers engage colliding teeth."""
from geometry_helpers import *
BODIES=[];JOINTS=[]
FRONT=np.array([.40,-.03,TABLE+.28]);REAR=FRONT+[0,.43,.09]
PITCH=.0127;TEETH=40;R=PITCH/(2*np.sin(np.pi/TEETH));RR=PITCH/(2*np.sin(np.pi/16))
# Frame, wheels and crank retain adult bicycle dimensions; the final
# layout below rests the bicycle on its non-drive side on foam supports.
front_hub=REAR+[0,-1.08,0];saddle=FRONT+[.025,.12,.48];head=FRONT+[.025,-.44,.41]
frame=[]
for a,b in [(FRONT+[.025,0,0],saddle),(saddle,head),(head,FRONT+[.025,0,0]),(saddle,REAR+[.025,0,0]),(FRONT+[.025,0,0],REAR+[.025,0,0]),(head,front_hub+[.025,0,0])]:frame.append(rod_between(a-FRONT,b-FRONT,.015))
frame += [cylinder(.022,.09,(-.01,0,0),Rotation.from_euler('y',90,degrees=True).as_quat()),sphere((.075,.12,.025),saddle-FRONT+[0,0,.01])]
# Tyres are visual/physical full-sized rings, not a scaled-down bicycle.
for centre in [front_hub,REAR]:
 for j in range(48):
  t=j*2*np.pi/48;u=(j+1)*2*np.pi/48
  shape=rod_between(centre-FRONT+[.025,.335*np.cos(t),.335*np.sin(t)],centre-FRONT+[.025,.335*np.cos(u),.335*np.sin(u)],.015);shape['color']=[.10,.11,.12];frame.append(shape)

BODIES.append(body('bicycle_frame',FRONT,frame,mass=12.,color=(.20,.38,.55)))
def sprocket(name,center,n,r,crank=False):
 sh=[cylinder(r-.006,.0024,quat=Rotation.from_euler('y',90,degrees=True).as_quat())]
 for i in range(n):
  t=i*2*np.pi/n;rot=Rotation.from_euler('x',t).as_quat()
  sh.append(box((.0024,.0075,.0032),(0,r*np.cos(t),r*np.sin(t)),quat=rot))
 if crank:
  sh += [box((.012,.170,.018),(-.025,.085,0)),box((.060,.055,.016),(-.055,.170,0),(.17,.18,.19))]
 BODIES.append(body(name,center,sh,mass=.75 if crank else .18,color=(.63,.65,.67),friction=.35,contact_offset=.00015,max_angular_velocity=8.))
 JOINTS.append(joint(name+'_bearing','bicycle_frame',name,center-FRONT,[0,0,0],axes={**fixed_axes(),'rotX':dict(limits=(-180,180),stiffness=0.,damping=.015)}))
sprocket('chainring',FRONT,TEETH,R,True);sprocket('rear_sprocket',REAR,16,RR)
# Ordinary single-pulley spring tensioner: permits chain recovery while
# maintaining tension afterwards, without stretching the steel links.
PIVOT=REAR+[0,-.015,-.060];IDLER=REAR+[0,-.050,-.110];IR=PITCH/(2*np.sin(np.pi/12))
BODIES.append(body('tensioner_arm',PIVOT,[rod_between([0,0,0],IDLER-PIVOT,.005)],mass=.065,color=(.25,.27,.29)))
JOINTS.append(joint('tensioner_spring','bicycle_frame','tensioner_arm',PIVOT-FRONT,[0,0,0],axes={**fixed_axes(),'rotX':dict(limits=(-70,70),stiffness=.4,damping=.01,target=30.)}))
sprocket('idler',IDLER,12,IR)
JOINTS[-1]['a']='tensioner_arm';JOINTS[-1]['p0']=(IDLER-PIVOT).tolist()

# Dense path resampled at the real 12.7 mm pitch; the front half is laterally
# off the chainring and must settle into the dropped configuration.
def path():
 yz=REAR[1:]-FRONT[1:];e=yz/np.linalg.norm(yz);n=np.array([-e[1],e[0]])
 points=[]
 # A closed belt route around two unequal sprockets, including slack.
 for c,r,angles in [(FRONT,R,np.linspace(np.pi/2,3*np.pi/2,100)),(IDLER,IR,np.linspace(np.radians(-85)-np.arctan2(e[1],e[0]),np.radians(-22)-np.arctan2(e[1],e[0]),45)),(REAR,RR,np.linspace(np.radians(-42),np.pi/2,70))]:
  for a in angles:
   xy=c[1:]+r*(e*np.cos(a)+n*np.sin(a));off=.045 if np.allclose(c,FRONT) else 0.
   points.append([c[0]+off,*xy])
 points=np.asarray(points);points=np.vstack([points,points[0]])
 lengths=np.linalg.norm(np.diff(points,axis=0),axis=1);arc=np.r_[0,np.cumsum(lengths)];count=round(arc[-1]/PITCH);u=np.linspace(0,arc[-1],count,endpoint=False)
 return np.c_[[np.interp(u,arc,points[:,k]) for k in range(3)]].T
POINTS=path();LINKS=len(POINTS)
for i in range(LINKS):
 a,b=POINTS[i],POINTS[(i+1)%LINKS];v=b-a;length=np.linalg.norm(v);x=v/length;y=np.array([1.,0.,0]);y-=x*(y@x);y/=np.linalg.norm(y);z=np.cross(x,y);rot=Rotation.from_matrix(np.column_stack([x,y,z]))
 shapes=[box((length,.001,.006),(0,s*.0023,0)) for s in [-1,1]]
 shapes += [cylinder(.0035,.0036,(-length/2,0,0),Rotation.from_euler('x',90,degrees=True).as_quat())]
 BODIES.append(body(f'link_{i:03d}',(a+b)/2,shapes,mass=.0031,quat=rot.as_quat().tolist(),color=(.24,.25,.27),friction=.3,contact_offset=.0001,max_angular_velocity=30.))
for i in range(LINKS):
 a=next(b for b in BODIES if b['name']==f'link_{i:03d}');b=next(b for b in BODIES if b['name']==f'link_{(i+1)%LINKS:03d}');axes={**fixed_axes(),'rotY':dict(limits=(-150,150),stiffness=0.,damping=.00005),'rotX':dict(limits=(-8,8),stiffness=.005,damping=.00005),'rotZ':dict(limits=(-8,8),stiffness=.005,damping=.00005)}
 JOINTS.append(joint(f'chain_pin_{i}',a['name'],b['name'],[a['shapes'][0]['size'][0]/2,0,0],[-b['shapes'][0]['size'][0]/2,0,0],axes=axes,break_force=300.))
finalize(BODIES,JOINTS)

# The full bicycle lies on its non-drive side on two low foam pads. This is
# ordinary access to a dropped chain, within the table-height arm workspace.
OLD_FRONT=FRONT.copy();BIKE_ROT=Rotation.from_euler('y',90,degrees=True).as_matrix();WORLD_FRONT=np.array([.33,.08,TABLE+.150])
def layout(p):return WORLD_FRONT+BIKE_ROT@(np.asarray(p)-OLD_FRONT)
for part in BODIES:
 part['pos']=layout(part['pos']).tolist();part['quat']=(Rotation.from_matrix(BIKE_ROT)*Rotation.from_quat(part['quat'])).as_quat().tolist()
FRONT=layout(FRONT);REAR=layout(REAR);POINTS=np.array([layout(p) for p in POINTS])
for name,where in [('front',layout(front_hub)),('rear',REAR)]:
 BODIES.append(body(name+'_foam_pad',[where[0],where[1],TABLE+.055],[box((.16,.12,.110))],fixed=True,mass=.05,color=(.24,.28,.31),friction=1.))
