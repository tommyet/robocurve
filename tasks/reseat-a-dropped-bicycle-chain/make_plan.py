"""Robot-only chain placement and quarter-turn contact probe."""
from pathlib import Path
import json,numpy as np
from scipy.spatial.transform import Rotation as Rot
from common import down
from geometry import FRONT,POINTS,R
from planner import Plan
p=Plan();RL=down(180);RR=down()
i=int(np.argmin(POINTS[:,1]));pick=(POINTS[i]+POINTS[(i+1)%len(POINTS)])/2;pick[2]+=.010
L=FRONT+[0,.095,.027]
p.add(3,'approach the crank and dropped chain',{'left':(L+[0,0,.035],RL,.5),'right':(pick+[0,0,.040],RR,.35)},'joint')
p.add(2,'place fingers around crank and chain',{'left':(L,RL,.5),'right':(pick,RR,.25)})
p.add(2,'hold the crank and pinch the chain',{'left':(L,RL,0.),'right':(pick,RR,0.)})
lift=pick+[0,0,.040]
p.add(3,'lift the dropped chain clear of the plate',{'right':(lift,RR,0.)})
above=np.array([FRONT[0],FRONT[1]-R,FRONT[2]+.060])
p.add(3,'carry the chain above the front teeth',{'right':(above,RR,0.)})
seat=np.array([FRONT[0],FRONT[1]-R,FRONT[2]+.013])
p.add(3,'lay the rollers onto the front teeth',{'right':(seat,RR,0.)})
p.add(1,'release the seated chain',{'right':(seat,RR,.3)})
p.add(2,'clear the crank path',{'right':(seat+[0,-.08,.08],RR,.5)})
for deg in np.linspace(15,90,6):
 rot=Rot.from_euler('z',deg,degrees=True).as_matrix();p.add(.8,'backpedal to feed the chain onto the teeth',{'left':(FRONT+rot@(L-FRONT),rot@RL,0.)})
p.add(3,'inspect the engagement',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
