"""Complete robot-only replacement sequence; native validation is pending."""
from pathlib import Path
import json,numpy as np
from scipy.spatial.transform import Rotation as Rot
from planner import Plan
from geometry import PLUG,CARRIER,TOOL,FC,PLUG_ROT
from common import down
p=Plan();RL=Rot.from_euler('x',45,degrees=True).as_matrix()@np.array([[1.,0,0],[0,0,-1],[0,1,0]]);RR=down(180);RT=down(180);L=PLUG+[0,.018,0]
p.add(3,'approach the open plug',{'left':(L+[0,.07,0],RL,.65),'right':(TOOL+[0,0,.07],down(180),.5)},'joint')
p.add(2,'grip the moulded plug body',{'left':(L,RL,.65)})
p.add(2,'close the supporting fingers',{'left':(L,RL,0.)})
p.add(3,'lift the unplugged plug for access',{'left':(L+[0,-.08,.075],RL,0.)})
from sequence import append_plan
append_plan(p,left_return=(L+[0,-.08,.075],RL,0.))
p.add(4,'return the plug to the table',{'left':(L,RL,0.)})
p.add(1,'release the plug',{'left':(L,RL,.7)})
p.add(3,'withdraw both hands',{'left':(L+[0,.08,.06],RL,.7)})
p.add(4,'inspect the released parts',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
