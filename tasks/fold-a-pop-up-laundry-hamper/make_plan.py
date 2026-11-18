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
p.add(2,'grip the spring frames',{'left':(L,RL,0.),'right':(R,RR,0.)})
p.add(4,'lift the flattened hamper',{'left':(L+[0,-.015,.10],RL,0.),'right':(R+[0,.015,.10],RR,0.)})
for i in range(1,9):
 u=i/8;a=Rot.from_euler('y',90*u,degrees=True).as_matrix()@grip(-50-30*u,-1);b=Rot.from_euler('y',-90*u,degrees=True).as_matrix()@grip(50+30*u,-1)
 lp=L+[.025*np.sin(np.pi*u),-.015-.160*u,.10+.020*u];rp=R+[-.025*np.sin(np.pi*u),.015+.160*u,.10+.020*u]
 p.add(1.5,'counter-twist and bring the loops together',{'left':(lp,a,0.),'right':(rp,b,0.)})
for i in range(1,9):
 u=i/8;a=Rot.from_euler('y',90+90*u,degrees=True).as_matrix()@grip(-80,-1);b=Rot.from_euler('y',-90-90*u,degrees=True).as_matrix()@grip(80,-1)
 lp=L+[.015*u,-.175-.055*u,.12-.08*u];rp=R+[-.015*u,.175+.055*u,.12-.08*u]
 p.add(1.5,'finish the counter-twist and nest the loops',{'left':(lp,a,0.),'right':(rp,b,0.)})
from common import down,TABLE
centre=np.array([.29,0,TABLE])
left_hold=centre+[-.025,.035,.060];right_hold=centre+[.040,-.035,.060]
p.add(1,'release the left edge',{'left':(lp,a,.55)})
p.add(2,'withdraw the left hand',{'left':(lp+[-.06,.08,.12],down(180),.55)},'joint')
p.add(3,'approach the far loop',{'left':([.33,.185,.91],down(180),0.),'right':(rp+[0,0,-.05],b,0.)})
p.add(5,'fold the far loop onto the centre',{'left':(left_hold,down(180),0.)})
p.add(1,'release the right edge',{'right':(rp+[0,0,-.05],b,.55)})
p.add(2,'withdraw the right hand',{'right':(rp+[0,-.10,.15],down(),.55)},'joint')
p.add(3,'approach the right outer loop',{'right':([.40,0,1.01],down(),0.)})
p.add(5,'stack the right loop',{'right':(right_hold,down(),0.)})
p.add(3,'approach the left outer loop',{'left':([.20,0,1.01],down(180),0.)})
p.add(5,'stack the left loop',{'left':(left_hold,down(180),0.)})
p.add(3,'inspect the stacked loops while held',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
