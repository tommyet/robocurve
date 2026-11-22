from pathlib import Path
import numpy as np,json
from planner import Plan
from common import down
from geometry import *
p=Plan();L=down(0)@Rotation.from_euler("x",-25,degrees=True).as_matrix();R=down(-90)@Rotation.from_euler("x",25,degrees=True).as_matrix();OPEN=.38;CLOSE=.28
for j in range(3):
 i=j%2;long=ORIGINS[i]+[0,(N-1-(N-1)/2)*DX,0.];cross=ORIGINS[2+j]+ROTATIONS[2+j].apply([0,(N-1-(N-1)/2)*DX,0])+[0,0,0.]
 p.add(3,f'{j}:approach',{'left':(long+[0,0,.08],L,OPEN),'right':(cross+[0,0,.08],R,OPEN)},'joint')
 p.add(3,f'{j}:align',{'left':(long,L,OPEN),'right':(cross,R,OPEN)})
 p.add(3,f'{j}:pinch',{'left':(long,L,CLOSE),'right':(cross,R,CLOSE)})
 p.add(4,f'{j}:lift longitudinal',{'left':(long+[0,-.020,.040],L,CLOSE),'right':(cross+[0,0,.015],R,CLOSE)})
 entry=PIE+[-.070,CROSS_Y[j],.034]
 end=PIE+[.0875,CROSS_Y[j],.028]
 p.add(4,f'{j}:feed onto pie',{'right':(entry,R,CLOSE)})
 p.add(6,f'{j}:draw across',{'right':(end,R,CLOSE)})
 p.add(3,f'{j}:lower cross strip',{'right':(end+[0,0,-.006],R,CLOSE)})
 p.add(2,f'{j}:release cross strip',{'right':(end+[0,0,-.006],R,.45)})
 p.add(2,f'{j}:clear right hand',{'right':(end+[0,0,.07],R,.6)})
 p.add(4,f'{j}:replace longitudinal',{'left':(long,L,CLOSE)})
 p.add(2,f'{j}:release longitudinal',{'left':(long,L,.45)})
 p.add(2,f'{j}:clear left hand',{'left':(long+[0,0,.08],L,.6)})
from yam_arena import ik,station
from yam_arena.constants import READY
p.add(3,'hands clear',{s:(*ik.tcp_pose(np.asarray(READY),station.BASES[s]),.7) for s in ['left','right']},'joint')
p.add(4,'inspect',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
