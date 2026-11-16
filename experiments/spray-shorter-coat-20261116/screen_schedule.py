"""Counterfactual030 dose/schedule screen ONLY; no native execution proof."""
import sys,json,argparse,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];TASK=ROOT/'tasks/uncap-spray-panel';sys.path.insert(0,str(TASK))
from scoring import SprayScorer,cell_area_weights
from config import VISIBLE_DOSE,PLAQUE_AREA_M2,MAX_OFF_PLAQUE_AREA_M2,PRESS_TRAVEL

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 rows=[json.loads(l)for l in(a.run/'trajectory.jsonl').read_text().splitlines()]
 data=[json.loads(l)for l in(TASK/'recorded_demo_actions.jsonl').read_text().splitlines()];actions=np.array([r['action']for r in data[1:]])
 scorer=SprayScorer();deltas=[];old=np.zeros(len(scorer.dose));curve=[]
 for i,row in enumerate(rows):
  result=scorer.update(row);dose=np.array(scorer.dose);deltas.append(dose-old);old=dose
  if row['button_travel']>=PRESS_TRAVEL:curve.append(dict(row=i,time=row['time'],button_travel_m=row['button_travel'],**result))
 deltas=np.array(deltas);weights=np.array(cell_area_weights());pressed=np.flatnonzero(deltas.sum(1)>0).tolist()
 def metric(indices):
  dose=deltas[indices].sum(0)if indices else np.zeros(deltas.shape[1]);visible=dose>=VISIBLE_DOSE
  return dict(coverage=float(weights[visible,0].sum()/PLAQUE_AREA_M2),outside_cm2=float(weights[visible,1].sum()*1e4),dose_seconds=float(len([i for i in indices if i in pressed])*.05))
 windows=[]
 for l in range(len(pressed)):
  for h in range(l+1,len(pressed)+1):
   keep=pressed[l:h];m=metric(keep);windows.append(dict(first_row=keep[0],last_row=keep[-1],**m,pass_area=bool(m['coverage']>=.9 and m['outside_cm2']<=MAX_OFF_PLAQUE_AREA_M2*1e4)))
 global_slew=np.abs(np.diff(actions,axis=0)).max(0);release_start=720
 schedules=[]
 # Preserve complete suffix720..778 (first release command throughfinalhold).
 # Each retained action maps to its original POSTSTEP row action+1.
 for last_prefix in range(700,711):
  for bridge in [None,*range(last_prefix+1,720)]:
   retained=list(range(last_prefix+1))+([]if bridge is None else[bridge])+list(range(release_start,len(actions)))
   joints=actions[retained];delta=np.abs(np.diff(joints,axis=0));joins=[]
   for k in range(1,len(retained)):
    if retained[k]!=retained[k-1]+1:
     d=np.abs(joints[k]-joints[k-1]);joins.append(dict(from_action=retained[k-1],to_action=retained[k],max_joint_jump_rad=float(np.r_[d[:6],d[7:13]].max()),delta14=d.tolist(),within_original_per_joint_maximum=bool(np.all(d<=global_slew+1e-12))))
   state_rows=[0,*[i+1 for i in retained]];m=metric(state_rows)
   schedules.append(dict(last_prefix_action=last_prefix,bridge_action=bridge,release_start_action=release_start,retained_action_count=len(retained),removed_action_count=len(actions)-len(retained),remaining_pressed_original_rows=[i for i in state_rows if i in pressed],joins=joins,within_original_per_joint_maximum=all(x['within_original_per_joint_maximum']for x in joins),**m,pass_area=bool(m['coverage']>=.9 and m['outside_cm2']<=MAX_OFF_PLAQUE_AREA_M2*1e4)))
 feasible=[x for x in schedules if x['pass_area']and x['within_original_per_joint_maximum']]
 out=dict(scope='COUNTERFACTUAL retained observed030poststep poses/dose; changing actions changes native dynamics, so this is NOT a scored/newnative run',trace_sha256=hashlib.sha256((a.run/'trajectory.jsonl').read_bytes()).hexdigest(),dataset_sha256=hashlib.sha256((TASK/'recorded_demo_actions.jsonl').read_bytes()).hexdigest(),scorer_sha256=hashlib.sha256((TASK/'scoring.py').read_bytes()).hexdigest(),config_sha256=hashlib.sha256((TASK/'config.py').read_bytes()).hexdigest(),old_recomputed_result=scorer.result(),pressed_rows=pressed,per_pressed_row_curve=curve,original_per_joint_max_delta=global_slew.tolist(),counterfactual_windows=windows,schedule_screens=schedules,feasible_schedules=feasible)
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2)+'\n')
 print('original',scorer.result());print('feasiblewindows',len([x for x in windows if x['pass_area']]),'feasibleschedules',len(feasible))
 for s in feasible[:15]:print({k:v for k,v in s.items()if k!='joins'})
 for n in range(1,9):print('bestwindow',n,sorted([x for x in windows if round(x['dose_seconds']/.05)==n],key=lambda x:(-x['coverage'],x['outside_cm2']))[:1])
if __name__=='__main__':main()
