"""Opposite short-edge grips, counter-twist and three-loop folding probe."""
from pathlib import Path
import json,numpy as np
from scipy.spatial.transform import Rotation as Rot
from geometry import GRIP_POINTS,CENTER
from planner import Plan
p=Plan()
def grip(angle,sign):
 a=np.radians(angle);z=np.array([np.cos(a),np.sin(a),0.]);x=np.array([0.,0.,sign]);return np.column_stack([x,np.cross(z,x),z])
RL=grip(-50,1);RR=grip(50,-1);L,R=GRIP_POINTS
p.add(3,'approach opposite bound ends',{'left':(L-.04*RL[:,2],RL,.3),'right':(R-.04*RR[:,2],RR,.3)},'joint')
p.add(2,'enclose the bound edges',{'left':(L,RL,.25),'right':(R,RR,.25)})
p.add(2,'grip the spring frames',{'left':(L,RL,0.),'right':(R,RR,0.)})
p.add(4,'lift the flattened hamper',{'left':(L+[0,-.015,.13],RL,0.),'right':(R+[0,.015,.13],RR,0.)})
for i in range(1,9):
 u=i/8;a=Rot.from_euler('x',90*u,degrees=True).as_matrix()@RL;b=Rot.from_euler('x',-90*u,degrees=True).as_matrix()@RR
 lp=L+[.025*np.sin(np.pi*u),-.015-.160*u,.13+.045*u];rp=R+[-.025*np.sin(np.pi*u),.015+.160*u,.13+.045*u]
 p.add(1.5,'counter-twist and bring the loops together',{'left':(lp,a,0.),'right':(rp,b,0.)})
p.add(3,'inspect the fold while held',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
