from pathlib import Path
import json,numpy as np
from planner import Plan
from common import down,TABLE
from geometry import HEAD,CAP
from scipy.spatial.transform import Rotation
p=Plan();RL=np.array([[0,-1,0],[0,0,-1],[1,0,0.] ]);RR=np.array([[0,-1,0],[0,0,1],[-1,0,0.] ]);T=Rotation.from_euler('y',-90,degrees=True).as_matrix()
L=CAP+[0,.060,.002];R=CAP+[0,-.060,.002]
p.add(3,'approach opposite parts of the cap rim',{'left':(L+[0,.045,.008],RL,.4),'right':(R+[0,-.045,.008],RR,.4)},'joint')
p.add(2,'lower fingers around the rim',{'left':(L,RL,.3),'right':(R,RR,.3)})
p.add(2,'grip the plain rim',{'left':(L,RL,0.),'right':(R,RR,0.)})
p.add(4,'lift and stretch the cap opening',{'left':(CAP+[0,.095,.09],RL,0.),'right':(CAP+[0,-.095,.09],RR,0.)})
p.add(4,'turn the cap toward the supported head',{'left':([.23,.095,HEAD[2]],T@RL,0.),'right':([.23,-.095,HEAD[2]],T@RR,0.)})
p.add(6,'draw the opening over the crown',{'left':([.36,.095,HEAD[2]],T@RL,0.),'right':([.36,-.095,HEAD[2]],T@RR,0.)})
p.add(2,'release the stretched rim',{'left':([.36,.095,HEAD[2]],T@RL,.7),'right':([.36,-.095,HEAD[2]],T@RR,.7)})
p.add(3,'withdraw both hands',{'left':([.28,.14,HEAD[2]+.03],T@RL,.7),'right':([.28,-.14,HEAD[2]+.03],T@RR,.7)})
p.add(4,'leave the cap in place',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
