"""Pinch opposite bound ends from outside, then counter-twist and nest."""
from pathlib import Path
import numpy as np,json
from scipy.spatial.transform import Rotation as Rot
from planner import Plan
from geometry import BODIES,GRIP_ENDS,FRAME_LAYERS,CENTER
p=Plan();base=np.array([[0,-1,0],[0,0,-1],[1,0,0.]])
flip=np.eye(3)
points=[np.mean([b['pos'] for b in BODIES if b['name'] in [f'wire_{f}_{i:02d}' for f in FRAME_LAYERS]],axis=0) for i in GRIP_ENDS]
def stack_grip(angle, polarity=1.):
 a=np.radians(angle);z=np.array([np.cos(a),np.sin(a),0.]);x=np.array([0.,0.,polarity]);return np.column_stack([x,np.cross(z,x),z])
RL=stack_grip(-50)
RR=stack_grip(50,-1)
L=points[0]-.001*RL[:,2];R=points[1]-.001*RR[:,2]
p.add(3,'approach opposite frame ends from outside',{'left':(L-.035*RL[:,2],RL,.3),'right':(R-.035*RR[:,2],RR,.3)},'joint')
p.add(2,'enclose the four stacked frame edges',{'left':(L,RL,.3),'right':(R,RR,.3)})
p.add(2,'grip both seams',{'left':(L,RL,0.),'right':(R,RR,0.)})
p.add(6,'lift the bound ends before turning the wrists',{'left':(points[0]+[0,-.025,.14]-.001*RL[:,2],RL,0.),'right':(points[1]+[0,.025,.14]-.001*RR[:,2],RR,0.)})
for step in range(1,7):
 u=step/6
 twist=min(1.,2*u)
 left=Rot.from_euler('x',90*twist,degrees=True).as_matrix()@RL
 right=Rot.from_euler('x',-90*twist,degrees=True).as_matrix()@RR
 lp=points[0]+[0,-.025-.215*u*u,.14+.06*u]-.001*left[:,2]
 rp=points[1]+[0,.025+.215*u*u,.14+.06*u]-.001*right[:,2]
 p.add(1.5,'turn the ends before bringing the loops together',{'left':(lp,left,0.),'right':(rp,right,0.)})
p.add(3,'hold the twisted frame for inspection',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
