"""First native folding candidate; the retaining-loop action still needs validation."""
from pathlib import Path
import numpy as np,json
from scipy.spatial.transform import Rotation
from planner import Plan
from common import down,TABLE
p=Plan();RL=Rotation.from_euler('x',-45,degrees=True).as_matrix()@down(-90);RR=Rotation.from_euler('x',45,degrees=True).as_matrix()@down(-90)
L=np.array([.34,.258,TABLE+.026]);R=np.array([.34,-.258,TABLE+.026])
p.add(3,'approach opposite frame ends',{'left':(L+[0,0,.13],RL,.6),'right':(R+[0,0,.13],RR,.6)},'joint')
p.add(2,'enclose the four flattened frames',{'left':(L,RL,.6),'right':(R,RR,.6)})
p.add(1,'grip both ends',{'left':(L,RL,.10),'right':(R,RR,.10)})
p.add(3,'lift clear of the table',{'left':(L+[-.04,0,.12],RL,.10),'right':(R+[-.04,0,.12],RR,.10)})
for step in range(1,5):
 u=step/4;left=Rotation.from_euler('y',-15*u,degrees=True).as_matrix()@RL;right=Rotation.from_euler('y',15*u,degrees=True).as_matrix()@RR
 p.add(1.5,'twist the ends inward',{'left':(L+[-.04,-.12*u,.12],left,.10),'right':(R+[-.04,.12*u,.12],right,.10)})
p.add(3,'bring the crossing loops together',{'left':(L+[.005,-.19,.08],left,.10),'right':(R+[-.085,.19,.14],right,.10)})
p.add(3,'hold the nested frame for inspection',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
