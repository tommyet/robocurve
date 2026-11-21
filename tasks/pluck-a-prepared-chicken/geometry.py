"""Loose prepared carcass, yielding skin and independently retained feathers."""
from geometry_helpers import *
BODIES=[];JOINTS=[]
C=np.array([.36,0,TABLE+.070]);N=12;GROUPS=4
AXIS=np.array([-.5,0,np.sqrt(.75)]);BQ=Rotation.align_vectors([AXIS],[[0,0,1]])[0].as_quat()
tray=[box((.42,.38,.006))]+[box((.42,.006,.035),(0,y,.020)) for y in [-.187,.187]]+[box((.006,.38,.035),(x,0,.020)) for x in [-.207,.207]]
BODIES.append(body('tray',[.36,0,TABLE+.003],tray,fixed=True,mass=.8,color=(.61,.68,.70),friction=.7))
# Eviscerated small broiler: body, folded wings and drumsticks are a loose
# rigid support. Only the working breast skin is deformable in this model.
parts=[sphere((.075,.115,.060),(0,0,0)),sphere((.027,.072,.032),(-.074,0,-.009)),sphere((.027,.072,.032),(.074,0,-.009))]
for sign in [-1,1]:
 parts+=[sphere((.029,.065,.030),(sign*.052,.100,-.015)),sphere((.012,.035,.014),(sign*.060,.155,-.020))]
parts+=[sphere((.025,.030,.024),(0,-.122,-.005))]
BODIES.append(body('carcass',C,parts,mass=1.05,color=(.91,.73,.59),friction=.6,contact_offset=.0001))
SKIN=[];TIPS=[];ROOTS=[]
for row in range(GROUPS):
 y=(row-1.5)*.030
 for col in range(3):
  x=(col-1)*.021;z=.059-.20*abs(x);name=f'skin_{row}_{col}';SKIN.append(name)
  BODIES.append(body(name,C+[x,y,z],[box((.0205,.0295,.001))],mass=.0015,color=(.96,.80,.65),friction=.6,contact_offset=.0001,exclude=['carcass']))
  axes={a:dict(limits=(-.006,.006),stiffness=250.,damping=.45) for a in ['transX','transY','transZ']}
  axes.update({a:dict(limits=(-20,20),stiffness=.04,damping=.002) for a in ['rotX','rotY','rotZ']})
  JOINTS.append(joint('skin_bond_'+name,'carcass',name,[x,y,z],[0,0,0],axes=axes,break_force=2.,break_torque=.025))
for i in range(N):
 group=i//3;off=i%3-1;y=(group-1.5)*.030+off*.005;root=C+[0,y,.060];ROOTS.append(root)
 exclusions=SKIN+['carcass'];tip=root+AXIS*.020;TIPS.append(tip)
 BODIES.append(body(f'quill_{i}',root+AXIS*.002,[cylinder(.0006,.016)],quat=BQ,mass=.00005,color=(.90,.85,.70),friction=.65,exclude=exclusions,contact_offset=.00005))
 # The upper shaft and feather vane bend relative to the embedded calamus.
 shapes=[cylinder(.0006,.020)]
 # Feather barbs are visual-only, attached to the bending shaft. Their soft
 # collapse is not resolved; finger contact and extraction use the quill.
 shapes += [dict(sphere((.00025,.0033,.010),(0,0,.004),(.92,.91,.84)),collision=False)]
 BODIES.append(body(f'feather_{i}',tip,shapes,quat=BQ,mass=.00012,color=(.94,.92,.84),friction=.65,exclude=exclusions,contact_offset=.00005))
 axes=fixed_axes();axes['transZ']=dict(limits=(0.,.020),stiffness=2000.,damping=.02,max_force=.35)
 JOINTS.append(joint(f'follicle_{i}',f'skin_{group}_1',f'quill_{i}',[0,off*.005,.001]-AXIS*.006,[0,0,-.008],q0=BQ,axes=axes))
 JOINTS.append(joint(f'shaft_{i}',f'quill_{i}',f'feather_{i}',[0,0,.008],[0,0,-.010],axes=bend_axes(.002,.00003,limit=45),break_force=1.8,break_torque=.012))
finalize(BODIES,JOINTS)
