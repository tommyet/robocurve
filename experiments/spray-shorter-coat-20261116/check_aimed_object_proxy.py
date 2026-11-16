"""Conservative moved-body static clearance; observed body poses plus commanded offset only."""
import json,sys
from pathlib import Path
import numpy as np
from check_aimed_geometry import obstacles,gap,ik
SOURCE=Path('/private/tmp/spray-recorded-030');rows=[json.loads(x)for x in(SOURCE/'trajectory.jsonl').read_text().splitlines()];static=obstacles(SOURCE)
vertices=np.array([[x,y,z]for x in(-1,1)for y in(-1,1)for z in(-1,1)])
faces=np.array([[0,1,3],[0,3,2],[4,6,7],[4,7,5],[0,4,5],[0,5,1],[2,3,7],[2,7,6],[0,2,6],[0,6,4],[1,5,7],[1,7,3]])
best=[10];negative=[]
for i in range(531,779):
 r=rows[i+1];shift=np.array([.022,-.002,0])*ik.smoothstep((i-530)/80);R=np.asarray(r['can_rotation']);p=np.asarray(r['can'])+shift
 for name,z,size in [('body',-.005,np.array([.052,.052,.13])),('shoulder',.065,np.array([.046,.046,.01]))]:
  tri=((vertices*size/2)@R.T+p+R@np.array([0,0,z]))[faces]
  for label,op,oR,osize in static+[('parked_cap_outer',np.asarray(r['cap']),np.asarray(r['cap_rotation']),np.array([.062,.062,.036]))]:
   g=gap(tri,op,oR,osize)
   if g<best[0]:best=[g,i,name,label]
   if g<0:negative.append([g,i,name,label])
result=dict(scope='Predicted held source-can pose+common translation only; conservative body/shoulder OBBs against riser, backing, full stand and parked-cap box at all248 waypoints; does not prove native held-can response.',minimum_gap_m=best,negative_gaps=negative)
Path(__file__).with_name('aimed-object-proxy-report.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
