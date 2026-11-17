"""Flexible trouser cuff with a loose turned hem and an open sprung safety pin."""
from geometry_helpers import *
BODIES=[];JOINTS=[]
NX,NY=18,10;DX,DY=.010,.024;C=np.array([.34,.12,TABLE+.006]);HEM=[]
# Both faces of a real flattened tubular leg, with a previously turned 20 mm hem.
for layer in ['front','back']:
 for i in range(NX):
  for j in range(NY):
   name=f'{layer}_{i}_{j}';pos=C+[(i-(NX-1)/2)*DX,(j-4.5)*DY,0 if layer=='front' else -.003]
   BODIES.append(body(name,pos,[box((DX*.99,DY*.99,.001))],mass=.0005,color=(.13,.19,.26),friction=.8))
   for di,dj in [(-1,0),(0,-1)]:
    if i+di>=0 and j+dj>=0:
     a=np.array([-di*DX/2,-dj*DY/2,0]);JOINTS.append(joint(f'cloth_{layer}_{i}_{j}_{di}_{dj}',f'{layer}_{i+di}_{j+dj}',name,a,-a,axes=bend_axes(.000002,.000001),break_force=10.,break_torque=.04))
for j in range(NY):
 for i in [0,NX-1]:JOINTS.append(joint(f'side_seam_{i}_{j}',f'front_{i}_{j}',f'back_{i}_{j}',[0,0,-.0015],[0,0,.0015],axes=bend_axes(.000004,.000002),break_force=20.))
for i in range(NX):
 for j in range(2):
  name=f'hem_{i}_{j}';pos=C+[(i-(NX-1)/2)*DX,-.115+j*.010,.0015];HEM.append(name)
  BODIES.append(body(name,pos,[box((DX*.99,.0099,.001))],mass=.00025,color=(.16,.22,.30),friction=.8))
  if j==0:JOINTS.append(joint('fold_'+str(i),f'front_{i}_0',name,[0,-.012,.00075],[0,-.005,-.00075],axes=bend_axes(.000003,.000001),break_force=10.))
  else:JOINTS.append(joint('hem_across_'+str(i),f'hem_{i}_0',name,[0,.005,0],[0,-.005,0],axes=bend_axes(.000002,.000001),break_force=10.))
  if i:JOINTS.append(joint(f'hem_along_{i}_{j}',f'hem_{i-1}_{j}',name,[DX/2,0,0],[-DX/2,0,0],axes=bend_axes(.000002,.000001),break_force=10.))
# Only the central 60 mm is loose; original stitching supports the rest of the hem.
for i in range(NX):
 if not 6<=i<12:
  JOINTS.append(joint('existing_stitch_'+str(i),f'front_{i}_0',f'hem_{i}_1',[0,.003,.0015],[0,0,0],axes=bend_axes(.000002,.000001),break_force=12.))
