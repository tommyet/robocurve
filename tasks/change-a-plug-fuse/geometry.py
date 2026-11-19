"""A full-size moulded UK plug, removable fuse carrier and passive retaining clips."""
from geometry_helpers import *
BODIES=[];JOINTS=[]
PLUG=np.array([.28,.08,TABLE+.014]);FC=np.array([.009,.012,.009]);FUSE_LENGTH=.0254;FUSE_RADIUS=.00315
# Rectangular pin face with rounded outer corners, three actual-sized pins,
# a moulded cord exit and the open internal space below the fuse carrier.
outer=[box((.064,.045,.008),(0,0,-.008)),box((.064,.009,.014),(0,-.018,.003)),box((.064,.005,.014),(0,.020,.003)),box((.008,.031,.014),(-.028,-.002,.003)),box((.006,.024,.014),(.029,-.0055,.003)),box((.006,.007,.012),(.029,.010,.002)),box((.027,.019,.014),(.001,-.006,.003))]
for x,y,size,height in [(-.010,-.0111,(.00635,.004),.0177),(-.010,.0111,(.00635,.004),.0177),(.0122,0,(.004,.008),.0227)]:
 outer.append(box((size[0],size[1],height),(x,y,.010+height/2),(.69,.59,.28)))
outer += [cylinder(.004,.09,(0,-.067,-.005),Rotation.from_euler('x',90,degrees=True).as_quat(),(.16,.16,.17))]
BODIES.append(body('plug',PLUG,outer,mass=.065,color=(.90,.89,.84),friction=.9,contact_offset=.0001,torsional_patch_radius=.008,min_torsional_patch_radius=.004))
# The lowered right-wall section is the ordinary screwdriver access notch.
# A fuse carrier's face is the ordinary pry point. Its four sprung fingers
# retain the cartridge beneath it; no artificial robot handle is added.
CARRIER_OFFSET=FC+[.003,0,.005]
CARRIER=PLUG+CARRIER_OFFSET
BODIES.append(body('carrier',CARRIER,[box((.037,.009,.0015)),box((.002,.009,.004),(.0175,0,-.002)),box((.002,.009,.002),(-.0175,0,-.001))],mass=.0035,color=(.19,.20,.22),friction=.8,contact_offset=.0001))
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
# Two long-side detents retain the cover without overlapping the plug pins.
for sign in [-1,1]:
 pos=CARRIER+[0,sign*.0055,-.001]
 name='cover_detent_'+('p' if sign>0 else 'n')
 # A bevel on each side of the catch converts carrier motion into outward
 # spring deflection during removal and refitting, as in a moulded snap tab.
 vertices=[[x,y,z] for x in [-.0025,.0025] for y,z in [(-sign*.0012,.0015),(sign*.0006,.0005),(sign*.0006,.0025)]]
 catch=dict(kind='mesh',points=vertices,faces=[[0,2,1],[3,4,5],[0,1,4,3],[1,2,5,4],[2,0,3,5]],pos=[0,0,0],quat=[0,0,0,1])
 BODIES.append(body(name,pos,[box((.005,.001,.004)),catch],mass=.0002,color=(.89,.88,.83)))
 JOINTS.append(joint(name+'_spring','plug',name,pos-PLUG+[0,0,-.002],[0,0,-.002],axes={**fixed_axes(),'rotX':dict(limits=(-35,35),stiffness=.055,damping=.0001)},break_force=25.,break_torque=.1))
TOOL=np.array([.28,-.14,TABLE+.028])
# 169 mm ordinary flat screwdriver, 3 mm blade. Its shaft gives the two
# grippers room while the tip levers the carrier notch.
BODIES.append(body('screwdriver',TOOL,[cylinder(.009,.070,(0,-.015,0),Rotation.from_euler('x',90,degrees=True).as_quat(),(.20,.45,.72)),cylinder(.002,.088,(0,.061,0),Rotation.from_euler('x',90,degrees=True).as_quat(),(.68,.70,.72)),box((.003,.014,.0008),(0,.112,0),(.68,.70,.72))],mass=.040,color=(.2,.45,.72),friction=.8,contact_offset=.0001,torsional_patch_radius=.005,min_torsional_patch_radius=.003))
BODIES.append(body('tool_rest',[TOOL[0],TOOL[1]-.025,TABLE+.0095],[box((.030,.020,.019))],fixed=True,mass=.05,color=(.58,.43,.27)))
BODIES.append(body('shaft_rest',[TOOL[0],TOOL[1]+.080,TABLE+.013],[box((.020,.020,.026))],fixed=True,mass=.02,color=(.58,.43,.27)))
BODIES.append(body('parts_dish',[.29,-.16,TABLE+.010],[box((.085,.070,.003)),box((.003,.070,.016),(-.043,0,.006)),box((.003,.070,.016),(.043,0,.006)),box((.085,.003,.016),(0,-.035,.006)),box((.085,.003,.016),(0,.035,.006))],fixed=False,mass=.1,color=(.60,.73,.63)))
# Ordinary raised parts tray catches the freed carrier and keeps the thin part
# reachable by the long precision fingers. It supplies no attachment.
CATCH_TRAY=np.array([.330,-.016,TABLE+.050])
BODIES.append(body('carrier_catch_tray',CATCH_TRAY-[0,0,.025],[box((.090,.070,.050)),box((.003,.070,.008),(-.045,0,.029)),box((.003,.070,.008),(.045,0,.029)),box((.090,.003,.008),(0,-.035,.029)),box((.090,.003,.008),(0,.035,.029))],fixed=True,mass=.15,color=(.60,.73,.63)))
# Turn the plug's access notch toward the right arm. Joint anchors are local
# and retain their original coordinates when the entire plug assembly turns.
PLUG_ROT=Rotation.from_euler('z',-90,degrees=True)
for part in BODIES:
 if part['name'] in ['plug','carrier','old_fuse'] or part['name'].startswith(('terminal_','carrier_grip_','cover_detent_')):
  part['pos']=(PLUG+PLUG_ROT.apply(np.asarray(part['pos'])-PLUG)).tolist()
  part['quat']=(PLUG_ROT*Rotation.from_quat(part.get('quat',[0,0,0,1]))).as_quat().tolist()
CARRIER=PLUG+PLUG_ROT.apply(CARRIER_OFFSET)
finalize(BODIES,JOINTS)
