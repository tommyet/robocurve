"""Replay measured unboxing telemetry without the simulator."""
import argparse
import json
from scoring import UnboxScorer

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('trajectory');args=p.parse_args()
    tracker=UnboxScorer()
    previous=-1.
    with open(args.trajectory) as f:
        for line in f:
            s=json.loads(line)
            if s['time']<=previous: raise ValueError('timestamps must strictly increase')
            previous=s['time'];tracker.update(s)
    print(json.dumps(tracker.result(),indent=2))

if __name__=='__main__': main()
