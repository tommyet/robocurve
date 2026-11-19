from pathlib import Path
import json,numpy as np
from planner import Plan
from scipy.spatial.transform import Rotation as Rot
from geometry import HEAD,CAP
p=Plan()
RL=np.array([[0,0,1],[-1,0,0],[0,-1,0.]])
RR=RL.copy()
L=CAP+[0,.080,0.];Q=CAP+[0,-.080,0.]
p.add(3,'approach below the rim along its tangent',{'left':(L-.020*RL[:,2]+[0,0,-.012],RL,.35),'right':(Q-.020*RR[:,2]+[0,0,-.012],RR,.35)},'joint')
p.add(3,'slide the open fingers beneath the rolled rim',{'left':(L+[0,0,-.010],RL,.35),'right':(Q+[0,0,-.010],RR,.35)})
p.add(1,'raise the fingers around the rolled rim',{'left':(L,RL,.35),'right':(Q,RR,.35)})
p.add(2,'pinch the free rim',{'left':(L,RL,.09),'right':(Q,RR,.09)})
p.add(4,'lift and stretch the cap opening',{'left':(CAP+[0,.095,.20],RL,.09),'right':(CAP+[0,-.095,.20],RR,.09)})
p.add(4,'bring the stretched cap over the crown',{'left':(HEAD+[0,.095,.215],RL,.09),'right':(HEAD+[0,-.095,.215],RR,.09)})
p.add(7,'pull the reversible cap over the head',{'left':(HEAD+[0,.095,.045],RL,.09),'right':(HEAD+[0,-.095,.045],RR,.09)})
p.add(2,'release the cap without opening into the head',{'left':(HEAD+[0,.095,.045],RL,.18),'right':(HEAD+[0,-.095,.045],RR,.18)})
p.add(3,'withdraw the fingertips upward',{'left':(HEAD+[-.05,.13,.15],RL,.18),'right':(HEAD+[-.05,-.13,.15],RR,.18)})
p.add(1,'open both hands clear of the cap',{'left':(HEAD+[-.05,.13,.15],RL,.7),'right':(HEAD+[-.05,-.13,.15],RR,.7)})
p.add(4,'inspect after release',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
