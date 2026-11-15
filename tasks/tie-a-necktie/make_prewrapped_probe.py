"""Write a holding-action diagnostic plan; this does not run a simulator."""
import argparse
import hashlib
import json
from pathlib import Path
from staged_grasp import initial_action

HERE = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--steps', type=int, default=100)
    args = parser.parse_args()
    if not 1 <= args.steps <= 3600:
        parser.error('Use 1 to 3600 ordinary actions')
    action = initial_action().tolist()
    plan = dict(schema='cloth-fixed-motion-v1', control_hz=20,
                requires_inside_out_reset=True, requires_adult_collar=True,
                requires_staged_start=True, requires_state_assisted_handoff=False,
                fixture_source_sha256=hashlib.sha256((HERE/'adult_layout.py').read_bytes()).hexdigest(),
                kind='unscored pre-wrapped reset diagnostic',
                frames=[dict(action14=action, stage='hold the disclosed starting grips')
                        for _ in range(args.steps)])
    args.out.write_text(json.dumps(plan, indent=2)+'\n')

if __name__ == '__main__':
    main()
