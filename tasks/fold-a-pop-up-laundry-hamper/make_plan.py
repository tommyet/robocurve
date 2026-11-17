"""Grip the shared frame seams, then twist and nest the passive spring frames."""
from pathlib import Path
import numpy as np,json
from scipy.spatial.transform import Rotation
from planner import Plan
from common import down,TABLE
from geometry import BODIES
p=Plan();base=np.array([[0,-1,0],[0,0,-1],[1,0,0.]])
RL=Rotation.from_euler('x',35,degrees=True).as_matrix()@base;RR=Rotation.from_euler('x',145,degrees=True).as_matrix()@base
points=[np.mean([b['pos'] for b in BODIES if b['name'] in [f'wire_{f}_{i:02d}' for f in range(4)]],axis=0) for i in [12,36]]
L=points[0]-.006*RL[:,2];R=points[1]-.006*RR[:,2]
p.add(3,'approach opposite sewn frame seams',{'left':(L+[0,0,.05],RL,.3),'right':(R+[0,0,.05],RR,.3)},'joint')
p.add(2,'enclose the joined frame edges',{'left':(L,RL,.3),'right':(R,RR,.3)})
p.add(2,'grip both seams',{'left':(L,RL,0.),'right':(R,RR,0.)})
p.add(3,'lift clear of the table',{'left':(L+[0,0,.06],RL,0.),'right':(R+[0,0,.06],RR,0.)})
axis=np.array([0.,0.,1.])
for step in range(1,5):
 u=step/4;left=Rotation.from_rotvec(axis*np.radians(65*u)).as_matrix()@RL;right=Rotation.from_rotvec(axis*np.radians(-65*u)).as_matrix()@RR
 p.add(1.5,'twist the ends inward',{'left':(L+[.10*u,-.10*u,.06+.10*u],left,0.),'right':(R+[-.10*u,.10*u,.06+.10*u],right,0.)})
p.add(3,'bring the crossing loops together',{'left':(L+[.13,-.135,.14],left,0.),'right':(R+[-.13,.135,.18],right,0.)})
p.add(3,'hold the nested frame for inspection',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
