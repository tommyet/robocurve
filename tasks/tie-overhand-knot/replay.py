"""Recompute a recorded rope trial from geometry and its saved configuration."""
import argparse
import json
from pathlib import Path

from scoring import replay_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trajectory', type=Path)
    parser.add_argument('--runtime', type=Path,
                        help='Saved runtime.json; defaults to the trajectory directory')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    runtime = args.runtime or args.trajectory.parent / 'runtime.json'
    metadata = json.loads(runtime.read_text())
    config = metadata['task_config']
    if not all(name in config for name in ('length', 'mass', 'radius', 'segment')):
        parser.error('runtime.json lacks the recorded physical configuration')
    result = replay_file(args.trajectory, config)
    text = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(text)
    print(text, end='')


if __name__ == '__main__':
    main()
