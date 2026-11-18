"""Pinch opposite bound ends from outside, then counter-twist and nest."""
from pathlib import Path
import numpy as np,json
from scipy.spatial.transform import Rotation as Rot
from planner import Plan
from geometry import BODIES,GRIP_ENDS,CENTER
p=Plan();base=np.array([[0,-1,0],[0,0,-1],[1,0,0.]])
flip=np.eye(3)
points=[np.mean([b['pos'] for b in BODIES if b['name'] in [f'wire_{f}_{i:02d}' for f in range(4)]],axis=0) for i in GRIP_ENDS]
RL=Rot.from_euler('x',30,degrees=True).as_matrix()@base@flip
RR=Rot.from_euler('x',150,degrees=True).as_matrix()@base
L=points[0]-.007*RL[:,2];R=points[1]-.007*RR[:,2]
p.add(3,'approach opposite frame ends from outside',{'left':(L-.035*RL[:,2],RL,.3),'right':(R-.035*RR[:,2],RR,.3)},'joint')
p.add(2,'enclose the four stacked frame edges',{'left':(L,RL,.3),'right':(R,RR,.3)})
p.add(2,'grip both seams',{'left':(L,RL,0.),'right':(R,RR,0.)})
p.add(2,'lift the bound ends before turning the wrists',{'left':(points[0]+[0,-.025,.04]-.007*RL[:,2],RL,0.),'right':(points[1]+[0,.025,.04]-.007*RR[:,2],RR,0.)},'joint')
RL0=Rot.from_euler('x',60,degrees=True).as_matrix()@base@flip
RR0=Rot.from_euler('x',120,degrees=True).as_matrix()@base
p.add(3,'lift clear of the table',{'left':(points[0]+[0,-.060,.10]-.007*RL0[:,2],RL0,0.),'right':(points[1]+[0,.060,.10]-.007*RR0[:,2],RR0,0.)},'joint')
for step in range(1,7):
 u=step/6;Q=Rot.from_euler('z',-45*u,degrees=True).as_matrix()
 left=Q@Rot.from_euler('y',-90*u,degrees=True).as_matrix()@RL0
 right=Q@Rot.from_euler('y',90*u,degrees=True).as_matrix()@RR0
 lp=CENTER+Q@(points[0]-CENTER+[0,-.060-.15*u,0])+[0,0,.10]-.007*left[:,2]
 rp=CENTER+Q@(points[1]-CENTER+[0,.060+.15*u,0])+[0,0,.10]-.007*right[:,2]
 p.add(2.,'counter-twist while bringing the ends together',{'left':(lp,left,0.),'right':(rp,right,0.)},'joint')
p.add(3,'bring the crossing loops together',{
 'left':(CENTER+Q@(points[0]-CENTER+[0,-.240,0])+[0,0,.115]-.007*left[:,2],left,0.),
 'right':(CENTER+Q@(points[1]-CENTER+[0,.240,0])+[0,0,.085]-.007*right[:,2],right,0.)},'joint')
p.add(3,'hold the nested frame for inspection',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
