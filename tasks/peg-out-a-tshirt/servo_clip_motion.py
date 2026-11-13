"""Six-second state-assisted first-peg alignment candidate.

The reference inserts three extra seconds with the handles held open. A bounded
outer loop integrates the desired robot TCP; ordinary joint PI tracks it. It
never adds the measured compliance displacement back into every reference.
"""
import argparse,copy,json
from pathlib import Path
from preserve_spare_motion import compile_preserve_spare


def compile_servo_clip():
    p=compile_preserve_spare();hold=copy.deepcopy(p['frames'][879]);hold['stage']='hold open peg for measured mouth alignment'
    p['frames'][880:880]=[copy.deepcopy(hold) for _ in range(60)]
    p['action_count']=len(p['frames']);p['clip_servo_window']=[820,940]
    p['source_waypoints']+=' Add60 ordinary held-open actions for a total6s alignment window before handle release.'
    p['do_not_run_reason']='Awaiting corrected outer-loop checks on actual058 states; no native successful clip yet.'
    return p


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();d=compile_servo_clip();a.out.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(actions=d['action_count'],clip_servo_window=d['clip_servo_window'])))
