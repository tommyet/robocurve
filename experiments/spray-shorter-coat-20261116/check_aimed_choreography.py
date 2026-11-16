"""Observed source ramp clearance and predicted relative command preservation."""
import sys,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tasks/uncap-spray-panel'))
from yam_arena import ik
import aimed_demo,recorded_demo
rows=[json.loads(x)for x in Path('/private/tmp/spray-recorded-030/trajectory.jsonl').read_text().splitlines()];new,_=aimed_demo.load_dataset();old,_=recorded_demo.load_dataset();bases=[np.array([0,.305,.75]),np.array([0,-.305,.75])]
relative=[]
for i in range(531,779):
 poses=[]
 for a in(old,new):
  p,R=ik.tcp_pose(a[i,:6],bases[0]);q,S=ik.tcp_pose(a[i,7:13],bases[1]);poses.append((R.T@(q-p),R.T@S))
 relative.append([float(np.linalg.norm(poses[1][0]-poses[0][0])),float(np.linalg.norm(poses[1][1]-poses[0][1]))])
ramp=rows[530:611];z=[];opposed=[];forces=[];travel=[];capspeed=[]
for r in ramp:
 axis=np.asarray(r['can_axis']);z.append(float(r['can'][2]-.005*axis[2]-.065*abs(axis[2])-.026*np.sqrt(max(0,1-axis[2]**2))-(.7475+.05)))
 m=np.asarray(r['left_can_contact_matrix']);opposed.append(bool(np.count_nonzero(np.linalg.norm(m.reshape(-1,3),axis=1)>.01)>=2));forces.append(float(np.linalg.norm(np.asarray(r['right_contact_matrix']).reshape(-1,3),axis=1).max()));travel.append(r['button_travel']);capspeed.append(r['cap_speed'])
result=dict(scope='Source030 OBSERVED ramp support/button measurements plus predicted commanded-FK paired-geometry preservation; not new native proof.',ramp_source_rows=[530,610],minimum_source_can_body_riser_top_clearance_m=min(z),source_ramp_left_two_contact_rows=sum(opposed),source_ramp_rows=len(ramp),max_source_right_all_contact_force_N=max(forces),maximum_source_valve_travel_m=max(travel),maximum_source_cap_speed_m_s=max(capspeed),maximum_relative_tcp_translation_change_m=max(x[0]for x in relative),maximum_relative_tcp_rotation_matrix_change=max(x[1]for x in relative),ramp_added_speed_max_m_s=float(np.linalg.norm([.022,-.002,0])*1.5/4),native_prediction='Translation of observed held body is only a proxy; actual grasp/valve response requires new native run.')
(ROOT/'experiments/spray-shorter-coat-20261116/aimed-choreography-report.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
