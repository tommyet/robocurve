from pathlib import Path
import json,numpy as np
from planner import Plan
from scipy.spatial.transform import Rotation as Rot
from geometry import HEAD,CAP
p=Plan()
RL=np.array([[0,-1,0],[0,0,-1],[1,0,0.]])
RR=np.array([[0,-1,0],[0,0,1],[-1,0,0.]])
RL=Rot.from_euler('x',20,degrees=True).as_matrix()@RL
RR=Rot.from_euler('x',-20,degrees=True).as_matrix()@RR
L=CAP+[0,.080,0.];Q=CAP+[0,-.080,0.]
p.add(3,'approach the open cap from its sides',{'left':(L+[0,.045,0.],RL,.25),'right':(Q+[0,-.045,0.],RR,.25)},'joint')
p.add(3,'place the fingers around opposite rim edges',{'left':(L,RL,.25),'right':(Q,RR,.25)})
p.add(1,'pinch the free rim',{'left':(L,RL,.09),'right':(Q,RR,.09)})
p.add(1,'hold the rim before lifting',{})
p.add(4,'lift and stretch the cap opening',{'left':(CAP+[0,.095,.20],RL,.09),'right':(CAP+[0,-.095,.20],RR,.09)})
p.add(4,'bring the stretched cap over the crown',{'left':(HEAD+[0,.095,.215],RL,.09),'right':(HEAD+[0,-.095,.215],RR,.09)})
p.add(7,'pull the cap over the head',{'left':(HEAD+[0,.095,.045],RL,.09),'right':(HEAD+[0,-.095,.045],RR,.09)})
p.add(2,'release the cap without opening into the head',{'left':(HEAD+[0,.095,.045],RL,.18),'right':(HEAD+[0,-.095,.045],RR,.18)})
p.add(3,'withdraw the fingertips upward',{'left':(HEAD+[-.05,.13,.15],RL,.18),'right':(HEAD+[-.05,-.13,.15],RR,.18)})
p.add(1,'open both hands clear of the cap',{'left':(HEAD+[-.05,.13,.15],RL,.7),'right':(HEAD+[-.05,-.13,.15],RR,.7)})
p.add(4,'inspect after release',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
