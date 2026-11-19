from pathlib import Path
import numpy as np,json
from planner import Plan
from geometry import POINTS,GRIP_IDS,HEAD,TOWEL
from common import TABLE
R=np.array([[0,0,1],[-1,0,0],[0,-1,0.]])
p=Plan();L=POINTS[GRIP_IDS[0]]+[.010,0,0];Q=POINTS[GRIP_IDS[1]]+[.010,0,0]
p.add(4,'approach above and outside the towel edges',{'left':(L+[-.06,.10,.16],R,.30),'right':(Q+[-.06,-.10,.16],R,.30)},'joint')
p.add(3,'lower in front of the hanging hems',{'left':(L+[-.07,0,0],R,.30),'right':(Q+[-.07,0,0],R,.30)})
p.add(3,'enclose the towel hems',{'left':(L,R,.30),'right':(Q,R,.30)})
p.add(2,'pinch the towel hems',{'left':(L,R,.09),'right':(Q,R,.09)})
for z in [TABLE+.16,TABLE+.22,TABLE+.28,TABLE+.32]:
 p.add(4,'lift the open towel to the next section',{'left':([.36,.085,z],R,.09),'right':([.36,-.085,z],R,.09)})
 p.add(4,'fold and gently squeeze the section',{'left':([.36,.024,z],R,.09),'right':([.36,-.024,z],R,.09)})
 p.add(6,'blot without rubbing',{})
 p.add(3,'open the towel clear of the section',{'left':([.36,.085,z],R,.09),'right':([.36,-.085,z],R,.09)})
p.add(4,'lower the towel to its rack',{'left':(L,R,.09),'right':(Q,R,.09)})
p.add(2,'release the towel',{'left':(L,R,.6),'right':(Q,R,.6)})
p.add(4,'withdraw clear',{'left':(L+[.04,.04,.16],R,.7),'right':(Q+[.04,-.04,.16],R,.7)})
p.add(4,'inspect the released result',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
