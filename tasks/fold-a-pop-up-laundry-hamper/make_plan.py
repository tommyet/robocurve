"""Opposite short-edge grips, counter-twist and three-loop folding probe."""
from pathlib import Path
import json,numpy as np
from scipy.spatial.transform import Rotation as Rot
from geometry import GRIP_POINTS,CENTER
from planner import Plan
p=Plan()
def grip(angle,sign):
 a=np.radians(angle);z=np.array([np.cos(a),np.sin(a),0.]);x=np.array([0.,0.,sign]);return np.column_stack([x,np.cross(z,x),z])
RL=grip(-50,-1);RR=grip(50,-1);L,R=GRIP_POINTS
p.add(3,'approach opposite bound ends',{'left':(L-.04*RL[:,2],RL,.3),'right':(R-.04*RR[:,2],RR,.3)},'joint')
p.add(2,'enclose the bound edges',{'left':(L,RL,.25),'right':(R,RR,.25)})
p.add(2,'grip the spring frames',{'left':(L,RL,.10),'right':(R,RR,.10)})
p.add(4,'lift the flattened hamper',{'left':(L+[0,-.015,.10],RL,.10),'right':(R+[0,.015,.10],RR,.10)})
for i in range(1,9):
 u=i/8;a=Rot.from_euler('y',90*u,degrees=True).as_matrix()@grip(-50-30*u,-1);b=Rot.from_euler('y',-90*u,degrees=True).as_matrix()@grip(50+30*u,-1)
 lp=L+[.025*np.sin(np.pi*u),-.015-.160*u,.10+.020*u];rp=R+[-.025*np.sin(np.pi*u),.015+.160*u,.10+.020*u]
 p.add(1.5,'counter-twist and bring the loops together',{'left':(lp,a,.10),'right':(rp,b,.10)})
for i in range(1,9):
 u=i/8;a=Rot.from_euler('y',90+75*u,degrees=True).as_matrix()@grip(-80,-1);b=Rot.from_euler('y',-90-75*u,degrees=True).as_matrix()@grip(80,-1)
 lp=L+[.055*u,-.175-.105*u,.12-.08*u+.14*np.sin(np.pi*u)];rp=R+[-.055*u,.175+.105*u,.12-.10*u]
 p.add(1.5,'finish the counter-twist and nest the loops',{'left':(lp,a,.10),'right':(rp,b,.10)})
from common import down,TABLE
# Lower the central crossing, then lay the two upright outer loops down.
# These are ordinary hand motions; every frame/cloth point stays native.
lp=lp.copy();rp=rp.copy();lp[2]=TABLE+.028;rp[2]=TABLE+.012
p.add(6,'lower the nested loops against the table',{'left':(lp,a,.10),'right':(rp,b,.10)})
p.add(1,'hold the central crossing',{})
p.add(1,'release the right edge above the table',{'right':(rp,b,.20)})
p.add(2,'clear the right fingers',{'right':(rp+[0,0,.085],b,.20)})
p.add(3,'approach the right outer loop',{'right':([.50,0,1.00],grip(80,-1),.07)})
p.add(6,'stack the right loop',{'right':([.42,-.045,TABLE+.045],grip(80,-1),.07)})
p.add(1,'hold the first outer loop down',{})
p.add(1,'release the left edge',{'left':(lp,a,.20)})
p.add(2,'clear the left fingers',{'left':(lp+[0,0,.085],a,.20)})
p.add(3,'approach the left outer loop',{'left':([.30,0,1.00],grip(-80,1),.07)})
p.add(6,'stack the left loop',{'left':([.39,.045,TABLE+.045],grip(-80,1),.07)})
p.add(4,'inspect the flat packet while both hands press',{})
# Retain the compact coils with their ordinary attached elastic loop.
p.add(2,'hold the packet beside the retaining path',{'right':([.485,-.025,TABLE+.045],grip(80,-1),.07)})
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
