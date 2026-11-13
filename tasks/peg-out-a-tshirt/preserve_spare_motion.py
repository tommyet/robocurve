"""Candidate first clip that leaves the second spare peg accessible.

It approaches the target handles from below. Native043/050 showed that the
old diagonal pass pushed the other peg from the line. This is an ordinary
joint plan, with optional separately disclosed reset-state grasp calibration.
"""
import argparse,json
from pathlib import Path
from flip_attach_motion import compile_flip_attach


def compile_preserve_spare():
    p=compile_flip_attach(grasp_x=.220,approach_depth=.010,
        clip_target=(.4787,.115,1.115),approach_from_below=True)
    p['requires_joint_feedback_from']=700
    p['feedback']='bounded right-arm joint feedback after700; reset cloth calibration is a separate explicit runner option'
    p['source_waypoints']='Translate below both free spare pegs before rising around the first handles. The previously demonstrated squeeze, free peg withdrawal/turn, corrected clip target and release sequence remain unchanged.'
    p['do_not_run_reason']='Awaiting all-frame fixture, opposite-arm and unused-peg hull rejection checks; later cloth/peg retention still requires native evidence.'
    return p


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();plan=compile_preserve_spare()
    args.out.write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(dict(actions=plan['action_count'],max_position_error_m=max(x['max_position_error_m'] for x in plan['kinematic_audit'])),indent=2))
