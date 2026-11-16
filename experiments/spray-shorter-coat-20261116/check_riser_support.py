"""Finite-riser SAT comparison using conservative circumscribed128-sided body cylinder."""
import json,numpy as np
from pathlib import Path
from check_aimed_geometry import gap,ik
rows=[json.loads(x)for x in Path('/private/tmp/spray-recorded-030/trajectory.jsonl').read_text().splitlines()];N=128;ang=np.arange(N)*2*np.pi/N;rad=.026/np.cos(np.pi/N);verts=np.array([[rad*np.cos(t),rad*np.sin(t),z]for z in(-.065,.065)for t in ang]);faces=[]
for i in range(N):
 j=(i+1)%N;faces.extend([[i,j,j+N],[i,j+N,i+N]])
for i in range(1,N-1):faces.extend([[0,i+1,i],[N,N+i,N+i+1]])
faces=np.array(faces);report=[]
for i in range(530,779):
 r=rows[i+1];R=np.asarray(r['can_rotation']);p=np.asarray(r['can'])+R@np.array([0,0,-.005]);tri=(verts@R.T+p)[faces];shift=np.array([.022,-.002,0])*ik.smoothstep((i-530)/80);source=gap(tri,np.array([.26,0,.7725]),np.eye(3),np.array([.08,.08,.05]));moved=gap(tri+shift,np.array([.26,0,.7725]),np.eye(3),np.array([.08,.08,.05]));report.append(dict(action=i,source_gap_m=source,moved_gap_m=moved,delta_gap_m=moved-source,source_body_com_xy=p[:2].tolist(),predicted_body_com_xy=(p+shift)[:2].tolist()))
result=dict(scope='Conservative circumscribed128-sided body cylinder SAT versus finite80mm square50mm riser. Actual source poses vs source+commandedoffset proxy. Negative gap represents existing support overlap, not verified new native contact. Robot holds can; COM projection alone is not unsupported stability proof.',minimum_source_gap_m=min(x['source_gap_m']for x in report),minimum_moved_gap_m=min(x['moved_gap_m']for x in report),maximum_additional_overlap_m=max(0,max(x['source_gap_m']-x['moved_gap_m']for x in report)),minimum_ramp_moved_gap_m=min(x['moved_gap_m']for x in report if x['action']<=609),projected_com_x_range_m=[min(x['predicted_body_com_xy'][0]for x in report),max(x['predicted_body_com_xy'][0]for x in report)],projected_com_y_range_m=[min(x['predicted_body_com_xy'][1]for x in report),max(x['predicted_body_com_xy'][1]for x in report)],rows=report)
Path(__file__).with_name('aimed-riser-support-report.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items()if k!='rows'})
