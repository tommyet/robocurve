"""CPU snapshot/nominal-route work only; no native state cache or mutation."""
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,'/private/tmp/spray-yam-source')
from pathlib import Path
import json,numpy as np
from yam_arena import ik
from yam_arena.urdf import quat_xyzw_to_matrix,axis_angle_matrix
from scene import layout
ROOT=Path(__file__).parent
ROW=json.loads((ROOT/'snapshot-row.json').read_text());REPORT=json.loads((ROOT/'route321.json').read_text());SAMPLES=REPORT['samples'];RIGHT=next(h for h in ROW['native_hands']if h['side']=='right');H=next(h for h in layout()[1]if h['b']=='north_bottom')
def inputs(index):
 s=SAMPLES[index];poses={n:np.array(v)for n,v in ROW['poses'].items()}
 if s['phase']=='supported_arc_contact':
  v=poses['north_bottom'];R=quat_xyzw_to_matrix(v[3:]);wallR=quat_xyzw_to_matrix(poses['north'][3:]);pivot=v[:3]+R@H['anchor_b'];newR=axis_angle_matrix(wallR[:,0],np.radians(s['value']-ROW['angles_deg']['north_bottom_hinge']))@R
  poses['north_bottom']=np.r_[pivot-newR@H['anchor_b'],ik.matrix_to_quat_xyzw(newR)]
 return dict(q=np.array(s['q']),fingers=np.array(s['fingers']),poses=poses,cutter=np.array(ROW['cutter_pose']),right_q=np.array(RIGHT['joints']),right_fingers=np.array(RIGHT['finger_joints']),contact=s['phase']in('contact_acquire','supported_arc_contact'))
def selected():
 out=[0]
 for phase in dict.fromkeys(s['phase']for s in SAMPLES):
  ids=[i for i,s in enumerate(SAMPLES)if s['phase']==phase];out.append(ids[len(ids)//2])
 return list(dict.fromkeys(out))
def tick(model,index):
 # Controller work shape: actual FK guard, pinned IK to nearbynext target,
 # then distinct bounded-command guard. Both use SAME freshworld inputs.
 d=inputs(index);first=model.check(**d);s=SAMPLES[min(index+1,len(SAMPLES)-1)]
 q,pe,re=ik.solve(s['tcp'],ik.matrix_to_quat_xyzw(np.array(s['R'])),d['q'],base_pos=(0,.305,.75),iters=800 if d['contact']else 240,tol=1e-6 if d['contact']else 1e-4)
 d['q']=q;second=model.check(**d)
 return first,second,pe,re
