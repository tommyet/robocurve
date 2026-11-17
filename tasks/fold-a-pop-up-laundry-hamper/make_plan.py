"""First native folding candidate; the retaining-loop action still needs validation."""
from pathlib import Path
import numpy as np,json
from scipy.spatial.transform import Rotation
from planner import Plan
from common import down,TABLE
p=Plan();base=np.array([[0,-1,0],[0,0,-1],[1,0,0.]])
RL=Rotation.from_euler('x',35,degrees=True).as_matrix()@base;RLP=Rotation.from_euler('x',35,degrees=True).as_matrix()@base;RR=Rotation.from_euler('x',145,degrees=True).as_matrix()@base
L=np.array([.324,.264,TABLE+.023])-.008*RL[:,2];R=np.array([.320,-.264,TABLE+.023])-.008*RR[:,2]
p.add(3,'approach opposite frame ends',{'left':(L+[0,0,.05],RL,.3),'right':(R+[0,0,.05],RR,.3)},'joint')
p.add(2,'enclose the four flattened frames',{'left':(L,RLP,.3),'right':(R,RR,.3)})
p.add(2,'grip both ends',{'left':(L,RLP,0.),'right':(R,RR,0.)})
p.add(3,'lift clear of the table',{'left':(L+[-.04,0,.12],RL,0.),'right':(R+[-.04,0,.12],RR,0.)})
for step in range(1,5):
 u=step/4;yaw=Rotation.from_euler('z',-30*u,degrees=True).as_matrix();left=yaw@Rotation.from_euler('y',-65*u,degrees=True).as_matrix()@RL;right=yaw@Rotation.from_euler('y',65*u,degrees=True).as_matrix()@RR
 p.add(1.5,'twist the ends inward',{'left':(L+[-.04,-.12*u,.12+.07*u],left,0.),'right':(R+[-.04,.12*u,.12+.07*u],right,0.)})
p.add(3,'bring the crossing loops together',{'left':(L+[.005,-.19,.18],left,0.),'right':(R+[-.085,.19,.22],right,0.)})
p.add(3,'hold the nested frame for inspection',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
