from pathlib import Path
import json,numpy as np
from planner import Plan
from scipy.spatial.transform import Rotation as Rot
from geometry import HEAD,CAP
from scipy.optimize import least_squares
from geometry import POINTS,RIM,M
from pad_covers import configure_kinematics
configure_kinematics()
from yam_arena import ik,station
from yam_arena.constants import READY
RL=np.array([[0,0,1],[-1,0,0],[0,-1,0.]])
RR=RL.copy();a=np.r_[READY,.096,READY,.096]
for side,o,node in [('left',0,RIM[M//4]),('right',7,RIM[3*M//4])]:
 target=POINTS[node]-RL@np.array([0,0,-.012])
 def f(q):
  p,R=ik.tcp_pose(q,station.BASES[side]);return np.r_[p-target,.3*ik._rot_error(RL,R)]
 sols=[least_squares(f,q,bounds=(ik.LOWER,ik.UPPER),max_nfev=400) for q in [a[o:o+6],(ik.LOWER+ik.UPPER)/2]]
 sol=min(sols,key=lambda q:np.linalg.norm(q.fun));assert np.linalg.norm(sol.fun)<.0003,(side,sol.fun);a[o:o+6]=sol.x
Path(__file__).with_name('initial-action.json').write_text(json.dumps({'action14':a.tolist(),'description':'Both hands hold the separate cap rim at real opposed contacts before frame zero; material is not repositioned.'},indent=2)+'\n')
p=Plan(a)
p.add(2,'hold the separate cap by its rim',{'left':(ik.tcp_pose(a[:6],station.BASES['left'])[0],RL,.065),'right':(ik.tcp_pose(a[7:13],station.BASES['right'])[0],RR,.065)})
p.add(4,'lift and stretch the cap opening',{'left':(CAP+[.012,.084,.20],RL,.03),'right':(CAP+[.012,-.084,.20],RR,.03)})
p.add(4,'bring the stretched cap over the crown',{'left':(HEAD+[.012,.084,.215],RL,.03),'right':(HEAD+[.012,-.084,.215],RR,.03)})
p.add(7,'draw the opening evenly below the crown',{'left':(HEAD+[.012,.084,.038],RL,.03),'right':(HEAD+[.012,-.084,.038],RR,.03)})
p.add(2,'open both grips in place',{'left':(HEAD+[.012,.084,.038],RL,.18),'right':(HEAD+[.012,-.084,.038],RR,.18)})
p.add(3,'slide both hands laterally clear',{'left':(HEAD+[.012,.16,.070],RL,.18),'right':(HEAD+[.012,-.16,.070],RR,.18)})
p.add(2,'withdraw both open hands',{'left':(HEAD+[0,.20,.15],RL,.7),'right':(HEAD+[0,-.20,.15],RR,.7)})
p.add(4,'inspect after release',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
