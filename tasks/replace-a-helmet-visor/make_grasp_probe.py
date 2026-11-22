"""Bounded contact diagnostic, not a full-score submission demonstration."""
from pathlib import Path
from geometry import *
from planner import Plan
from common import down
p=Plan()
from yam_arena import ik,station
readyP,readyR=ik.tcp_pose(p.a[7:13],station.BASES['right'])
p.add(3,'raise right',{'right':(readyP+[0,0,.13],readyR,.20)})
point=np.array([.157,0,.030]);R=OPEN@down(0);a=STARTS['old']+OPEN@point
p.add(3,'clear before old',{'right':(a-R[:,2]*.065,R,.20)})
p.add(3,'approach old',{'right':(a-R[:,2]*.025,R,.20)})
p.add(3,'align old',{'right':(a,R,.20)})
p.add(2,'grip old',{'right':(a,R,.01)})
p.add(2,'hold grasp',{})
print(p.save(Path(__file__).with_name('demo-plan.json')))
