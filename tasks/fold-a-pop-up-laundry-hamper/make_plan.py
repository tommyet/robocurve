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
p.add(2,'grip the spring frames',{'left':(L,RL,.08),'right':(R,RR,.08)})
p.add(4,'lift the flattened hamper',{'left':(L+[0,-.015,.10],RL,.08),'right':(R+[0,.015,.10],RR,.08)})
for i in range(1,9):
 u=i/8;a=Rot.from_euler('y',90*u,degrees=True).as_matrix()@grip(-50-30*u,-1);b=Rot.from_euler('y',-90*u,degrees=True).as_matrix()@grip(50+30*u,-1)
 lp=L+[.025*np.sin(np.pi*u),-.015-.160*u,.10+.020*u];rp=R+[-.025*np.sin(np.pi*u),.015+.160*u,.10+.020*u]
 p.add(1.5,'counter-twist and bring the loops together',{'left':(lp,a,.08),'right':(rp,b,.08)})
for i in range(1,9):
 u=i/8;a=Rot.from_euler('y',90+90*u,degrees=True).as_matrix()@grip(-80,-1);b=Rot.from_euler('y',-90-90*u,degrees=True).as_matrix()@grip(80,-1)
 lp=L+[.015*u,-.175-.055*u,.12-.08*u];rp=R+[-.015*u,.175+.055*u,.12-.08*u]
 p.add(1.5,'finish the counter-twist and nest the loops',{'left':(lp,a,.08),'right':(rp,b,.08)})
from common import down,TABLE
# Lower the central crossing, then lay the two upright outer loops down.
# These are ordinary hand motions; every frame/cloth point stays native.
lp=lp.copy();rp=rp.copy();lp[2]=TABLE+.018;rp[2]=TABLE+.018
p.add(6,'lower the nested loops against the table',{'left':(lp,a,.08),'right':(rp,b,.08)})
p.add(1,'hold the central crossing',{})
p.add(1,'release the right edge above the table',{'right':(rp,b,.20)})
p.add(2,'clear the right fingers',{'right':(rp+[0,0,.085],b,.20)})
p.add(3,'approach the right outer loop',{'right':([.40,0,1.00],down(),.55)})
p.add(6,'stack the right loop',{'right':([.32,-.045,TABLE+.030],down(),.55)})
p.add(1,'hold the first outer loop down',{})
p.add(1,'release the left edge',{'left':(lp,a,.20)})
p.add(2,'clear the left fingers',{'left':(lp+[0,0,.085],a,.20)})
p.add(3,'approach the left outer loop',{'left':([.20,0,1.00],down(180),.55)})
p.add(6,'stack the left loop',{'left':([.29,.045,TABLE+.030],down(180),.55)})
p.add(4,'inspect the flat packet while both hands press',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
