"""Robot-only pickup, seating and backpedal probe on an upright bicycle."""
from pathlib import Path
import json,numpy as np
from scipy.spatial.transform import Rotation as Rot
from geometry import FRONT,POINTS,R
from planner import Plan
p=Plan();RL=np.array([[0,0,1],[0,1,0],[-1,0,0.]]);RR=RL.copy()
i=int(np.argmin(POINTS[:,2]));pick=(POINTS[i]+POINTS[(i+1)%len(POINTS)])/2;pick[0]-=.005
L=FRONT+[-.025,.125,0]
p.add(3,'approach the crank and loose chain',{'left':(pick+[-.05,0,0],RR,.35)},'joint')
p.add(2,'place the fingers around crank and chain',{'left':(pick,RR,.25)})
p.add(2,'hold the crank and pinch the chain',{'left':(pick,RR,0.)})
lift=pick+[-.04,0,.03]
p.add(3,'lift the dropped chain clear of the frame',{'left':(lift,RR,0.)})
turn=Rot.from_euler('x',-90,degrees=True).as_matrix();RR2=turn@RR
above=FRONT+[-.06,-R,0]
p.add(4,'align the rollers with the front teeth',{'left':(above,RR2,0.)})
seat=FRONT+[-.010,-R,0]
p.add(3,'place the chain onto the front teeth',{'left':(seat,RR2,0.)})
p.add(1,'release the chain',{'left':(seat,RR2,.3)})
p.add(2,'withdraw clear of the crank',{'left':(seat+[-.09,-.03,0],RR2,.5)})
p.add(3,'approach the crank after seating',{'right':(L+[-.06,0,0],RL,.5)},'joint')
p.add(2,'grasp the crank',{'right':(L,RL,.5)})
p.add(2,'close on the crank',{'right':(L,RL,0.)})
for deg in np.linspace(-15,-90,6):
 rot=Rot.from_euler('x',deg,degrees=True).as_matrix();p.add(.8,'backpedal to feed the rollers onto the teeth',{'right':(FRONT+rot@(L-FRONT),rot@RL,0.)})
p.add(3,'inspect engagement',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
