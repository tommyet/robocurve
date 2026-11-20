from pathlib import Path
import numpy as np,json
from planner import Plan
from common import down
from geometry import *
GRIP_R=down(0)@Rotation.from_euler("x",50,degrees=True).as_matrix()
p=Plan();L=down(0);R=GRIP_R;tail=TAIL.copy();tool=TOOL.copy()
p.add(3,'approach tail and scaler',{'left':(tail+[0,0,.08],L,.35),'right':(tool+[0,0,.08],R,.30)},'joint')
p.add(3,'place fingers around tail and handle',{'left':(tail,L,.25),'right':(tool,R,.20)})
p.add(2,'grip tail and scaler handle',{'left':(tail,L,.18),'right':(tool,R,.09)})
p.add(2,'lift the scaler',{'right':(tool+[0,0,.10],R,.09)})
for lane,x in enumerate([-.022,-.011,0.,.011,.022]):
 extent=.049 if abs(x)>.02 else .073
 q,Q=surface(x,extent);target=C+q+Q[:,2]*.0040-Q@HEAD_OFFSET
 p.add(3,'approach scraping lane '+str(lane),{'right':(target+[0,0,.045],Q@GRIP_R,.09)},'joint')
 p.add(2,'load scraping lane '+str(lane),{'right':(target,Q@GRIP_R,.09)})
 for j,y in enumerate(np.linspace(extent,-extent,13)[1:]):
  q,Q=surface(x,float(y));target=C+q+Q[:,2]*.0040-Q@HEAD_OFFSET
  p.add(.5,'scrape lane '+str(lane)+' point '+str(j),{'right':(target,Q@GRIP_R,.09)})
 p.add(2,'lift from scraping lane '+str(lane),{'right':(target+[0,0,.050],Q@GRIP_R,.09)})
p.add(3,'return scaler above its starting place',{'right':(tool+[0,0,.065],R,.09)})
p.add(2,'put scaler on the table',{'right':(tool+[0,0,.003],R,.09)})
p.add(2,'release scaler and fish',{'left':(tail,L,.45),'right':(tool+[0,0,.003],R,.45)})
from yam_arena import ik,station
from yam_arena.constants import READY
clear={side:(*ik.tcp_pose(np.asarray(READY),station.BASES[side]),.6) for side in ['left','right']}
p.add(3,'leave hands clear',clear,'joint')
p.add(4,'inspect remaining scales and intact skin',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
