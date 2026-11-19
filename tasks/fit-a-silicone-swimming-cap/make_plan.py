from pathlib import Path
import json,numpy as np
from planner import Plan
from geometry import HEAD,CAP
from common import down
p=Plan()
# Approach tangentially just below the rim; radial jaws pinch its two sides.
RL=np.array([[0,0,1],[-1,0,0],[0,-1,0.]])
RR=np.array([[0,0,1],[-1,0,0],[0,-1,0.]])
L=CAP+[0,.080,.003];R=CAP+[0,-.080,.003]
p.add(3,'approach above and outside the loose cap',{'left':(L+[-.07,.06,.15],RL,.60),'right':(R+[-.07,-.06,.15],RR,.60)},'joint')
p.add(2,'lower outside the rim and its support',{'left':(L+[-.07,.06,0],RL,.60),'right':(R+[-.07,-.06,0],RR,.60)})
p.add(3,'slide the fingers beneath the free rim',{'left':(L,RL,.60),'right':(R,RR,.60)})
p.add(2,'pinch opposite sides of the rim',{'left':(L,RL,.09),'right':(R,RR,.09)})
p.add(4,'lift and stretch the opening',{'left':(CAP+[0,.095,.15],RL,.09),'right':(CAP+[0,-.095,.15],RR,.09)})
p.add(4,'place the stretched cap above the head',{'left':([HEAD[0],.095,HEAD[2]+.145],RL,.09),'right':([HEAD[0],-.095,HEAD[2]+.145],RR,.09)})
p.add(7,'pull the cap over the crown',{'left':(HEAD+[0,.095,.045],RL,.09),'right':(HEAD+[0,-.095,.045],RR,.09)})
p.add(2,'release the rim',{'left':(HEAD+[0,.095,.045],RL,.7),'right':(HEAD+[0,-.095,.045],RR,.7)})
p.add(3,'withdraw from the fitted cap',{'left':(HEAD+[-.08,.13,.075],RL,.7),'right':(HEAD+[-.08,-.13,.075],RR,.7)})
p.add(4,'inspect after release',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