# Commercial-size 50 mm steel safety pin. Spring hinge is open at rest.
PIN=np.array([.46,-.11,TABLE+.004]);Q=Rotation.from_euler('z',90,degrees=True)
BODIES.append(body('pin_frame',PIN,[rod_between([0,0,0],[.045,0,0],.00065),cylinder(.003,.0015,quat=Rotation.from_euler('y',90,degrees=True).as_quat()),box((.007,.005,.002),(.045,0,.002))],mass=.0018,color=(.7,.72,.74),quat=list(Q.as_quat()),friction=.8,contact_offset=.00005))
openR=Q*Rotation.from_euler('y',-25,degrees=True)
BODIES.append(body('pin_arm',PIN,[rod_between([0,0,0],[.043,0,0],.00065)],mass=.0007,color=(.7,.72,.74),quat=list(openR.as_quat()),contact_offset=.00005))
axes=fixed_axes();axes['rotY']=dict(limits=(-5,35),stiffness=.20,damping=.002)
JOINTS.append(joint('pin_spring','pin_frame','pin_arm',[0,0,0],[0,0,0],axes=axes,break_force=50.,break_torque=.35))
cone=dict(kind='mesh',points=[[-.001,0,.0006],[-.001,.0006,0],[-.001,0,-.0006],[-.001,-.0006,0],[.001,0,0]],faces=[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(0,3,2,1)])
BODIES.append(body('needle_point',PIN+openR.apply([.044,0,0]),[cone],mass=.0001,color=(.7,.72,.74),quat=list(openR.as_quat()),contact_offset=.00003))
axes=fixed_axes();axes['transX']=dict(limits=(-.001,.0001),stiffness=5000.,damping=.5)
JOINTS.append(joint('point_compression','pin_arm','needle_point',[.044,0,0],[0,0,0],axes=axes,break_force=50.))
JOINTS.append(joint('pin_catch','pin_frame','pin_arm',[.043,0,.001],[.043,0,0],axes=fixed_axes(),enabled=False,break_force=15.,break_torque=.10))
for b in list(BODIES):
 if b['name'].startswith(('front_','back_','hem_')):
  axes=bend_axes(0.,.000001,179);axes['transY']=dict(limits=(1,-1));axes['transZ']=dict(limits=(1,-1));axes['transX']=dict(limits=(-.043,.001),stiffness=0.,damping=.05,max_force=.5)
  JOINTS.append(joint('hole_'+b['name'],'pin_arm',b['name'],[.045,0,0],[0,0,0],axes=axes,enabled=False,break_force=3.,break_torque=.02))
# An ordinary wooden sewing support sits inside the cuff, separating its faces.
# The turned front edge overhangs it by 26 mm so a fingertip can get underneath.
cloth=[b for b in BODIES if b['name'].startswith(('front_','back_','hem_'))]
old={b['name']:(np.array(b['pos']),Rotation.from_quat(b.get('quat',[0,0,0,1]))) for b in cloth}
def height(x):return .026-min(1.,max(0.,(abs(x-.34)-.065)/.020))*.023
for b in cloth:
 x,y,z=b['pos'];back=b['name'].startswith('back_');hem=b['name'].startswith('hem_')
 slope=(height(x+.0001)-height(x-.0001))/.0002 if not back else 0.
 rot=Rotation.from_euler('y',-np.arctan(slope));b['quat']=rot.as_quat().tolist()
 b['pos']=[x,.27-y,TABLE+(.003 if back else height(x)+(.0015 if hem else 0.))]
 b['mass']=.00004 if hem else .00008;b['shapes'][0]['size'][0]*=np.sqrt(1+slope*slope)
lookup={b['name']:b for b in BODIES}
for j in JOINTS:
 if j['a'] in old and j['b'] in old:
  a,ra=old[j['a']];b,rb=old[j['b']];point=(a+ra.apply(j['p0'])+b+rb.apply(j['p1']))/2
  back=j['a'].startswith('back_') and j['b'].startswith('back_')
  extra=.0015*sum(n.startswith('hem_') for n in [j['a'],j['b']])/2
  point=np.array([point[0],.27-point[1],TABLE+(.003 if back else height(point[0])+extra)])
  for side,name in enumerate([j['a'],j['b']]):
   spec=lookup[name];j['p'+str(side)]=Rotation.from_quat(spec['quat']).inv().apply(point-spec['pos']).tolist()
  for axis in ['rotX','rotY','rotZ']:
   if 'stiffness' in j['axes'][axis]:j['axes'][axis]['stiffness']=.0001 if j['name'].startswith(('fold_','hem_')) else .00002
BODIES.append(body('sewing_support',[.34,.144,TABLE+.014],[box((.140,.200,.020))],mass=.25,fixed=True,color=(.62,.43,.25)))
for b in BODIES:
 if b['name'].startswith(('front_','back_','hem_')) or b['name']=='sewing_support':b['pos'][1]-=.15
finalize(BODIES,JOINTS)
