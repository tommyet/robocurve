from pathlib import Path
import numpy as np,json
from planner import Plan
from scipy.spatial.transform import Rotation
from geometry import POINTS,GRIP_IDS,HEAD,TOWEL
from common import TABLE
RL=np.array([[0,-1,0],[0,0,-1],[1,0,0.]])
RR=np.array([[0,-1,0],[0,0,1],[-1,0,0.]])
RL=Rotation.from_euler('z',20,degrees=True).as_matrix()@RL
RR=Rotation.from_euler('z',-20,degrees=True).as_matrix()@RR
p=Plan();L=POINTS[GRIP_IDS[0]].copy();Q=POINTS[GRIP_IDS[1]].copy()
p.add(4,'approach outside the towel edges',{'left':(L+[0,.02,.05],RL,.30),'right':(Q+[0,-.02,.05],RR,.30)},'joint')
p.add(3,'lower beside the hanging hems',{'left':(L+[0,.02,0],RL,.30),'right':(Q+[0,-.02,0],RR,.30)})
p.add(3,'enclose the towel hems',{'left':(L,RL,.30),'right':(Q,RR,.30)})
p.add(4,'pinch the towel hems',{'left':(L,RL,.09),'right':(Q,RR,.09)})
for z in [TABLE+.16,TABLE+.22,TABLE+.28,TABLE+.32]:
 p.add(4,'lift the open towel to the next section',{'left':([.36,.085,z],RL,.09),'right':([.36,-.085,z],RR,.09)})
 p.add(4,'fold and gently squeeze the section',{'left':([.36,.024,z],RL,.09),'right':([.36,-.024,z],RR,.09)})
 p.add(6,'blot without rubbing',{})
 p.add(3,'open the towel clear of the section',{'left':([.36,.085,z],RL,.09),'right':([.36,-.085,z],RR,.09)})
p.add(4,'lower the towel to its rack',{'left':(L,RL,.09),'right':(Q,RR,.09)})
p.add(2,'release the towel',{'left':(L,RL,.6),'right':(Q,RR,.6)})
p.add(4,'withdraw clear',{'left':(L+[.04,.04,.16],RL,.7),'right':(Q+[.04,-.04,.16],RR,.7)})
p.add(4,'inspect the released result',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
