"""Read-only 013 command/response replay; no simulated closed-loop claim."""
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,'/private/tmp/spray-yam-source')
from pathlib import Path
import json,hashlib,time
import numpy as np
from fast_safety import ScoopSafety
from workload import inputs,SAMPLES,ROOT
from yam_arena import ik
source=Path('/private/tmp/carton-open013-approved-source')
d=json.loads((source/'recent100-diagnosis.json').read_text());rows=[json.loads(x)for x in(source/'recent100-raw.jsonl').read_text().splitlines()]
qa=np.array([x['actual_joint_q_poststep']for x in d]);qcmd=np.array([x['issued_joint_q']for x in d]);residual=qcmd-qa;bias=np.median(residual,axis=0)
issued=np.array([x['issued_tcp_FK']for x in d]);actual=np.array([x['actual_tcp_poststep']for x in d]);reference=np.array([x['reported_reference_tcp']for x in d]);preactual=np.array([x['reported_actual_tcp_PRESTEP']for x in d])
angle=lambda a,b:float(np.degrees(np.arccos(np.clip((np.trace(np.array(a)@np.array(b).T)-1)/2,-1,1))))
model=ScoopSafety();checks=[]
# Same actual current scene on each row, only hypothetical ordinary q targets
# changed. This checks command geometry, not the resulting native response.
for row in rows[::10]+[rows[-1]]:
 left=next(h for h in row['native_hands']if h['side']=='left');right=next(h for h in row['native_hands']if h['side']=='right');q=np.array(row['action_14d'][:6]);candidate=q+bias
 args=dict(fingers=np.array(left['finger_joints']),poses={n:np.array(v)for n,v in row['poses'].items()},cutter=np.array(row['cutter_pose']),right_q=np.array(right['joints']),right_fingers=np.array(right['finger_joints']),contact=False)
 plain=model.check(q=q,**args);augmented=model.check(q=candidate,**args)
 checks.append(dict(time_s=row['time'],candidate_q=candidate.tolist(),nominal=plain,augmented=augmented))
# Scope probe only: applying this SAME free-space offset everywhere is not a
# controller recommendation. It tests why a compensation transfer needs guards.
route=[]
for i in range(len(SAMPLES)):
 args=inputs(i);args['q']=args['q']+bias;result=model.check(**args)
 route.append(dict(index=i,phase=SAMPLES[i]['phase'],**result))
held=np.r_[False,np.diff([x['fraction']for x in d])<1e-12]
report=dict(status='READ_ONLY_RECOMMENDATION_NOT_IMPLEMENTED',native013_status='intentionally_cancelled_before_contact_not_controller_failure',window_s=[d[0]['time'],d[-1]['time']],samples=len(d),reference_hold_rows=int(held.sum()),median_command_minus_actual_joint_rad=bias.tolist(),held_cursor_median_joint_residual_rad=np.median(residual[held],axis=0).tolist(),median_commandFK_minus_postactual_TCP_m=np.median(issued-actual,axis=0).tolist(),median_reference_minus_preactual_TCP_m=np.median(reference-preactual,axis=0).tolist(),reference_to_issuedFK_m={'median':float(np.median(np.linalg.norm(reference-issued,axis=1))),'max':float(np.max(np.linalg.norm(reference-issued,axis=1)))},issuedFK_to_postactual_rotation_deg={'median':float(np.median([angle(x['issued_R_FK'],x['actual_R_poststep'])for x in d])),'max':float(max(angle(x['issued_R_FK'],x['actual_R_poststep'])for x in d))},reported_hand_contact_force_max_N={'target':max(x['target_force_N']for x in d),'other':max(x['other_force_N']for x in d)},hypothetical_same_scene_checks=checks,all_sampled_augmented_commands_safe=all(x['augmented']['safe']for x in checks),minimum_augmented_hard_gap_m=min(x['augmented']['hard_gap_m']for x in checks),minimum_augmented_other_arm_gap_m=min(x['augmented']['other_arm_aabb_gap_m']for x in checks),universal_frozen_bias_route_scope_probe={'cases':len(route),'unsafe_count':sum(not x['safe']for x in route),'minimum_hard_gap_m':min(x['hard_gap_m']for x in route),'minimum_other_arm_gap_m':min(x['other_arm_aabb_gap_m']for x in route),'limiting_case':min(route,key=lambda x:x['hard_gap_m']),'warning':'Constant above-aperture residual is configuration-dependent; not a validated transfer to supported contact.'},recommendation={'controller_change':'Bounded proprioceptive joint target offset PI is justified for a separate reviewed free-space test. No gate relaxation or mechanical gain changes.','reference':'Store unbiased q reference separately from augmented ordinary14D action; add b exactly once. Do not seed a new nominal reference from augmented FK and then add b again. Preserve exact previous command at handoffs.','bounds':'Candidate initial review: existing +/-20mrad total bias and <=.25mrad/frame, explicit joint/action-limit antiwindup; gain/velocity damping to be agreed with Astra before implementation. The 8.35mrad joint6 residual fits this envelope.','safety':'Run unchanged315-piece actual and actual augmented-action candidate guard every tick; retain precontact north_bottom as hard obstacle. No unreviewed contact extension.','reuse_cut_I':'Existing Ki.5/s Cartesian I (75um normstep,3mm component cap) covers the observed translation scale but does not itself compensate rotation and would need the same independent-unbiased-reference/handoff proof. Joint PI addresses both pose components.','proof_limit':'Read-only replay proves a residual and checks hypothetical command geometry, not closed-loop stability, all-substep contact absence, or future native retention.'},source_sha256={name:hashlib.sha256((source/name).read_bytes()).hexdigest()for name in('recent100-raw.jsonl','recent100-diagnosis.json','recent100-estimate.json')})
(ROOT/'tracking-recommendation.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:report[k]for k in('median_command_minus_actual_joint_rad','all_sampled_augmented_commands_safe','minimum_augmented_hard_gap_m','minimum_augmented_other_arm_gap_m','universal_frozen_bias_route_scope_probe')},indent=2))
