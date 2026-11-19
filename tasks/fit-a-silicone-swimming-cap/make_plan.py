from pathlib import Path
import json,numpy as np
from planner import Plan
from scipy.spatial.transform import Rotation as Rot
from geometry import HEAD,CAP
from start_pose import START_ACTION
p=Plan(START_ACTION)
RL=np.array([[0,0,1],[-1,0,0],[0,-1,0.]])
RR=RL.copy()
L=CAP+[0,.080,0.];Q=CAP+[0,-.080,0.]
p.add(1,'centre the open fingers beside the rim',{'left':(L+[.010,0,0],RL,.35),'right':(Q+[.010,0,0],RR,.35)})
p.add(3,'pinch the free rim',{'left':(L+[.010,0,0],RL,.09),'right':(Q+[.010,0,0],RR,.09)})
p.add(4,'lift and stretch the cap opening',{'left':(CAP+[0,.095,.20],RL,.09),'right':(CAP+[0,-.095,.20],RR,.09)})
p.add(4,'bring the stretched cap over the crown',{'left':(HEAD+[0,.095,.215],RL,.09),'right':(HEAD+[0,-.095,.215],RR,.09)})
p.add(7,'pull the reversible cap over the head',{'left':(HEAD+[0,.095,.045],RL,.09),'right':(HEAD+[0,-.095,.045],RR,.09)})
p.add(2,'release the back edge while the front remains held',{'left':(HEAD+[-.02,.125,.045],RL,.18)})
p.add(2,'slide the back fingers clear',{'left':(HEAD+[-.12,.15,.09],RL,.18)})
p.add(2,'release the front edge',{'right':(HEAD+[-.02,-.125,.045],RR,.18)})
p.add(2,'slide the front fingers clear',{'right':(HEAD+[-.12,-.15,.09],RR,.18)})
p.add(1,'open both hands clear of the cap',{'left':(HEAD+[-.12,.15,.09],RL,.7),'right':(HEAD+[-.12,-.15,.09],RR,.7)})
p.add(4,'inspect after release',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
