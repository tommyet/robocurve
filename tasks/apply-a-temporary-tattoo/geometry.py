"""Flexible transfer paper, compressible wet sponge, and a curved PVC forearm."""
from geometry_helpers import *
BODIES=[];JOINTS=[]
ARM=np.array([.34,.025,TABLE+.045]);ARM_RADIUS=.032
# A rigid practice form covered in smooth PVC vinyl, mounted on ordinary rests.
BODIES.append(body('forearm',ARM,[cylinder(ARM_RADIUS,.20,quat=Rotation.from_euler('y',90,degrees=True).as_quat())],mass=.25,fixed=True,color=(.69,.44,.31)))
for side in [-1,1]:BODIES.append(body('support_'+str(side).replace('-','n'),ARM+[side*.080,0,-.032],[box((.025,.07,.026))],mass=.05,fixed=True,color=(.25,.29,.33)))
# Printed target is a 40 x 35 mm rectangle near the top of the form.
forearm=next(b for b in BODIES if b['name']=='forearm')
for side in [-1,1]:
 a=side*.0175/ARM_RADIUS;y=(ARM_RADIUS+.0002)*np.sin(a);z=(ARM_RADIUS+.0002)*np.cos(a)
 line=rod_between([-.020,y,z],[.020,y,z],.00025);line.update(collision=False,color=(.12,.12,.12));forearm['shapes'].append(line)
 arc=np.linspace(-.0175/ARM_RADIUS,.0175/ARM_RADIUS,13)
 for a,b in zip(arc[:-1],arc[1:]):
  pts=[[side*.020,(ARM_RADIUS+.0002)*np.sin(t),(ARM_RADIUS+.0002)*np.cos(t)] for t in [a,b]]
  line=rod_between(*pts,.00025);line.update(collision=False,color=(.12,.12,.12));forearm['shapes'].append(line)

NX,NY=10,8;DX=DY=.005;PAPER=np.array([.34,.13,TABLE+.0303])
BODIES.append(body('paper_rest',[.34,.13,TABLE+.015],[box((.030,.020,.030))],mass=.02,fixed=True,color=(.55,.63,.69)))
PATTERN=['0110110','1111111','1111111','0111110','0011100','0001000'];INK=[]
for i in range(NX):
 for j in range(NY):
  name=f'paper_{i}_{j}';x=(i-(NX-1)/2)*DX;y=(j-(NY-1)/2)*DY
  ink=1<=i<=7 and 1<=j<=6 and PATTERN[j-1][i-1]=='1'
  if ink:INK.append(name)
  shapes=[box((DX*.98,DY*.98,.00030))]
  if ink:
   shape=box((DX*.95,DY*.95,.00004),(0,0,-.00017),(.8,.03,.05));shape['collision']=False;shapes.append(shape)
  BODIES.append(body(name,PAPER+[x,y,0],shapes,mass=.000006,color=(.95,.93,.85),friction=.6,contact_offset=.00005))
  for di,dj in [(-1,0),(0,-1)]:
   if i+di>=0 and j+dj>=0:
    prev=f'paper_{i+di}_{j+dj}';a=np.array([-di*DX/2,-dj*DY/2,0])
    JOINTS.append(joint(f'sheet_{i}_{j}_{di}_{dj}',prev,name,a,-a,axes=bend_axes(.0000005,.0000001),break_force=1.5,break_torque=.006))
  JOINTS.append(joint('tack_'+name,'forearm',name,[0,0,ARM_RADIUS],[0,0,0],axes=bend_axes(.0000001,.0000001),break_force=.20,enabled=False,collision=True))
SPONGE=np.array([.34,-.16,TABLE+.019])
BODIES.append(body('sponge',SPONGE,[box((.040,.040,.015))],mass=.012,color=(.85,.67,.16),friction=.9))
PADCOUNT=16
for i,(x,y) in enumerate([(x,y) for x in [-.015,-.005,.005,.015] for y in [-.015,-.005,.005,.015]]):
 name='sponge_pad_'+str(i);rel=np.array([x,y,-.009])
 BODIES.append(body(name,SPONGE+rel,[box((.010,.010,.003))],mass=.00075,color=(.87,.71,.20),friction=.8))
 axes=fixed_axes();axes['transZ']=dict(limits=(-.001,.007),stiffness=100.,damping=.2)
 for axis in ['rotX','rotY']:axes[axis]=dict(limits=(-45,45),stiffness=.0001,damping=.0001)
 JOINTS.append(joint('compression_'+str(i),'sponge',name,rel,[0,0,0],axes=axes,break_force=30.))
BODIES.append(body('sponge_dish',[.34,-.16,TABLE+.003],[box((.070,.070,.006))]+[box((.070,.003,.015),(0,s*.034,.006)) for s in [-1,1]]+[box((.003,.070,.015),(s*.034,0,.006)) for s in [-1,1]],mass=.08,color=(.65,.73,.80)))
finalize(BODIES,JOINTS)
