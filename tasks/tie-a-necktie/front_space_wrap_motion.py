"""Candidate: make room in front of the collar before wrapping the wide end.

Native032's behind pass loaded the strip against the shoulder edge. The same
retained initial pinch is moved forward and slightly upward before wrapping;
this creates ordinary working space without a fixture or material change.
"""
import argparse,json
from pathlib import Path
from stabilized_wrap_motion import compile_stabilized_wrap


def compile_front_space():
    plan=compile_stabilized_wrap(narrow_position=(.350,.117,.883),wide_rear=.430,tail_z=.873,tail_y=.117)
    plan['waypoint_evidence']='First680 actions preserve native032 front crossing; pinch the narrow tail15 mm above its tip, then move it60 mm forward and10 mm up. This keeps the working wrap in front of the shoulder and the held narrow point below the dangling wide tip. Native material state is offline diagnosis only.'
    return plan


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    plan=compile_front_space();args.out.write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps(dict(actions=plan['action_count'],max_position_error_m=max(a['max_position_error_m'] for a in plan['kinematic_audit'])),indent=2))
