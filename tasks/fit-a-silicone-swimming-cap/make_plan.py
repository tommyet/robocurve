from pathlib import Path
import json,numpy as np
from planner import Plan
from geometry import HEAD,CAP
from common import down
p=Plan()
c=np.cos(np.radians(30));s=np.sin(np.radians(30))
RL=np.array([[0,-1,0],[-c,0,-s],[s,0,-c]])
RR=np.array([[0,-1,0],[-c,0,s],[-s,0,-c]])
L=CAP+[0,.060,.002];R=CAP+[0,-.060,.002]
p.add(3,'approach the loose cap',{'left':(L+[0,.05,.03],RL,.18),'right':(R+[0,-.05,.03],RR,.18)},'joint')
p.add(3,'lower the open pads around the rim',{'left':(L,RL,.18),'right':(R,RR,.18)})
p.add(2,'pinch opposite sides of the rim',{'left':(L,RL,0.),'right':(R,RR,0.)})
p.add(4,'lift and stretch the opening',{'left':(CAP+[0,.095,.10],RL,0.),'right':(CAP+[0,-.095,.10],RR,0.)})
p.add(4,'place the stretched cap above the head',{'left':([HEAD[0],.095,HEAD[2]+.23],RL,0.),'right':([HEAD[0],-.095,HEAD[2]+.23],RR,0.)})
p.add(7,'pull the plain reversible cap over the crown',{'left':(HEAD+[0,.095,.045],RL,0.),'right':(HEAD+[0,-.095,.045],RR,0.)})
p.add(2,'release the rim',{'left':(HEAD+[0,.095,.045],RL,.7),'right':(HEAD+[0,-.095,.045],RR,.7)})
p.add(3,'withdraw from the fitted cap',{'left':(HEAD+[-.08,.13,.075],RL,.7),'right':(HEAD+[-.08,-.13,.075],RR,.7)})
p.add(4,'inspect after release',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
