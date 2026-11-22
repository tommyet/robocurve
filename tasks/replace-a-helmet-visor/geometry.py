"""Curved helmet visor, paired spring release catches and replacement shield."""
from geometry_helpers import *
BODIES=[];JOINTS=[]
HELMET=np.array([.22,0,TABLE+.135]);PIVOT=np.array([0,0,.025]);OPEN=Rotation.from_euler('y',-70,degrees=True).as_matrix()
# Full-size inert helmet on a fixed wooden display stand, not on a person.
shell=sphere((.145,.118,.125));BODIES.append(body('helmet',HELMET,[shell],mass=1.4,fixed=True,color=(.24,.29,.32),friction=.5))
BODIES.append(body('stand',[.22,0,TABLE+.007],[cylinder(.11,.014)],mass=.6,fixed=True,color=(.4,.28,.15)))
PINS={s:np.array([0,sign*.132,.025]) for s,sign in [('left',1),('right',-1)]}
for side,sign in [('left',1),('right',-1)]:
 pin=PINS[side]
 BODIES.append(body('base_'+side,HELMET+pin+np.array([0,-sign*.012,0]),[box((.045,.012,.050))],mass=.025,fixed=True,color=(.12,.14,.16)))
# The shield is 2 mm polycarbonate represented by curved segments, joined to
# two compliant ears. The shell remains solid; the unused face opening isn't
# removed because the task only contacts the outside visor and hinge bases.
NEW=np.array([.17,-.30,TABLE+.048]);STARTS={'old':HELMET+PIVOT-OPEN@PIVOT,'new':NEW};ROTS={'old':OPEN,'new':np.eye(3)}
for tag in ['new']:
 origin=STARTS[tag];Q=ROTS[tag];shapes=[]
 for a in np.linspace(-np.pi/2,np.pi/2,25)[:-1]+np.pi/48:
  # Narrow native convex panels retain the curved hollow interior.
  c=np.array([.157*np.cos(a),.137*np.sin(a),-.005])
  shapes.append(box((.002,.018,.085),c,quat=Rotation.from_euler('z',a).as_quat()))
 BODIES.append(body(tag+'_visor',origin,shapes,quat=Rotation.from_matrix(Q).as_quat(),mass=.095,color=((.40,.51,.58) if tag=='old' else (.65,.78,.84)),friction=.6,contact_offset=.0002))
 for side,sign in [('left',1),('right',-1)]:
  pin=PINS[side];ear=pin+np.array([.012,0,.010])
  BODIES.append(body(tag+'_ear_'+side,origin+Q@ear,[box((.032,.005,.026))],quat=Rotation.from_matrix(Q).as_quat(),mass=.006,color=(.32,.40,.44),friction=.8))
  axes=bend_axes(3.,.03,10)
  JOINTS.append(joint(tag+'_ear_flex_'+side,tag+'_visor',tag+'_ear_'+side,ear,[0,0,0],axes=axes,break_force=40.,break_torque=.6))
  # Compliant plastic seating avoids an infinite impulse at snap engagement.
  axes={a:dict(limits=(-.003,.003),stiffness=300.,damping=2.5,max_force=3.) for a in ['transX','transY','transZ']}
  axes.update({a:dict(limits=(-6,6),stiffness=.2,damping=.03,max_force=.05) for a in ['rotX','rotZ']})
  axes['rotY']=dict(limits=(0,72),stiffness=.8,damping=.03,max_force=.7)
  JOINTS.append(joint(tag+'_hinge_'+side,'helmet',tag+'_ear_'+side,pin,pin-ear,q0=Rotation.from_matrix(OPEN).as_quat(),q1=[0,0,0,1],axes=axes,enabled=(tag=='old'),collision=False,break_force=80.,break_torque=1.))
finalize(BODIES,JOINTS)
