"""Curved helmet visor, paired spring release catches and replacement shield."""
from geometry_helpers import *
BODIES=[];JOINTS=[]
HELMET=np.array([.40,.08,TABLE+.15]);PIVOT=np.array([0,0,.025]);OPEN=Rotation.from_euler('y',-70,degrees=True).as_matrix()
# Full-size inert helmet on a fixed wooden display stand, not on a person.
shell=sphere((.145,.118,.145));BODIES.append(body('helmet',HELMET,[shell],mass=1.4,fixed=True,color=(.24,.29,.32),friction=.5))
BODIES.append(body('stand',[.4,.08,TABLE+.007],[cylinder(.11,.014)],mass=.6,fixed=True,color=(.4,.28,.15)))
PINS={s:np.array([0,sign*.132,.025]) for s,sign in [('left',1),('right',-1)]}
for side,sign in [('left',1),('right',-1)]:
 pin=PINS[side]
 BODIES.append(body('base_'+side,HELMET+pin,[box((.045,.012,.050))],mass=.025,fixed=True,color=(.12,.14,.16)))
 button=pin+np.array([.024,sign*.003,.010])
 BODIES.append(body('trigger_'+side,HELMET+button,[box((.010,.014,.014))],mass=.005,color=(.75,.20,.10),friction=.7))
 axes=fixed_axes();axes['transX']=dict(limits=(-.004,0),stiffness=650.,damping=.3)
 JOINTS.append(joint('trigger_slide_'+side,'helmet','trigger_'+side,button,[0,0,0],axes=axes,break_force=60.))
# The shield is 2 mm polycarbonate represented by curved segments, joined to
# two compliant ears. The shell remains solid; the unused face opening isn't
# removed because the task only contacts the outside visor and hinge bases.
NEW=np.array([.17,-.30,TABLE+.09]);STARTS={'old':HELMET+PIVOT-OPEN@PIVOT,'new':NEW};ROTS={'old':OPEN,'new':OPEN}
for tag in ['old','new']:
 origin=STARTS[tag];Q=ROTS[tag];shapes=[]
 for a in np.linspace(-np.pi/2,np.pi/2,25)[:-1]+np.pi/48:
  # Narrow native convex panels retain the curved hollow interior.
  c=np.array([.157*np.cos(a),.137*np.sin(a),-.005])
  shapes.append(box((.002,.018,.085),c,quat=Rotation.from_euler('z',a).as_quat()))
 BODIES.append(body(tag+'_visor',origin,shapes,quat=Rotation.from_matrix(Q).as_quat(),mass=.095,color=((.40,.51,.58) if tag=='old' else (.65,.78,.84)),friction=.6,contact_offset=.0002))
 for side,sign in [('left',1),('right',-1)]:
  pin=PINS[side];ear=pin+np.array([.012,0,.010])
  BODIES.append(body(tag+'_ear_'+side,origin+Q@ear,[box((.032,.005,.026))],quat=Rotation.from_matrix(Q).as_quat(),mass=.006,color=(.32,.40,.44),friction=.8))
  axes=bend_axes(.35,.003,10)
  JOINTS.append(joint(tag+'_ear_flex_'+side,tag+'_visor',tag+'_ear_'+side,ear,[0,0,0],axes=axes,break_force=40.,break_torque=.6))
  axes=fixed_axes();axes['rotY']=dict(limits=(0,72),stiffness=0.,damping=.001)
  JOINTS.append(joint(tag+'_hinge_'+side,'helmet',tag+'_ear_'+side,pin,pin-ear,q0=Rotation.from_matrix(OPEN).as_quat(),axes=axes,enabled=(tag=='old'),collision=False,break_force=80.,break_torque=1.))
# Two padded display blocks support the spare in its open fitting orientation.
for y in [-.41,-.19]:
 BODIES.append(body('spare_support_'+str(y).replace('-','n').replace('.','p'),[.17,y,TABLE+.035],[box((.045,.035,.070))],fixed=True,mass=.2,color=(.48,.40,.28)))
TRAY=np.array([.18,.32,TABLE+.006]);BODIES.append(body('tray',TRAY,[box((.31,.28,.012))],mass=.5,fixed=True,color=(.45,.37,.26)))
finalize(BODIES,JOINTS)
