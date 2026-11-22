"""Plan only ordinary arm poses; the native solver moves the paper."""
from pathlib import Path
from planner import Plan
from geometry import *
from common import rotation
GRIPS={'left':0,'right':63}
def orient(normal,approach=None):
 x=np.asarray(normal);x=x/np.linalg.norm(x)
 z=np.array([0.,0.,-1.]) if approach is None else np.array(approach,dtype=float)
 z=z-x*np.dot(z,x);z/=np.linalg.norm(z);y=np.cross(z,x);return np.column_stack([x,y,z])
p=Plan();rest={s:np.array(BODIES[2+i]['pos']) for s,i in GRIPS.items()}
Rs={s:orient((1 if s=='left' else -1)*Rotation.from_quat(BODIES[2+i]['quat']).as_matrix()[:,2]) for s,i in GRIPS.items()}
relative={s:Rotation.from_quat(BODIES[2+GRIPS[s]]['quat']).as_matrix().T@Rs[s] for s in GRIPS}
def flat_grip(side,normal):
 normal=np.array(normal,dtype=float);normal/=np.linalg.norm(normal)
 width=np.array([0.,0.,1.]);length=np.cross([0.,0.,1.],normal);paper=np.column_stack([width,length,np.cross(width,length)])
 return paper@relative[side]
p.add(3,'approach',{s:(pos-.025*Rs[s][:,2],Rs[s],.8) for s,pos in rest.items()},mode='joint')
p.add(2,'align',{s:(pos,Rs[s],.7) for s,pos in rest.items()})
p.add(2,'pinch',{s:(pos,Rs[s],.0215) for s,pos in rest.items()})
# Keep the held length taut on a route tangent to the torso. This plans hand
# poses only; paper shape and contact are still determined by native physics.
from scipy.optimize import brentq
from scipy.integrate import quad
length=(GRIPS['right']-GRIPS['left'])*DX
arc=lambda t:quad(lambda u:np.hypot(RX*np.sin(u),RY*np.cos(u)),0,t)[0]
perimeter=4*arc(np.pi/2)
def route(y):
 def shape(x):
  a=(x-CENTER[0])/RX;b=y/RY;r=np.hypot(a,b)
  theta=np.arctan2(b,a)+np.arccos(1/r)
  T=np.array([CENTER[0]+RX*np.cos(theta),RY*np.sin(theta),CHEST])
  P=np.array([x,y,CHEST]);L=perimeter-2*arc(theta)+2*np.linalg.norm(P-T)
  return L,T,P
 lower=CENTER[0]+(RX+.000001 if abs(y)<RY else .001-RX)
 x=brentq(lambda x:shape(x)[0]-length,lower,CENTER[0]+.5)
 return shape(x)[1:]
def targets(y,height=0.):
 T,P=route(y);out={}
 for side,sign in [('left',1),('right',-1)]:
  target=P*np.array([1,sign,1]);target[2]+=height;tangent=(T-P)*np.array([1,sign,1])*(1 if side=='left' else -1);tangent/=np.linalg.norm(tangent)
  width=np.array([0.,0.,1.]);paper=np.column_stack([width,tangent,np.cross(width,tangent)])
  out[side]=(target,paper@relative[side],.0215)
 return out
p.add(4,'lift',targets(.47,.04))
p.add(1,'settle',targets(.47,.04))
# Interpolate the physical route continuously rather than cutting across it.
from yam_arena import ik,station
errors=[0.,0.];seconds=21
for k in range(1,round(seconds*20)+1):
 u=ik.smoothstep(k/(seconds*20));y=.47+u*(-.03-.47)
 h=float(np.interp(y,[-.03,.025,.075,.15,.25,.34,.47],[0.,.002,.005,.010,.020,.030,.040]))
 for side,(pos,R,g) in targets(y,h).items():
  o=0 if side=='left' else 7
  q,pe,re=ik.solve(pos,ik.matrix_to_quat_xyzw(R),p.a[o:o+6],base_pos=station.BASES[side],iters=100,rot_weight=.02)
  p.a[o:o+6]=q;p.a[o+6]=g;errors=[max(errors[0],float(pe)),max(errors[1],float(re))]
 p.frames.append(dict(action14=p.a.tolist(),stage='wrap'))
p.audit.append(dict(stage='wrap',position_error_m=errors[0],rotation_error_rad=errors[1]));print('wrap',errors,flush=True)
p.add(4,'read',targets(-.03))
print(p.save(Path(__file__).with_name('demo-plan.json')))
