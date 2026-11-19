"""Robot-only pickup, seating and backpedal probe on an upright bicycle."""
from pathlib import Path
import json,numpy as np
from scipy.spatial.transform import Rotation as Rot
from geometry import FRONT,POINTS,R,pickup_index,PEDAL
from pad_covers import configure_kinematics
configure_kinematics()
from planner import Plan
p=Plan();RL=np.array([[0,0,1],[0,1,0],[-1,0,0.]]);RR=np.array([[0,0,1],[-1,0,0],[0,-1,0.]])
from demo_targets import PICK,ROTATION
pick=PICK.copy();RR=ROTATION.copy()
L=PEDAL.copy()
p.add(3,'approach the crank and loose chain',{'right':(pick+[-.05,0,0],RR,.35)},'joint')
p.add(2,'place the fingers around crank and chain',{'right':(pick,RR,.25)})
p.add(2,'hold the crank and pinch the chain',{'right':(pick,RR,0.)})
lift=pick+[-.04,0,.01]
p.add(3,'lift the dropped chain clear of the frame',{'right':(lift,RR,0.)})
RR2=RR.copy()
above=FRONT+[-.04,-R,0]
p.add(4,'align the rollers with the front teeth',{'right':(above,RR2,0.)})
seat=FRONT+[-.005,-R,0]
p.add(3,'place the chain onto the front teeth',{'right':(seat,RR2,0.)})
p.add(3,'approach the crank while holding the chain in place',{'left':(L+[-.06,0,0],RL,.5)},'joint')
p.add(2,'grasp the crank',{'left':(L,RL,.5)})
p.add(2,'close on the crank',{'left':(L,RL,0.)})
for deg in np.linspace(-15,-90,6):
 rot=Rot.from_euler('x',deg,degrees=True).as_matrix()
 p.add(.8,'guide the chain while starting the crank',{'left':(FRONT+rot@(L-FRONT),RL,0.),'right':(FRONT+rot@(seat-FRONT),rot@RR2,0.)})
guide=FRONT+rot@(seat-FRONT);guideR=rot@RR2
p.add(1,'release the engaged chain',{'right':(guide,guideR,.5)})
p.add(2,'withdraw clear of the chain',{'right':(guide+[-.09,0,0],guideR,.5)})
for deg in np.linspace(-105,-480,26):
 rot=Rot.from_euler('x',deg,degrees=True).as_matrix();p.add(.8,'backpedal to feed the rollers onto the teeth',{'left':(FRONT+rot@(L-FRONT),RL,0.)})
p.add(1,'release the pedal',{'left':(FRONT+rot@(L-FRONT),RL,.55)})
p.add(3,'withdraw from the drivetrain',{'left':(FRONT+rot@(L-FRONT)+[-.10,0,0],RL,.55)})
p.add(4,'inspect engagement after release',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
