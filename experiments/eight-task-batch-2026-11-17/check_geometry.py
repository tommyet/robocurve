import importlib,sys,numpy as np
from pathlib import Path
root=Path(__file__).resolve().parents[2]
for slug in sys.argv[1:]:
 sys.path.insert(0,str(root/'tasks'/slug))
 for n in ['geometry','geometry_helpers']:sys.modules.pop(n,None)
 g=importlib.import_module('geometry');from scipy.spatial.transform import Rotation
 bodies={b['name']:b for b in g.BODIES};errors=[]
 for j in g.JOINTS:
  if not j.get('enabled',True):continue
  a,b=[bodies[j[k]] for k in ['a','b']]
  pa=np.array(a['pos'])+Rotation.from_quat(a['quat']).apply(j['p0']);pb=np.array(b['pos'])+Rotation.from_quat(b['quat']).apply(j['p1'])
  gap=np.linalg.norm(pb-pa)
  if gap>.0011:errors.append((j['name'],round(gap*1000,3)))
 print(slug,len(g.BODIES),'bodies',len(g.JOINTS),'joints','initial gaps >1.1mm:',errors[:12])
 assert not errors
 sys.path.pop(0)
