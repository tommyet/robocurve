"""Two-handed catch release, visor replacement and hinge check."""
from pathlib import Path
from geometry import *
from planner import Plan
from common import down
p=Plan()
from yam_arena import ik,station
from yam_arena.constants import READY
readyP,readyR=ik.tcp_pose(p.a[7:13],station.BASES['right'])
p.add(3,'raise right',{'right':(readyP+[0,0,.13],readyR,.20)})
middle=np.array([.157,0,.030]);wing=np.array([.1073134409,.10,.030])
def shield(origin,Q,g=.01,point=middle,tilt=None):
 tilt=0 if tilt is None else tilt
 az=0 if point[1]<.02 else np.degrees(np.arctan2(point[1]/.137**2,point[0]/.157**2))+180
 R=Rotation.from_euler('z',az,degrees=True).as_matrix()@down(0)@Rotation.from_euler('x',tilt,degrees=True).as_matrix()
 return (np.asarray(origin)+Q@point,Q@R,g)
def move(t,stage,side,pose,mode='cartesian'):p.add(t,stage,{side:pose},mode=mode)
a,R,g=shield(STARTS['old'],OPEN,g=.20,point=middle)
move(3,'clear before old','right',(a-R[:,2]*.065,R,g))
move(3,'approach old','right',(a-R[:,2]*.025,R,g))
move(3,'align old','right',shield(STARTS['old'],OPEN,g=.20))
move(2,'grip old','right',shield(STARTS['old'],OPEN))
def trigger(side):
 pressR=Rotation.from_euler('x',-30 if side=='left' else 30,degrees=True).as_matrix()@down(0)
 point=HELMET+PINS[side]+np.array([.024,(1 if side=='left' else -1)*.010,.045])
 move(3,'approach trigger '+side,side,(point+[.04,0,.025],pressR,.01),'joint')
 move(2,'press trigger '+side,side,(point+[-.006,0,-.008],pressR,.01))
 move(2,'hold trigger '+side,side,(point+[-.006,0,-.008],pressR,.01))
 move(2,'clear trigger '+side,side,(point+[.025,0,.020],pressR,.01))
 readySideP,readySideR=ik.tcp_pose(READY,station.BASES[side])
 move(3,'raise after trigger '+side,side,(readySideP+[0,0,.13],readySideR,.01),'joint')
trigger('left')
p.add(2,'settle',{})
print(p.save(Path(__file__).with_name('demo-plan.json')))
