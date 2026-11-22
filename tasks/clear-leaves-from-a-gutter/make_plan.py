"""Ordinary scoop pickup, confined sweep and tipping into the bucket."""
from pathlib import Path
from planner import Plan
from geometry import *
from common import down
p=Plan()
def target(origin,Q=None,g=.14):
 Q=np.eye(3) if Q is None else Q
 return {'right':(np.asarray(origin)+Q@HANDLE,Q@down(0),g)}
p.add(3,'approach',target(SCOOP+[0,0,.10],g=.7),mode='joint')
p.add(2,'align',target(SCOOP,g=.7))
p.add(2,'grip',target(SCOOP))
p.add(2,'lift',target(SCOOP+[0,0,.12]))
entry=GUTTER+[0,-.23,-RADIUS+.003]
Q=Rotation.from_euler('x',-3,degrees=True).as_matrix()
p.add(4,'position',target(entry+[0,0,.12],Q))
p.add(3,'enter',target(entry,Q))
p.add(6,'scoop',target(entry+[0,.29,0],Q))
p.add(3,'lift leaves',target(entry+[0,.29,.15],Rotation.from_euler('x',15,degrees=True).as_matrix()))
over=BUCKET+[0,0,.175]
p.add(5,'carry',target(over))
p.add(4,'empty',target(over,Rotation.from_euler('y',-65,degrees=True).as_matrix()))
p.add(2,'drain',target(over,Rotation.from_euler('y',-65,degrees=True).as_matrix()))
p.add(3,'return',target(SCOOP+[0,0,.14]))
p.add(3,'set down',target(SCOOP))
p.add(1,'release',target(SCOOP,g=.8))
p.add(2,'clear',target(SCOOP+[0,0,.12],g=.8))
print(p.save(Path(__file__).with_name('demo-plan.json')))
