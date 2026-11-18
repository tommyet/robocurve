"""A full-size moulded UK plug, removable fuse carrier and passive retaining clips."""
from geometry_helpers import *
BODIES=[];JOINTS=[]
PLUG=np.array([.20,.025,TABLE+.014]);FC=np.array([.009,.012,.009]);FUSE_LENGTH=.0254;FUSE_RADIUS=.00315
# Rectangular pin face with rounded outer corners, three actual-sized pins,
# a moulded cord exit and the open internal space below the fuse carrier.
outer=[box((.054,.045,.008),(0,0,-.008)),box((.054,.009,.014),(0,-.018,.003)),box((.054,.005,.014),(0,.020,.003)),box((.008,.031,.014),(-.024,-.002,.003)),box((.006,.031,.014),(.026,-.002,.003)),box((.027,.019,.014),(.001,-.006,.003))]
for x,y,size,height in [(-.010,-.0111,(.00635,.004),.0177),(-.010,.0111,(.00635,.004),.0177),(.0122,0,(.004,.008),.0227)]:
 outer.append(box((size[0],size[1],height),(x,y,.010+height/2),(.69,.59,.28)))
outer += [cylinder(.004,.09,(0,-.067,-.005),Rotation.from_euler('x',90,degrees=True).as_quat(),(.16,.16,.17))]
BODIES.append(body('plug',PLUG,outer,mass=.065,color=(.90,.89,.84),friction=.9,torsional_patch_radius=.008,min_torsional_patch_radius=.004))
# A fuse carrier's face is the ordinary pry point. Its four sprung fingers
# retain the cartridge beneath it; no artificial robot handle is added.
CARRIER=PLUG+FC+[0,0,.005]
BODIES.append(body('carrier',CARRIER,[box((.032,.009,.0015)),box((.002,.009,.004),(.015,0,-.002)),box((.002,.009,.002),(-.015,0,-.001))],mass=.0035,color=(.19,.20,.22),friction=.8))
Q=Rotation.from_euler('y',90,degrees=True).as_quat()
def fuse(name,pos,marked=False):
 sh=[cylinder(FUSE_RADIUS,FUSE_LENGTH,quat=Q,color=(.90,.88,.79))]
 for sign in [-1,1]:sh.append(cylinder(FUSE_RADIUS+.0001,.0048,(sign*.0103,0,0),Q,(.69,.70,.72)))
 sh.append(cylinder(FUSE_RADIUS+.00002,.0018,(0,0,0),Q,(.68,.11,.11)))
 if marked:sh.append(box((.003,.001,.001),(0,-.0032,.0015),(.10,.10,.10)))
 BODIES.append(body(name,pos,sh,mass=.0065,color=(.9,.89,.83),friction=.4,contact_offset=.0001,torsional_patch_radius=.0015,min_torsional_patch_radius=.0005))
fuse('old_fuse',PLUG+FC,True)
SPARE=np.array([.40,-.105,TABLE+.016]);fuse('spare_fuse',SPARE)
BODIES.append(body('spare_rest',[SPARE[0],SPARE[1],TABLE+.006],[box((.018,.018,.012))],mass=.01,fixed=True,color=(.58,.43,.27)))
# Terminal clips are copper-alloy spring leaves, not gravity-only cradles.
# Their approximate spring response gives newton-scale extraction resistance.
def clip_pair(prefix,parent,parent_pos,centre,x,width,stiffness,color,from_top=False):
 for sign in [-1,1]:
  z=centre[2]+(.005 if from_top else -.003)
  origin=np.array([centre[0]+x,centre[1]+sign*.0031,z]);dz=-.003 if from_top else .003
  sh=[box((width,.00065,.006),(0,0,dz)),box((width,.0017,.0013),(0,-sign*.0006,2*dz))]
  name=prefix+('_p' if sign>0 else '_n')
  BODIES.append(body(name,origin,sh,mass=.00015,color=color,friction=.4,contact_offset=.00008))
  axes={**fixed_axes(),'rotX':dict(limits=(-35,35),stiffness=stiffness,damping=.0001)}
  JOINTS.append(joint(name+'_spring',parent,name,origin-parent_pos,[0,0,0],axes=axes,break_force=20.,break_torque=.08))
for sign in [-1,1]:
 clip_pair('terminal_'+('p' if sign>0 else 'n'),'plug',PLUG,PLUG+FC,sign*.010,.004,.045,(.70,.56,.25))
 clip_pair('carrier_grip_'+('p' if sign>0 else 'n'),'carrier',CARRIER,PLUG+FC,sign*.004,.0025,.025,(.19,.20,.22),True)
# Shallow face detents create passive retention of the carrier in the plug.
for sign in [-1,1]:
 pos=CARRIER+[sign*.014,0,-.001]
 name='cover_detent_'+('p' if sign>0 else 'n')
 BODIES.append(body(name,pos,[box((.001,.005,.004)),box((.0014,.005,.0008),(-sign*.0005,0,.0018))],mass=.0002,color=(.89,.88,.83)))
 JOINTS.append(joint(name+'_spring','plug',name,pos-PLUG+[0,0,-.002],[0,0,-.002],axes={**fixed_axes(),'rotY':dict(limits=(-35,35),stiffness=.055,damping=.0001)},break_force=25.,break_torque=.1))
TOOL=np.array([.36,-.14,TABLE+.028])
# 169 mm ordinary flat screwdriver, 3 mm blade. Its shaft gives the two
# grippers room while the tip levers the carrier notch.
BODIES.append(body('screwdriver',TOOL,[cylinder(.009,.070,(0,-.015,0),Rotation.from_euler('x',90,degrees=True).as_quat(),(.20,.45,.72)),cylinder(.002,.088,(0,.061,0),Rotation.from_euler('x',90,degrees=True).as_quat(),(.68,.70,.72)),box((.003,.014,.0008),(0,.112,0),(.68,.70,.72))],mass=.040,color=(.2,.45,.72),friction=.8,torsional_patch_radius=.005,min_torsional_patch_radius=.003))
BODIES.append(body('tool_rest',[TOOL[0],TOOL[1]-.025,TABLE+.0095],[box((.030,.020,.019))],fixed=True,mass=.05,color=(.58,.43,.27)))
BODIES.append(body('shaft_rest',[TOOL[0],TOOL[1]+.080,TABLE+.013],[box((.020,.020,.026))],fixed=True,mass=.02,color=(.58,.43,.27)))
BODIES.append(body('parts_dish',[.29,-.16,TABLE+.010],[box((.085,.070,.003)),box((.003,.070,.016),(-.043,0,.006)),box((.003,.070,.016),(.043,0,.006)),box((.085,.003,.016),(0,-.035,.006)),box((.085,.003,.016),(0,.035,.006))],fixed=False,mass=.1,color=(.60,.73,.63)))
finalize(BODIES,JOINTS)
