"""Replay every measured sample and verify stage evidence against source hashes."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from scoring import SprayScorer
from config import PRESS_TRAVEL

def verify_final_full_score_hold(rows):
    """Require one real second of consecutive full-score endpoint samples."""
    if not rows or rows[-1]['metrics']['score']!=1.:raise ValueError('no final full score')
    first=len(rows)-1
    while first>0 and rows[first-1]['metrics']['score']==1.:first-=1
    tail=rows[first:]
    if (tail[-1]['time']-tail[0]['time']<1.-1e-8 or
        any(abs(b['time']-a['time']-.05)>1e-8 for a,b in zip(tail,tail[1:]))):
        raise ValueError('video trace lacks a continuous one-second final full-score hold')
    return dict(first_full_score_time_s=tail[0]['time'],final_time_s=tail[-1]['time'],
                full_score_elapsed_s=tail[-1]['time']-tail[0]['time'],full_score_samples=len(tail))


def audit(run):
    rows=[json.loads(x) for x in (run/'trajectory.jsonl').read_text().splitlines()]
    if not rows:raise ValueError('empty trial')
    hashes=json.loads((run/'source-sha256.json').read_text())
    for name,expected in hashes.items():
        actual=hashlib.sha256((run/'source'/name).read_bytes()).hexdigest()
        if actual!=expected:raise ValueError('snapshot hash mismatch: '+name)
    # Replaying a different current scorer would not audit the recorded trial.
    for name in ('config.py','scoring.py'):
        if hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()!=hashes[name]:
            raise ValueError('audit interpreter must use matching '+name)
    scorer=SprayScorer();detached=False;presses=0;errors=[]
    max_ik=0.;max_rot=0.
    for row in rows:
        result=scorer.update(row)
        for key,value in result.items():
            original=row['metrics'][key]
            same=(abs(original-value)<1e-7 if isinstance(value,(int,float)) and not isinstance(value,bool) else original==value)
            if not same:errors.append((row['time'],key,original,value))
        if row['cap_detached']:detached=True
        if detached and row['button_travel']>=PRESS_TRAVEL:presses+=1
        for e in (row.get('controller') or {}).get('errors',{}).values():
            max_ik=max(max_ik,e['position']);max_rot=max(max_rot,e['rotation'])
        for h in row.get('hands',[]):
            if not all(math.isfinite(q) for q in h['joints']):raise ValueError('nonfinite arm joints')
    if errors:raise ValueError('replay differs: '+str(errors[:3]))
    if len(rows)!=round(rows[-1]['time']*20)+1:raise ValueError('missing control samples')
    summary=json.loads((run/'score-summary.json').read_text())
    if abs(summary['score']-scorer.value)>1e-7:raise ValueError('summary score mismatch')
    if scorer.value==1. and (not detached or not presses):raise ValueError('full score without physical cap/press evidence')
    final_hold=verify_final_full_score_hold(rows) if scorer.value==1. else None
    return dict(passed=True,trace_sha256=hashlib.sha256((run/'trajectory.jsonl').read_bytes()).hexdigest(),samples=len(rows),control_steps=len(rows)-1,
                duration=rows[-1]['time'],score=scorer.value,cap_detached=detached,
                depressed_control_samples=presses,max_planned_ik_error_m=max_ik,
                max_planned_ik_rotation_rad=max_rot,metrics=scorer.result(),
                final_full_score_hold=final_hold,
                scope='source integrity, all-sample scorer replay and measured stage evidence; not contact-force calibration')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path)
    args=p.parse_args();print(json.dumps(audit(args.run),indent=2))
