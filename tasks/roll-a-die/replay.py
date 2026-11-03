"""Recompute a die-roll score from the retained motion audit."""

import argparse
import json
from pathlib import Path

from scoring import RollTracker


def replay(path):
    tracker = RollTracker()
    count = 0
    for line in Path(path).read_text().splitlines():
        if line.strip():
            tracker.update(json.loads(line))
            count += 1
    if not count:
        raise ValueError("empty trajectory")
    return tracker.summary()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trajectory")
    args = parser.parse_args()
    print(json.dumps(replay(args.trajectory), indent=2))
