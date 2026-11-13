"""Candidate: retain a longer narrow tail below the physical pinch.

Native035 cleared the shoulder but the15mm tail escaped when crossing loaded
it. Grasp40mm above the tip, then move it to the previously clear holding pose. No material law or fixture changes are made.
"""
import argparse,json
from pathlib import Path
from stabilized_wrap_motion import compile_stabilized_wrap


def compile_deeper_bite():
    plan=compile_stabilized_wrap(narrow_position=(.350,.117,.883),wide_rear=.430,tail_z=.898,tail_y=.117,tail_yaw=-15.)
    plan['waypoint_evidence']='First680 actions preserve native035 front crossing. The narrow pinch moves25mm farther from its tip, leaving about40mm of material below it, and returns to the already clear holding pose with a60mm forward/15mm downward motion. This is an ordinary contact technique candidate, with no online cloth feedback.'
    return plan


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    plan=compile_deeper_bite();args.out.write_text(json.dumps(plan,indent=2)+'\n')
    print(json.dumps({'actions':plan['action_count'],'max_position_error_m':max(a['max_position_error_m'] for a in plan['kinematic_audit'])},indent=2))
