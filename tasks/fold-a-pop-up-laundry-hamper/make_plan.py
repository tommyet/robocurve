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
p.add(2,'grip the spring frames',{'left':(L,RL,.11),'right':(R,RR,.11)})
p.add(4,'lift the flattened hamper',{'left':(L+[0,-.015,.10],RL,.11),'right':(R+[0,.015,.10],RR,.11)})
for i in range(1,9):
 u=i/8;a=Rot.from_euler('y',90*u,degrees=True).as_matrix()@grip(-50-30*u,-1);b=Rot.from_euler('y',-90*u,degrees=True).as_matrix()@grip(50+30*u,-1)
 lp=L+[.025*np.sin(np.pi*u),-.015-.160*u,.10+.020*u];rp=R+[-.025*np.sin(np.pi*u),.015+.160*u,.10+.020*u]
 p.add(1.5,'counter-twist and bring the loops together',{'left':(lp,a,.11),'right':(rp,b,.11)})
for i in range(1,9):
 u=i/8;a=Rot.from_euler('y',90+90*u,degrees=True).as_matrix()@grip(-80,-1);b=Rot.from_euler('y',-90-90*u,degrees=True).as_matrix()@grip(80,-1)
 lp=L+[.015*u,-.175-.055*u,.12-.08*u];rp=R+[-.015*u,.175+.055*u,.12-.08*u]
 p.add(1.5,'finish the counter-twist and nest the loops',{'left':(lp,a,.11),'right':(rp,b,.11)})
from common import down,TABLE
# Keep both native edge grips while the table nests the twisted loops.
lp=lp.copy();rp=rp.copy();lp[2]=TABLE+.028;rp[2]=TABLE+.028
p.add(6,'lower the nested loops against the table',{'left':(lp,a,.11),'right':(rp,b,.11)})
p.add(3,'hold the loops compact for inspection',{})
# Keep both edge grips while turning the tools upright, then use the tabletop
# to nest the spring loops. This adds no object control or material change.
p.add(6,'turn the held packet down toward the table',{'left':(lp+[0,0,.015],down(180),.11),'right':(rp+[0,0,.015],down(),.11)})
p.add(6,'press the held loops flat',{'left':(lp+[0,0,-.005],down(180),.11),'right':(rp+[0,0,-.005],down(),.11)})
p.add(3,'inspect the packet while both edges stay held',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
