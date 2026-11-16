import json,sys,numpy as np
sys.path.insert(0,'/private/tmp/robocurve-carton-revisions/tasks/break-down-taped-carton')
from scene import layout
from turnover import rx,advance_support,solve_target
from turnover_targets import wall_target,tip_vertices
from turnover_safety import Geometry,BASES
from check_turnover import parked_cutter
from config import TOP
from model import HEIGHT,WIDTH
from yam_arena.urdf import quat_xyzw_to_matrix
G=Geometry();V=tip_vertices(G);rows=json.load(open('/private/tmp/turnover-astra-dense.json'));parts=layout()[0];corners=np.array([[x,y,z]for x in[-1,1]for y in[-1,1]for z in[-1,1]]);raw={p['name']:(np.array(p['pos']),quat_xyzw_to_matrix([*p['quat'][1:],p['quat'][0]]),p['size'])for p in parts};out=[]
for row in rows:
 a=row['angle']
 if a not in(0,10,20,30,40,50,60):continue
 R=rx(-np.radians(a));vv=np.concatenate([p+corners*np.array(sz)/2@Q.T for p,Q,sz in raw.values()]);yr=-.10+.093-np.cos(np.radians(a))*.093+np.sin(np.radians(a))*(-.0015);o=np.array([.25,yr,TOP+.0002-(vv@R.T)[:,2].min()]);obs={n:(o+R@p,R@Q,sz)for n,(p,Q,sz)in raw.items()};obs.update(parked_cutter());vertices=np.concatenate([p+corners*np.array(sz)/2@Q.T for p,Q,sz in list(obs.values())[:12]])
 for lead in(1.2,.3):
  no,nR=advance_support(o,R,vertices,lead);p,Q=wall_target(no,nR,'right',HEIGHT,WIDTH,V,.0002);q,pe,re=solve_target(p,Q,row['solutions'][1]['q'],BASES['right'],starts=4);other=G.parts('left',row['solutions'][0]['q'],[-.012]*2);g=G.guard('right',q,[-.012]*2,obs,other,intended=True,intended_targets=('south','south_top'));out.append(dict(angle=a,lead=lead,pe=pe,re=re,guard=g))
print(json.dumps(out,indent=2));json.dump(out,open('/private/tmp/turnover-command-lead.json','w'),indent=2)
