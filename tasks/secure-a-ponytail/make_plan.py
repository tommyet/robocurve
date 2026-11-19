from pathlib import Path
import json,numpy as np
from planner import Plan
from scipy.spatial.transform import Rotation as Rot
from geometry import ELASTIC,HEAD
p=Plan()
RL=Rot.from_euler('y',-30,degrees=True).as_matrix()@np.array([[0,-1,0],[-1,0,0],[0,0,-1.]])
RR=RL.copy()
L=ELASTIC+[0,.0175,.002];R=ELASTIC+[0,-.0175,.002]
p.add(3,'approach the plain elastic from its two sides',{'left':(L+[0,0,.055],RL,.20),'right':(R+[0,0,.055],RR,.20)},'joint')
p.add(2,'place the pads around opposite parts of the elastic',{'left':(L,RL,.20),'right':(R,RR,.20)})
p.add(2,'grip the elastic',{'left':(L,RL,.09),'right':(R,RR,.09)})
p.add(4,'lift and stretch the elastic',{'left':(ELASTIC+[0,.050,.065],RL,.09),'right':(ELASTIC+[0,-.050,.065],RR,.09)})
p.add(4,'place the opening beneath the loose hair ends',{'left':([.300,.050,HEAD[2]-.235],RL,.09),'right':([.300,-.050,HEAD[2]-.235],RR,.09)})
p.add(7,'bring the loose hair through the elastic',{'left':([.300,.050,HEAD[2]-.130],RL,.09),'right':([.300,-.050,HEAD[2]-.130],RR,.09)})
p.add(3,'let the elastic gather the ponytail',{'left':([.300,.026,HEAD[2]-.130],RL,.09),'right':([.300,-.026,HEAD[2]-.130],RR,.09)})
p.add(2,'release the elastic',{'left':([.300,.026,HEAD[2]-.130],RL,.18),'right':([.300,-.026,HEAD[2]-.130],RR,.18)})
p.add(2,'withdraw the fingertips from inside the elastic',{'left':([.300,.026,HEAD[2]-.115],RL,.18),'right':([.300,-.026,HEAD[2]-.115],RR,.18)})
p.add(3,'withdraw from the ponytail',{'left':([.25,.11,HEAD[2]-.10],RL,.18),'right':([.25,-.11,HEAD[2]-.10],RR,.18)})
p.add(1,'open clear of the head',{'left':([.25,.11,HEAD[2]-.10],RL,.6),'right':([.25,-.11,HEAD[2]-.10],RR,.6)})
p.add(4,'released inspection',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
