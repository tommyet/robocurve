"""Two-handed catch release, visor replacement and hinge check."""
from pathlib import Path
from geometry import *
from planner import Plan
from common import down
p=Plan()
from yam_arena import ik,station
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
 move(2,'press trigger '+side,side,(point+[0,0,.0075],pressR,.01))
 move(2,'clear trigger '+side,side,(point+[.025,0,.020],pressR,.01))
trigger('left')
a,R,g=shield(STARTS['old'],OPEN,g=.20,point=wing)
move(3,'approach wing','left',(a-R[:,2]*.025,R,g),'joint')
move(3,'align wing','left',shield(STARTS['old'],OPEN,g=.20,point=wing))
move(2,'grip wing','left',shield(STARTS['old'],OPEN,point=wing))
move(1,'release middle','right',shield(STARTS['old'],OPEN,g=.12))
move(2,'clear middle','right',shield(STARTS['old']+[0,-.08,.06],OPEN,g=.12))
trigger('right')
move(3,'remove old','left',shield(STARTS['old']+[.075,0,.025],OPEN,point=wing))
move(3,'clear old sideways','left',shield(STARTS['old']+[.075,.08,.025],OPEN,point=wing))
parkQ=np.eye(3)
move(4,'carry old','left',shield(TRAY+[0,0,.12],parkQ,point=wing),'joint')
move(3,'place old','left',shield(TRAY+[0,0,.054],parkQ,point=wing))
move(1,'release old','left',shield(TRAY+[0,0,.054],parkQ,g=.8,point=wing))
move(2,'clear left','left',shield(TRAY+[0,0,.12],parkQ,g=.8,point=wing))
def newshield(origin,Q,g=.01):return shield(origin,Q,g,tilt=20)
move(3,'approach spare','right',newshield(NEW+[0,0,.08],np.eye(3),g=.12),'joint')
move(2,'align spare','right',newshield(NEW,np.eye(3),g=.12))
move(2,'grip spare','right',newshield(NEW,np.eye(3)))
move(4,'lift spare','right',newshield(NEW+[.04,0,.08],OPEN))
move(4,'align hooks','right',newshield(STARTS['old']+[.015,0,.025],OPEN))
move(3,'seat hooks','right',newshield(STARTS['old'],OPEN))
for label,angles in [('close check',np.linspace(-70,0,36)[1:]),('open check',np.linspace(0,-70,36)[1:])]:
 for angle in angles:
  Q=Rotation.from_euler('y',angle,degrees=True).as_matrix();origin=HELMET+PIVOT-Q@PIVOT
  move(.20,label,'right',newshield(origin,Q))
move(1,'release spare','right',newshield(STARTS['old'],OPEN,g=.12))
move(3,'clear','right',newshield(STARTS['old']+[.04,-.04,.08],OPEN,g=.12))
move(1,'open hands','right',newshield(STARTS['old']+[.04,-.04,.08],OPEN,g=.8))
p.add(2,'settle',{})
print(p.save(Path(__file__).with_name('demo-plan.json')))
