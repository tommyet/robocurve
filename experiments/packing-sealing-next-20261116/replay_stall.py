"""Rebuild planner history with logged gates; independently rerun REAL315 at finalprestate.
Logged gate replay is state reconstruction, not independent validation of earlierstates.
"""
import sys,json,hashlib,argparse,copy
from pathlib import Path
from types import SimpleNamespace
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tasks/pack-and-tape-carton'))
from robot import ClosureProbe
from test_roll_probe import Tensor
from roll_probe import BASES
from check_roll_probe import nominal_poses
from yam_arena import ik
from yam_arena.constants import READY,FINGER_OPEN

def reconstruct(source):
 raw=(source/'trajectory.jsonl').read_bytes();rows=[json.loads(l)for l in raw.splitlines()];owners=json.loads((source/'capture-manifest.json').read_text())['owners'];state={'poses':{n:[*p,*ik.matrix_to_quat_xyzw(R)]for n,(p,R)in nominal_poses().items()}}
 ready=np.r_[READY,1.,READY,1.].astype(np.float32).astype(float);scene={s+'_robot':SimpleNamespace(data=SimpleNamespace(joint_pos=Tensor([[*ready[j*7:j*7+6],FINGER_OPEN,FINGER_OPEN]])))for j,s in enumerate(('left','right'))}
 env=SimpleNamespace(_ready=Tensor([ready]),_low=np.r_[ik.LOWER,0.,ik.LOWER,0.],_high=np.r_[ik.UPPER,1.,ik.UPPER,1.],_ids={s+'_robot':(list(range(6)),[6,7])for s in('left','right')},rig=SimpleNamespace(bases=BASES),_base=SimpleNamespace(arena_world=SimpleNamespace(get_pose_w=lambda n:Tensor([state['poses'][n]])),scene=scene));probe=ClosureProbe(env);real=probe.geometry;maxerr=0.;snap=None
 for i,row in enumerate(rows):
  if i:
   prev=rows[i-1];state['poses']={owners[path]['entity']:pose for path,pose in prev['native_body_world_poses'].items()if owners[path]['kind']=='object'}
   for j,s in enumerate(('left','right')):
    h=prev['native_hands'][j];scene[s+'_robot'].data.joint_pos=Tensor([[*h['joints'],*h['finger_joints']]])
   probe.previous=np.asarray(prev['action_14d'],float)
  if i==len(rows)-1:
   snap=probe.candidate_state();snap={k:v.tolist()if isinstance(v,np.ndarray)else v for k,v in snap.items()};prestate=copy.deepcopy(state['poses']);pre_hands=copy.deepcopy(rows[i-1]['native_hands']);previous=probe.previous.tolist();probe.geometry=real
  else:
   report=row['robot_control'];calls=[report['clearance_actual'],report['clearance_previous'],*[t['clearance']for t in report['advance_trials']]];at=[0]
   def check(*args,**kwargs):
    n=at[0];at[0]+=1;return calls[min(n,len(calls)-1)]
   probe.geometry=SimpleNamespace(check=check)
  action,out=probe.command(i*.05);maxerr=max(maxerr,float(np.max(np.abs(action-np.asarray(row['action_14d'])))))
 final=dict(trace_sha256=hashlib.sha256(raw).hexdigest(),source_row_count=len(rows),command_time_s=(len(rows)-1)*.05,post_state_time_s=rows[-1]['time'],state_reconstruction='Earlier numeric geometry reports replayed only to reconstruct planner state; final actual/previous/allcandidate guards independently recomputed using real315mesh geometry.',maximum_replayed_action_difference=maxerr,prestate=dict(poses=prestate,hands=pre_hands,previous_action=previous,planner=snap),recomputed_final_report=out,native_final_report=rows[-1]['robot_control'])
 return final
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=reconstruct(a.source);a.out.write_text(json.dumps(r,indent=2)+'\n');print({k:v for k,v in r.items()if k not in('prestate','native_final_report','recomputed_final_report')});print({k:r['recomputed_final_report'].get(k)for k in('phase','advance_fraction','failure','clearance_previous','advance_trials')})
