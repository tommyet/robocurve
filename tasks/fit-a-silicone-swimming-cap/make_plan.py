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
p.add(1,'centre the open fingers beside the rim',{'left':(L+[.024,0,0],RL,.35),'right':(Q+[.024,0,0],RR,.35)})
p.add(3,'pinch the free rim',{'left':(L+[.024,0,0],RL,.03),'right':(Q+[.024,0,0],RR,.03)})
p.add(4,'lift and stretch the cap opening',{'left':(CAP+[0,.095,.20],RL,.03),'right':(CAP+[0,-.095,.20],RR,.03)})
p.add(4,'bring the stretched cap over the crown',{'left':(HEAD+[0,.095,.215],RL,.03),'right':(HEAD+[0,-.095,.215],RR,.03)})
p.add(3,'hook the front rim over the forehead',{'left':(HEAD+[-.065,.095,.090],RL,.03),'right':(HEAD+[-.065,-.095,.090],RR,.03)})
p.add(4,'draw the cap back over the crown',{'left':(HEAD+[.040,.095,.045],RL,.03),'right':(HEAD+[.040,-.095,.045],RR,.03)})
p.add(2,'open both grips in place',{'left':(HEAD+[.040,.095,.045],RL,.5),'right':(HEAD+[.040,-.095,.045],RR,.5)})
p.add(3,'slide both hands laterally clear',{'left':(HEAD+[.040,.16,.070],RL,.5),'right':(HEAD+[.040,-.16,.070],RR,.5)})
p.add(2,'withdraw both open hands',{'left':(HEAD+[0,.20,.15],RL,.7),'right':(HEAD+[0,-.20,.15],RR,.7)})
p.add(4,'inspect after release',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
