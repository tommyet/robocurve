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
p.add(3,'pinch the free rim',{'left':(L+[.010,0,0],RL,.07),'right':(Q+[.010,0,0],RR,.07)})
p.add(4,'lift and stretch the cap opening',{'left':(CAP+[0,.095,.20],RL,.07),'right':(CAP+[0,-.095,.20],RR,.07)})
p.add(4,'bring the stretched cap over the crown',{'left':(HEAD+[0,.095,.215],RL,.07),'right':(HEAD+[0,-.095,.215],RR,.07)})
p.add(7,'pull the reversible cap over the head',{'left':(HEAD+[.030,.085,.020],RL,.07),'right':(HEAD+[.030,-.085,.020],RR,.07)})
p.add(1,'open the left grip in place',{'left':(HEAD+[.030,.085,.020],RL,.4)})
p.add(2,'slide the left fingers clear',{'left':(HEAD+[-.12,.15,.09],RL,.4)})
p.add(1,'open the right grip in place',{'right':(HEAD+[.030,-.085,.020],RR,.4)})
p.add(2,'slide the right fingers clear',{'right':(HEAD+[-.12,-.15,.09],RR,.4)})
p.add(1,'open both hands clear of the cap',{'left':(HEAD+[-.12,.15,.09],RL,.7),'right':(HEAD+[-.12,-.15,.09],RR,.7)})
p.add(4,'inspect after release',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
