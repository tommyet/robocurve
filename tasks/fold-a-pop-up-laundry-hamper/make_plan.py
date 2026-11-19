"""Opposite short-edge grips, counter-twist and three-loop folding probe."""
from pathlib import Path
import json,numpy as np
from scipy.spatial.transform import Rotation as Rot
from geometry import GRIP_POINTS,CENTER
from planner import Plan
def grip(angle,sign):
 a=np.radians(angle);z=np.array([np.cos(a),np.sin(a),0.]);x=np.array([0.,0.,sign]);return np.column_stack([x,np.cross(z,x),z])
def twist(base,angle):
 # Share the turn between a reachable wrist bend and forearm roll, keeping
 # the housing farther from the emerging outer loop.
 old=Rot.from_euler('y',angle,degrees=True).as_matrix()@base
 rolled=base@Rot.from_euler('z',angle,degrees=True).as_matrix()
 return old@Rot.from_rotvec(.4*Rot.from_matrix(old.T@rolled).as_rotvec()).as_matrix()
RL=grip(-50,-1);RR=grip(50,-1);L,R=GRIP_POINTS
from pad_covers import configure_kinematics
configure_kinematics()
from yam_arena import ik,station
from yam_arena.constants import READY
from scipy.optimize import least_squares
initial=np.r_[READY,.1172,READY,.1172]
for side,o,point,ori in [('left',0,L,RL),('right',7,R,RR)]:
 def residual(q):
  pp,rr=ik.tcp_pose(q,station.BASES[side]);return np.r_[3*(pp-point),.08*ik._rot_error(ori,rr)]
 candidates=[least_squares(residual,seed,bounds=(ik.LOWER,ik.UPPER),max_nfev=500) for seed in [initial[o:o+6],(ik.LOWER+ik.UPPER)/2]]
 sol=min(candidates,key=lambda x:np.linalg.norm(x.fun));pos,actual_R=ik.tcp_pose(sol.x,station.BASES[side])
 assert np.linalg.norm(pos-point)<.0003 and np.linalg.norm(ik._rot_error(ori,actual_R))<.08,('pre-held reset unreachable',side,sol.fun)
 initial[o:o+6]=sol.x
 if side=='left':RL=actual_R
 else:RR=actual_R
Path(__file__).with_name('initial-action.json').write_text(json.dumps({'action14':initial.tolist(),'description':'Both hands already hold the full-size, uncoiled bound edges at real opposing-pad contacts.'},indent=2)+'\n')
p=Plan(initial)
# Preserve the original controller phase numbering; these reset-only entries
# are excluded from timed execution and never move task material.
for count,label in [(60,'approach opposite bound ends'),(40,'enclose the bound edges'),(40,'grip the spring frames')]:
 p.frames.extend(dict(action14=initial.tolist(),stage=label) for _ in range(count))
p.add(4,'lift the flattened hamper',{'left':(L+[0,-.015,.07],RL,.10),'right':(R+[0,.015,.07],RR,.10)})
for i in range(1,9):
 u=i/8;a=twist(grip(-50-30*u,-1),90*u);b=twist(grip(50+30*u,-1),-90*u)
 lp=L+[.025*np.sin(np.pi*u),-.015-.160*u,.07+.020*u];rp=R+[-.025*np.sin(np.pi*u),.015+.160*u,.07+.020*u]
 p.add(1.5,'counter-twist and bring the loops together',{'left':(lp,a,.10),'right':(rp,b,.10)})
for i in range(1,9):
 u=i/8;a=twist(grip(-80,-1),90+75*u);b=twist(grip(80,-1),-90-75*u)
 lp=L+[.055*u,-.175-.105*u,.09-.05*u+.14*np.sin(np.pi*u)];rp=R+[-.055*u,.175+.105*u,.09-.07*u]
 p.add(1.5,'finish the counter-twist and nest the loops',{'left':(lp,a,.10),'right':(rp,b,.10)})
from common import down,TABLE
RP=Rot.from_euler('y',-30,degrees=True).as_matrix()@down(0)
# Lower the central crossing, then lay the two upright outer loops down.
# Closed fingers press the raised loops down against the table; no regrasp is assumed.
# Every frame/cloth point stays native.
lp=lp.copy();rp=rp.copy();lp[2]=TABLE+.028;rp[2]=TABLE+.012
p.add(6,'lower the nested loops against the table',{'left':(lp,a,.10),'right':(rp,b,.10)})
p.add(1,'hold the central crossing',{})
p.add(1,'release the left edge above the table',{'left':(lp,a,.20)})
p.add(2,'clear the left fingers',{'left':(lp+[0,0,.085],a,.20)})
p.add(3,'approach the left outer loop',{'left':([.30,0,1.02],down(0),.03)})
p.add(2,'enclose the left outer loop',{'left':([.30,0,.98],down(0),.03)})
p.add(2,'pinch the left outer loop',{'left':([.30,0,.96],down(0),.03)})
p.add(6,'stack the left loop',{'left':([.39,.045,TABLE+.025],down(0),.03)})
p.add(1,'hold the first outer loop down',{})
p.add(1,'release the right edge',{'right':(rp,b,.20)})
p.add(2,'clear the right fingers',{'right':(rp+[0,0,.085],b,.20)})
p.add(3,'approach the right outer loop',{'right':([.50,0,1.02],RP,.03)},'joint')
p.add(2,'enclose the right outer loop',{'right':([.50,0,.98],RP,.03)})
p.add(2,'pinch the right outer loop',{'right':([.50,0,.96],RP,.03)})
p.add(6,'stack the right loop',{'right':([.42,-.045,TABLE+.025],RP,.03)})
p.add(4,'inspect the flat packet while both hands press',{})
# Retain the compact coils with their ordinary attached elastic loop.
p.add(2,'hold the packet beside the retaining path',{'right':([.43,-.025,TABLE+.025],RP,.03)})
p.add(2,'clear the left hand for the retainer',{'left':([.39,.14,TABLE+.16],grip(-80,1),.45)})
p.add(3,'approach the loose retaining loop',{'left':([.39,.11,TABLE+.055],grip(-80,1),.35)})
p.add(2,'pinch the retaining loop',{'left':([.39,.11,TABLE+.055],grip(-80,1),.05)})
p.add(3,'lift the retaining loop over the packet',{'left':([.39,.11,1.02],grip(-80,1),.05)})
p.add(5,'stretch the loop across the packet',{'left':([.39,-.15,1.00],grip(-80,1),.05)})
p.add(4,'slip the loop below the far edge',{'left':([.39,-.15,TABLE+.018],grip(-80,1),.05)})
p.add(1,'release the retaining loop',{'left':([.39,-.15,TABLE+.018],grip(-80,1),.25)})
p.add(3,'clear the left fingers from the loop',{'left':([.28,-.15,.98],grip(-80,1),.25)})
p.add(3,'remove the supporting hand',{'right':([.50,-.16,.94],grip(80,-1),.25)})
p.add(1,'open both hands away from the packet',{'left':([.28,-.15,.98],grip(-80,1),.7),'right':([.50,-.16,.94],grip(80,-1),.7)})
p.add(4,'inspect the secured released packet',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
