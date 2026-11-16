"""Offline ordinary joint targets, not actor writes or a native success proof."""
import sys,json,hashlib,re,argparse
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];TASK=ROOT/'tasks/uncap-spray-panel';sys.path.insert(0,str(TASK))
from yam_arena import ik
from yam_arena.constants import SHOULDER,WRIST
from recorded_demo import load_dataset as original_dataset
OFFSET=np.array([.022,-.002,0.]);START=530;END=610
BASES=(np.array([0.,.305,.75]),np.array([0.,-.305,.75]))

def compile_actions():
 original,source=original_dataset();actions=original.copy();reports=[]
 for index in range(START+1,len(actions)):
  fraction=ik.smoothstep((index-START)/(END-START));shift=OFFSET*fraction;row={'action_index':index,'fraction':fraction,'offset_world_m':shift.tolist(),'arms':[]}
  for arm in(0,1):
   sl=slice(arm*7,arm*7+6);p,Q=ik.tcp_pose(original[index,sl],BASES[arm]);seed=actions[index-1,sl]
   q,pe,rot_err=ik.solve(p+shift,ik.matrix_to_quat_xyzw(Q),seed,base_pos=BASES[arm],iters=220,damping=.02,tol=1e-8)
   if pe>2e-7 or rot_err>2e-6:raise ValueError(f'IK residual at{index}arm{arm}: {pe}/{rot_err}')
   actions[index,sl]=q;pp,RR=ik.tcp_pose(q,BASES[arm]);row['arms'].append(dict(position_residual_m=float(np.linalg.norm(pp-p-shift)),rotation_residual_rad=float(np.linalg.norm(ik._rot_error(Q,RR)))))
  reports.append(row)
 low=np.asarray(source['action_lower']);high=np.asarray(source['action_upper'])
 if not np.isfinite(actions).all()or np.any(actions<low)or np.any(actions>high):raise ValueError('compiled action outside unchanged original bounds')
 if not np.array_equal(actions[:START+1],original[:START+1])or not np.array_equal(actions[:,[6,13]],original[:,[6,13]]):raise ValueError('prefix/jaw choreography changed')
 velocities=np.array([SHOULDER['velocity']]*3+[WRIST['velocity']]*3);delta=abs(np.diff(actions,axis=0))
 for arm in(0,1):
  if np.any(delta[:,arm*7:arm*7+6]/.05>velocities):raise ValueError('implied joint setpoint speed exceeds unchanged hardware velocity limits')
 header={'kind':'header','action_dim':14,'labels':source['action_order'],'source_dataset_sha256':source['dataset_sha256'],'offline_transform':'common_WORLD_TCP_translation'}
 data='\n'.join(json.dumps(r,separators=(',',':'))for r in[header,*[dict(t=i,action=a.tolist())for i,a in enumerate(actions)]])+'\n';datahash=hashlib.sha256(data.encode()).hexdigest()
 meta=dict(schema='offline-common-tcp-translation-v1',dataset_sha256=datahash,source_dataset_sha256=source['dataset_sha256'],source_metadata_sha256=hashlib.sha256((TASK/'recorded_demo_metadata.json').read_bytes()).hexdigest(),action_count=779,hold_steps=40,total_action_steps=819,control_hz=20,action_order=source['action_order'],action_lower=source['action_lower'],action_upper=source['action_upper'],offset_world_m=OFFSET.tolist(),ramp_start_action=START,ramp_end_action=END,ramp_kind='smoothstep',unchanged_prefix_actions=START+1,unchanged_grippers_all_actions=True,observation_access='ONLY Observation.state_time online; no geometry/scene/contact/telemetry access',native_validated=False,eligibility='Pending fresh native run; CPU IK and command checks only',transport='unchanged float32 adapter cast; original action limits and actuator parameters',trace_mapping='action i held from i/20 to(i+1)/20; native rowi+1 is post-action; original779step duration and40hold preserved')
 (TASK/'aimed_demo_actions.jsonl').write_text(data);metaraw=json.dumps(meta,indent=2)+'\n';(TASK/'aimed_demo_metadata.json').write_text(metaraw);metahash=hashlib.sha256(metaraw.encode()).hexdigest()
 p=TASK/'aimed_demo.py';text=p.read_text();text=re.sub(r"^DATA_SHA256=.*$",f"DATA_SHA256='{datahash}'",text,flags=re.M);text=re.sub(r"^METADATA_SHA256=.*$",f"METADATA_SHA256='{metahash}'",text,flags=re.M);p.write_text(text)
 report=dict(scope='CPU all-waypoint IK/limits only; native trajectory and collisions unproved',dataset_sha256=datahash,metadata_sha256=metahash,source_dataset_sha256=source['dataset_sha256'],offset_world_m=OFFSET.tolist(),ramp_start_action=START,ramp_end_action=END,max_position_residual_m=max(a['position_residual_m']for r in reports for a in r['arms']),max_rotation_residual_rad=max(a['rotation_residual_rad']for r in reports for a in r['arms']),original_max_joint_delta=np.abs(np.diff(original,axis=0)).max(0).tolist(),aimed_max_joint_delta=delta.max(0).tolist(),maximum_joint_setpoint_speed_rad_s=(delta[:,:6].max(0)/.05).tolist(),rows=reports)
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args();result=compile_actions();args.out.write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items()if k!='rows'})
