from pathlib import Path
import json,numpy as np
from planner import Plan
from geometry import HEAD,CAP
from common import down
p=Plan()
c=np.cos(np.radians(0));s=np.sin(np.radians(0))
RL=np.array([[0,-1,0],[s,0,-c],[c,0,s]])
RR=np.array([[0,-1,0],[s,0,c],[-c,0,s]])
L=CAP+[0,.080,0];R=CAP+[0,-.080,0]
p.add(3,'approach the loose cap from the sides',{'left':(L+[0,.02,.03],RL,.60),'right':(R+[0,-.02,.03],RR,.60)},'joint')
p.add(3,'place the pads around the free rim',{'left':(L,RL,.60),'right':(R,RR,.60)})
p.add(2,'pinch opposite sides of the rim',{'left':(L,RL,.09),'right':(R,RR,.09)})
p.add(4,'lift and stretch the opening',{'left':(CAP+[0,.095,.15],RL,.09),'right':(CAP+[0,-.095,.15],RR,.09)})
p.add(4,'place the stretched cap above the head',{'left':([HEAD[0],.095,HEAD[2]+.145],RL,.09),'right':([HEAD[0],-.095,HEAD[2]+.145],RR,.09)})
p.add(7,'pull the cap over the crown',{'left':(HEAD+[0,.095,.045],RL,.09),'right':(HEAD+[0,-.095,.045],RR,.09)})
p.add(2,'release the rim',{'left':(HEAD+[0,.095,.045],RL,.7),'right':(HEAD+[0,-.095,.045],RR,.7)})
p.add(3,'withdraw from the fitted cap',{'left':(HEAD+[-.08,.13,.075],RL,.7),'right':(HEAD+[-.08,-.13,.075],RR,.7)})
p.add(4,'inspect after release',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
