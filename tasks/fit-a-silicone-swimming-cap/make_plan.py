from pathlib import Path
import json,numpy as np
from planner import Plan
from geometry import HEAD,CAP
p=Plan()
# Approach from the front, pinch normal to the rim wall, then lower the
# stretched cap over an upright, adult-sized headform.
RL=np.array([[0,0,1],[-1,0,0],[0,-1,0.]])
RR=RL.copy()
L=CAP+[0,.060,.002];R=CAP+[0,-.060,.002]
p.add(3,'move outside the cap before approaching',{'left':(L+[0,.12,.14],RL,.4),'right':(R+[0,-.12,.14],RR,.4)},'joint')
p.add(3,'approach opposite parts of the cap rim',{'left':(L+[-.05,0,-.025],RL,.4),'right':(R+[-.05,0,-.025],RR,.4)})
p.add(2,'place fingers around the hanging rim',{'left':(L+[0,0,-.025],RL,.5),'right':(R+[0,0,-.025],RR,.5)})
p.add(2,'raise the pads around the free rim',{'left':(L,RL,.5),'right':(R,RR,.5)})
p.add(2,'centre the open jaws on the observed rim',{'left':(L,RL,.5),'right':(R,RR,.5)})
p.add(2,'pinch the plain rim',{'left':(L,RL,0.),'right':(R,RR,0.)})
p.add(4,'lift and stretch the cap opening',{'left':(CAP+[0,.095,.210],RL,0.),'right':(CAP+[0,-.095,.210],RR,0.)})
p.add(4,'centre the opening above the crown',{'left':([HEAD[0],.095,CAP[2]+.210],RL,0.),'right':([HEAD[0],-.095,CAP[2]+.210],RR,0.)})
p.add(6,'lower the cap over the crown',{'left':(HEAD+[0,.095,.045],RL,0.),'right':(HEAD+[0,-.095,.045],RR,0.)})
p.add(2,'release the stretched rim',{'left':(HEAD+[0,.095,.045],RL,.7),'right':(HEAD+[0,-.095,.045],RR,.7)})
p.add(3,'withdraw both hands',{'left':(HEAD+[-.08,.15,.075],RL,.7),'right':(HEAD+[-.08,-.15,.075],RR,.7)})
p.add(4,'leave the cap in place',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
