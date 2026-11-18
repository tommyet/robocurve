"""Ordinary pin brush, steel pin-tail comb, and freely bending hair bundles."""
from geometry_helpers import *
BODIES=[];JOINTS=[]
BRUSH=np.array([.30,.015,TABLE+.017])
# A 190 mm brush: 95 mm head and 95 mm handle. Head contacts a rubber mat.
BODIES.append(body('mat',[.30,.015,TABLE+.002],[box((.12,.16,.004))],fixed=True,mass=.08,color=(.23,.31,.35),friction=1.))
shapes=[box((.052,.095,.010)),sphere((.026,.0475,.005)),box((.021,.095,.009),(0,.09,0))]
BODIES.append(body('brush',BRUSH,shapes,mass=.08,color=(.75,.24,.33),friction=.9,torsional_patch_radius=.006,min_torsional_patch_radius=.003))
for i in range(7):
 for j in range(11):
  pos=np.array([(i-3)*.007,(j-5)*.007,.013]);name=f'pin_{i}_{j}'
  BODIES.append(body(name,BRUSH+pos,[cylinder(.00085,.016),sphere((.0013,)*3,(0,0,.008))],mass=.00012,color=(.90,.88,.77),contact_offset=.0001))
  JOINTS.append(joint(name+'_root','brush',name,pos,[0,0,0],axes=fixed_axes(),break_force=18.,break_torque=.12))
# Ten loose locks represent 1 g of shed hair. Each lock is a 0.8 mm contact
# proxy for many finer hairs; it is neither rigid nor glued to the brush.
HAIRS=10;SEGMENTS=28
for strand in range(HAIRS):
 y=-.030+strand*.006;u=np.linspace(-1,1,SEGMENTS+1)
 # Each strand snakes between neighbouring pins, with two loose ends.
 points=np.c_[.037*u,y+.0028*np.sin(4*np.pi*u+strand*.55),.008+.002*np.cos(3*np.pi*u+strand*.6)]+BRUSH
 for i,(a,b) in enumerate(zip(points[:-1],points[1:])):
  v=b-a;length=np.linalg.norm(v);R=Rotation.align_vectors([v/length],[[1,0,0]])[0]
  part=body(f'hair_{strand}_{i}',(a+b)/2,[box((length,.0008,.0008))],mass=.0001/SEGMENTS,color=(.12+.018*(strand%3),.065,.025),quat=R.as_quat().tolist(),friction=.5,contact_offset=.0001,linear_damping=.15,angular_damping=.1)
  I=part['mass']*length*length/12;part['inertia']=[max(I/15,1e-12),max(I,1e-12),max(I,1e-12)];BODIES.append(part)
  if i:
   previous=BODIES[-2];axes={axis:dict(limits=(-180,180),stiffness=2e-7,damping=1e-8) for axis in ('rotX','rotY','rotZ')}
   JOINTS.append(joint(f'hair_join_{strand}_{i}',previous['name'],part['name'],[previous['shapes'][0]['size'][0]/2,0,0],[-length/2,0,0],axes=axes))
TOOL=np.array([.43,-.10,TABLE+.027])
# 200 mm comb: 100 mm plastic toothed section and 100 mm steel pin-tail.
comb=[box((.012,.090,.004),(0,-.020,0)),cylinder(.0009,.105,(0,.0775,0),Rotation.from_euler('x',90,degrees=True).as_quat(),(.67,.69,.72))]
comb += [box((.017,.0012,.004),(.009,-.060+i*.003,0)) for i in range(26)]
BODIES.append(body('comb',TOOL,comb,mass=.016,color=(.15,.44,.61),friction=.9,torsional_patch_radius=.005,min_torsional_patch_radius=.002))
BODIES.append(body('comb_rest',[.43,-.145,TABLE+.0125],[box((.030,.020,.025))],fixed=True,mass=.03,color=(.58,.43,.27)))
BODIES.append(body('comb_tail_rest',[.43,-.045,TABLE+.013],[box((.020,.020,.026))],fixed=True,mass=.02,color=(.58,.43,.27)))
BODIES.append(body('waste_dish',[.30,.16,TABLE+.012],[box((.12,.11,.003)),box((.004,.11,.020),(-.06,0,.008)),box((.004,.11,.020),(.06,0,.008)),box((.12,.004,.020),(0,-.055,.008)),box((.12,.004,.020),(0,.055,.008))],fixed=False,mass=.12,color=(.77,.84,.75),friction=.7))
finalize(BODIES,JOINTS)
