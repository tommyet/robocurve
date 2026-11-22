"""Full-size local roof-edge assembly, gutter scoop, bucket and flexible dry leaves."""
from geometry_helpers import *
BODIES=[];JOINTS=[]
GUTTER=np.array([.40,0,TABLE+.17]);RADIUS=.056;LENGTH=.60
# Half-round PVC rain gutter, open upwards, with a real fascia and overhang.
shapes=[]
for a in np.linspace(np.pi,2*np.pi,25)[:-1]+np.pi/48:
 x=RADIUS*np.cos(a);z=RADIUS*np.sin(a)
 shapes.append(box((np.pi*RADIUS/24+.001,LENGTH,.003),(x,0,z),quat=Rotation.from_euler('y',-a-np.pi/2).as_quat()))
shapes += [box((.112,.003,.056),(0,y,-.028)) for y in [-.30,.30]]
shapes += [box((.018,.62,.18),(.080,0,.015),color=(.55,.37,.22)),box((.20,.62,.014),(.14,0,.055),color=(.25,.26,.28))]
# Bracket crosses the access opening at the far edge of this leaf-filled bay.
shapes += [box((.118,.018,.008),(0,.15,.002),color=(.27,.28,.29)),box((.035,.018,.13),(.065,.15,-.055))]
BODIES.append(body('roof_edge',GUTTER,shapes,mass=6.,fixed=True,color=(.75,.77,.78),friction=.45))
# Bench-safe timber legs, securing a local 1:1 roof section at reachable height.
for y in [-.24,.24]:
 BODIES.append(body('support_'+str(y).replace('-','n').replace('.','p'),[.48,y,TABLE+.045],[box((.06,.06,.09))],mass=.4,fixed=True,color=(.55,.37,.22)))
BUCKET=np.array([.48,-.42,TABLE+.075]);BUCKET_R=.085
BODIES.append(body('bucket',BUCKET,[cylinder(BUCKET_R,.004,(0,0,-.073)),*ring(BUCKET_R,.15,.003,n=32)],mass=.30,color=(.18,.37,.56),friction=.8))
# Plastic gutter scoop with a thin bevelled mouth and open top, not a grasp tool.
SCOOP=np.array([.18,.02,TABLE+.009]);HANDLE=np.array([0,-.12,.013])
points=[[-.025,-.055,0],[.025,-.055,0],[-.025,.055,0],[.025,.055,0],[-.025,-.055,.004],[.025,-.055,.004],[-.025,.055,.0005],[.025,.055,.0005]]
faces=[(0,2,3,1),(4,5,7,6),(0,1,5,4),(1,3,7,5),(2,6,7,3),(0,4,6,2)]
scoop=[dict(kind='mesh',points=points,faces=faces),box((.003,.11,.025),(-.0265,0,.0125)),box((.003,.11,.025),(.0265,0,.0125)),box((.053,.003,.025),(0,-.0565,.0125)),box((.018,.14,.014),(0,-.12,.013))]
BODIES.append(body('scoop',SCOOP,scoop,mass=.085,color=(.88,.42,.12),friction=.7))
LEAVES=[];SEEDS=[]
for i in range(12):
 x=GUTTER[0]+[-.015,0,.015][i%3];y=-.09+(i//3)*.045
 z=GUTTER[2]-np.sqrt(RADIUS**2-(x-GUTTER[0])**2)+.003+(i%3)*.001
 angle=[-20,15,40][i%3];R=Rotation.from_euler('z',angle,degrees=True);origin=np.array([x,y,z]);names=[]
 for j in range(4):
  name=f'leaf_{i}_{j}';names.append(name);width=[.013,.026,.026,.013][j]
  pos=origin+R.apply([0,(j-1.5)*.015,abs(j-1.5)*.001])
  BODIES.append(body(name,pos,[box((width,.015-.00002,.0004))],quat=R.as_quat(),mass=.0003/4,color=(.41+.02*(i%3),.32,.14),friction=.45,contact_offset=.00015,speculative_ccd=True))
  if j:
   # Anchors include the shallow curl, held by passive bending stiffness.
   a=BODIES[-2];b=BODIES[-1];mid=(np.array(a['pos'])+np.array(b['pos']))/2
   JOINTS.append(joint(f'leaf_flex_{i}_{j}',names[-2],name,R.inv().apply(mid-a['pos']),R.inv().apply(mid-b['pos']),axes=bend_axes(.00004,.000001,120)))
 LEAVES.append(names)
finalize(BODIES,JOINTS)
