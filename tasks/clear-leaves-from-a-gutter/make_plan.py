"""Ordinary scoop pickup, confined sweep and tipping into the bucket."""
from pathlib import Path
from planner import Plan
from geometry import *
from common import down
p=Plan();GRIP_R=Rotation.from_euler("x",30,degrees=True).as_matrix()@down(0)
def target(origin,Q=None,g=.14):
 Q=np.eye(3) if Q is None else Q
 return {'right':(np.asarray(origin)+Q@HANDLE,Q@GRIP_R,g)}
p.add(3,'approach',target(SCOOP+[0,0,.10],g=.7),mode='joint')
p.add(2,'align',target(SCOOP,g=.7))
p.add(2,'grip',target(SCOOP))
p.add(2,'lift',target(SCOOP+[0,0,.12]))
entry=GUTTER+[0,-.065,-RADIUS+.0005]
Q=Rotation.from_euler('x',-5,degrees=True).as_matrix()
p.add(4,'position',target(entry+[0,0,.065],Q))
p.add(3,'enter',target(entry,Q))
stopR=Rotation.from_euler('y',-40,degrees=True).as_matrix()@down(0)
stopP=GUTTER+np.array([0,.16,-RADIUS+.032])
p.add(3,'approach leaf backstop',{'left':(stopP+[0,0,.08],stopR,.01)},mode='joint')
p.add(2,'hold leaves',{'left':(stopP,stopR,.01)})
p.add(6,'scoop',target(entry+[0,.19,0],Q))
p.add(3,'lift leaves',{**target(entry+[0,.19,.08],Rotation.from_euler('x',15,degrees=True).as_matrix()),'left':(stopP+[0,0,.10],stopR,.8)})
p.add(3,'withdraw from roof',target(entry+[-.15,.19,.08],Rotation.from_euler('x',15,degrees=True).as_matrix()))
over=BUCKET+[0,0,.085]
carryQ=Rotation.from_euler('z',270,degrees=True).as_matrix()
p.add(5,'carry',target(over,carryQ),mode='joint')
p.add(4,'empty',target(over,carryQ@Rotation.from_euler('y',-70,degrees=True).as_matrix()))
p.add(2,'drain',target(over,carryQ@Rotation.from_euler('y',-70,degrees=True).as_matrix()))
p.add(3,'return',target(SCOOP+[0,0,.10]),mode='joint')
p.add(3,'set down',target(SCOOP))
p.add(1,'release',target(SCOOP,g=.8))
p.add(2,'clear',target(SCOOP+[0,0,.12],g=.8))
print(p.save(Path(__file__).with_name('demo-plan.json')))
