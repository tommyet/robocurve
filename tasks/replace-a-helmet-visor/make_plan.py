"""Two-handed catch release, visor replacement and hinge check."""
from pathlib import Path
from geometry import *
from planner import Plan
from common import down
p=Plan()
def shield(origin,Q,g=.01):
 R=down(0)@Rotation.from_euler('x',20,degrees=True).as_matrix()
 return (np.asarray(origin)+Q@np.array([.157,0,.030]),Q@R,g)
def move(t,stage,side,pose,mode='cartesian'):p.add(t,stage,{side:pose},mode=mode)
def newshield(origin,Q,g=.01):return shield(origin,Q,g)
move(3,'approach spare','right',newshield(NEW+[0,0,.08],np.eye(3),g=.12),'joint')
move(2,'align spare','right',newshield(NEW,np.eye(3),g=.12))
move(2,'grip spare','right',newshield(NEW,np.eye(3)))
move(3,'lift clear','right',newshield(NEW+[0,0,.06],np.eye(3)))
move(4,'lift spare','right',newshield(NEW+[.14,0,.08],OPEN))
move(3,'clear shell front','right',newshield([.43,NEW[1],STARTS['old'][2]+.015],OPEN))
move(4,'centre in front','right',newshield([.43,0,STARTS['old'][2]+.015],OPEN))
move(4,'align hooks','right',newshield(STARTS['old']+[.015,0,.015],OPEN))
move(3,'seat hooks','right',newshield(STARTS['old'],OPEN))
move(2,'hold seated','right',newshield(STARTS['old'],OPEN))
for label,angles in [('close check',np.linspace(-70,0,36)[1:]),('open check',np.linspace(0,-70,36)[1:])]:
 for angle in angles:
  Q=Rotation.from_euler('y',angle,degrees=True).as_matrix();origin=HELMET+PIVOT-Q@PIVOT
  move(.20,label,'right',newshield(origin,Q))
move(1,'release spare','right',newshield(STARTS['old'],OPEN,g=.12))
move(3,'clear','right',newshield(STARTS['old']+[.04,-.04,.08],OPEN,g=.12))
move(1,'open hands','right',newshield(STARTS['old']+[.04,-.04,.08],OPEN,g=.8))
p.add(2,'settle',{})
print(p.save(Path(__file__).with_name('demo-plan.json')))
