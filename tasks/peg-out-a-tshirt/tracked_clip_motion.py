"""Candidate clip with a deeper hem bite and ordinary joint tracking.

Native043 proved free peg removal/rotation, but the insertion hand deflected
24mm upward and the garment crept out of its pinch. Keep the same reference
route, insert10mm farther into the hem initially, then correct right-arm joint
tracking after action700. This uses no object/material-state feedback.
"""
import argparse,json
from pathlib import Path
from flip_attach_motion import compile_flip_attach


def compile_tracked_clip():
    p=compile_flip_attach(grasp_x=.230,clip_target=(.4787,.115,1.115))
    p['requires_joint_feedback_from']=700
    p['feedback']='right-arm ordinary joint positions only; bounded PI after action700, no object/assessor state'
    p['source_waypoints']='Native043 peg removal/turn retained a stable hand-relative pose. Center the open mouth on the line using native043 hand/peg transform (5.3mm forward/1mm upward reference correction),10mm deeper initial hem pinch. Bounded right-arm joint tracking corrects observed insertion deflection; native revalidation required.'
    p['do_not_run_reason']='Awaiting new full-pose hull/line rejection check and runtime tracking CPU checks.'
    return p


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();d=compile_tracked_clip();a.out.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(actions=d['action_count'],max_position_error_m=max(x['max_position_error_m'] for x in d['kinematic_audit'])),indent=2))
