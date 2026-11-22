"""Two-handed catch release, visor replacement and hinge check."""
from pathlib import Path
from geometry import *
from planner import Plan
from common import down
p=Plan();middle=np.array([.157,0,-.005]);wing=np.array([.05,.13,-.005])
def shield(origin,Q,g=.01,point=middle):
 R=down(0)@Rotation.from_euler('x',-40 if np.array_equal(point,wing) else 40,degrees=True).as_matrix()
 return (np.asarray(origin)+Q@point,Q@R,g)
def move(t,stage,side,pose,mode='cartesian'):p.add(t,stage,{side:pose},mode=mode)
move(3,'approach old','right',shield(STARTS['old']+[0,0,.03],OPEN,g=.8),'joint')
move(2,'align old','right',shield(STARTS['old'],OPEN,g=.8))
move(2,'grip old','right',shield(STARTS['old'],OPEN))
def trigger(side):
 pressR=Rotation.from_euler('x',-30 if side=='left' else 30,degrees=True).as_matrix()@down(0)
 point=HELMET+PINS[side]+np.array([.024,(1 if side=='left' else -1)*.010,.045])
 move(3,'approach trigger '+side,side,(point+[0,0,.035],pressR,.01),'joint')
 move(2,'press trigger '+side,side,(point+[0,0,.002],pressR,.01))
 move(2,'clear trigger '+side,side,(point+[0,0,.05],pressR,.01))
trigger('left')
move(3,'approach wing','left',shield(STARTS['old']+[0,0,.04],OPEN,g=.8,point=wing),'joint')
move(2,'align wing','left',shield(STARTS['old'],OPEN,g=.8,point=wing))
move(2,'grip wing','left',shield(STARTS['old'],OPEN,point=wing))
move(1,'release middle','right',shield(STARTS['old'],OPEN,g=.8))
move(2,'clear middle','right',shield(STARTS['old']+[0,-.08,.06],OPEN,g=.8))
trigger('right')
move(3,'remove old','left',shield(STARTS['old']+[.02,0,.025],OPEN,point=wing))
move(4,'carry old','left',shield(TRAY+[0,0,.10],np.eye(3),point=wing),'joint')
move(3,'place old','left',shield(TRAY+[0,0,.055],np.eye(3),point=wing))
move(1,'release old','left',shield(TRAY+[0,0,.055],np.eye(3),g=.8,point=wing))
move(2,'clear left','left',shield(TRAY+[0,0,.10],np.eye(3),g=.8,point=wing))
move(3,'approach spare','right',shield(NEW+[0,0,.08],np.eye(3),g=.8),'joint')
move(2,'align spare','right',shield(NEW,np.eye(3),g=.8))
move(2,'grip spare','right',shield(NEW,np.eye(3)))
move(4,'lift spare','right',shield(NEW+[0,0,.12],OPEN))
move(4,'align hooks','right',shield(STARTS['old']+[.015,0,.025],OPEN))
move(3,'seat hooks','right',shield(STARTS['old'],OPEN))
for label,angles in [('close check',np.linspace(-70,0,36)[1:]),('open check',np.linspace(0,-70,36)[1:])]:
 for angle in angles:
  Q=Rotation.from_euler('y',angle,degrees=True).as_matrix();origin=HELMET+PIVOT-Q@PIVOT
  move(.20,label,'right',shield(origin,Q))
move(1,'release spare','right',shield(STARTS['old'],OPEN,g=.8))
move(3,'clear','right',shield(STARTS['old']+[0,0,.03],OPEN,g=.8))
p.add(2,'settle',{})
print(p.save(Path(__file__).with_name('demo-plan.json')))
