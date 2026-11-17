"""One half avocado, retained pit and damageable flesh; no fixed fruit fixture."""
from geometry_helpers import *
BODIES=[];JOINTS=[]
C=np.array([.34,0,TABLE+.031]);PIT=C+[0,-.012,.018]
BODIES.append(body('board',[.34,0,TABLE+.009],[box((.30,.24,.018))],mass=1.,fixed=True,color=(.64,.40,.19)))
# Skin and lower flesh support a hollow upper socket, rather than a solid sphere.
skin=[sphere((.032,.050,.002),(0,0,-.011),(.12,.22,.06)),sphere((.024,.019,.012),(0,.033,0),(.14,.28,.07))]
# A low base and a socket wall leave actual collision clearance under the pit.
for t in np.arange(12)*2*np.pi/12:skin.append(sphere((.010,.011,.009),(.027*np.sin(t),-.012+.028*np.cos(t),-.004),(.33,.45,.10)))
BODIES.append(body('fruit',C,skin,mass=.065,color=(.14,.23,.06)))
for i,t in enumerate(np.arange(12)*2*np.pi/12):
 rel=np.array([.027*np.sin(t),-.012+.028*np.cos(t),.006]);name=f'flesh_{i:02d}'
 BODIES.append(body(name,C+rel,[sphere((.010,.011,.011))],mass=.0045,color=(.69,.78,.24),exclude=[f'flesh_{j:02d}' for j in range(12) if j!=i]))
 JOINTS.append(joint('flesh_bond_'+str(i),'fruit',name,rel,[0,0,0],axes=fixed_axes(),break_force=12.,break_torque=.08))
BODIES.append(body('stone',PIT,[sphere((.018,.019,.018))],mass=.018,color=(.42,.21,.10),friction=.6))
JOINTS.append(joint('stone_bond','fruit','stone',PIT-C,[0,0,0],axes=fixed_axes(),break_force=7.,break_torque=.045,collision=True))
DISH=np.array([.34,-.18,TABLE+.002])
BODIES.append(body('dish',DISH,[cylinder(.055,.004)]+ring(.055,.024,.004,z=.010),mass=.10,color=(.7,.75,.8)))

finalize(BODIES,JOINTS)
