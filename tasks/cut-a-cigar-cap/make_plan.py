"""Candidate ordinary-joint plan. Native success has not been demonstrated."""
from pathlib import Path
import numpy as np,json
from scipy.spatial.transform import Rotation
from planner import Plan
from common import down,TABLE
from geometry import CIGAR,CUTTER,CAP
p=Plan();RL=Rotation.from_euler('x',-45,degrees=True).as_matrix()@down(0);RR=Rotation.from_euler('x',45,degrees=True).as_matrix()@down(0)
# Pick up both separate objects. The right fingers act on the real sliding handles.
L=CIGAR+[0,.025,0]-.008*RL[:,2];R=CUTTER-.008*RR[:,2]
p.add(3,'approach cigar and cutter',{'left':(L+[0,0,.10],RL,.6),'right':(R+[0,0,.10],RR,1.)},'joint')
p.add(2,'enclose cigar and open handles',{'left':(L,RL,.6),'right':(R,RR,1.)})
p.add(1,'hold the cigar and lightly grip cutter',{'left':(L,RL,.185),'right':(R,RR,.85)})
p.add(3,'lift both objects',{'left':(L+[0,0,.16],RL,.185),'right':(R+[0,0,.16],RR,.85)})
# Rotate the aperture to the cigar axis, keeping it away from the head until aligned.
yaw=Rotation.from_euler('z',-20,degrees=True).as_matrix();turn=yaw@Rotation.from_euler('x',-45,degrees=True).as_matrix();RC=turn@RR
cigar_turn=yaw@Rotation.from_euler('x',45,degrees=True).as_matrix();LC=cigar_turn@RL
G=np.array([.30,.12,TABLE+.19]);head=G+cigar_turn@(CAP-(CIGAR+[0,.025,0]))
C0=head-turn[:,2]*.055;C1=head.copy()
p.add(4,'orient cigar and aperture',{'left':(G-.008*LC[:,2],LC,.185),'right':(C0-.008*RC[:,2],RC,.85)})
p.add(3,'position the cap through the aperture',{'right':(C1-.008*RC[:,2],RC,.85)})
p.add(3,'close both guillotine blades',{'right':(C1-.008*RC[:,2],RC,.40)})
p.add(1,'hold the completed cut',{})
p.add(2,'open cutter',{'right':(C1-.008*RC[:,2],RC,.85)})
p.add(3,'withdraw cutter from head',{'right':(C0-.008*RC[:,2],RC,.85)})
p.add(4,'return objects above board',{'left':(L+[0,0,.10],RL,.185),'right':(R+[0,0,.10],RR,.85)})
p.add(2,'lower both to board',{'left':(L,RL,.185),'right':(R,RR,.85)})
p.add(1,'release cigar and cutter',{'left':(L,RL,.8),'right':(R,RR,1.)})
p.add(3,'withdraw hands',{'left':(L+[0,0,.15],RL,.8),'right':(R+[0,0,.15],RR,1.)})
p.add(4,'released outcome',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
