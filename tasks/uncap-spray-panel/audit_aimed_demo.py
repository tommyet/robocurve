"""Verify actual ordinary applied commands match the frozen aimed clock policy."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from aimed_demo import PlaybackClock,DATA_SHA256

def audit(run):
 run=Path(run);logs=list((run/'actions').glob('*/*.jsonl'))
 if len(logs)!=1:raise ValueError('expected exactly one episode action log')
 lines=[json.loads(x)for x in logs[0].read_text().splitlines()];header=lines.pop(0)
 clock=PlaybackClock();steps=len(lines)
 if header['action_dim']!=14 or not 1<=steps<=clock.metadata['total_action_steps']:raise ValueError('wrong applied action count/dimension')
 if[x['t']for x in lines]!=list(range(steps)):raise ValueError('noncontiguous applied commands')
 expected=np.asarray([clock.command(i/20)[0]for i in range(steps)]);actual=np.asarray([x['action']for x in lines])
 if actual.shape!=expected.shape or not np.array_equal(actual,expected):raise ValueError('actual applied commands differ from frozen aimed schedule')
 rows=[json.loads(x)for x in (run/'trajectory.jsonl').read_text().splitlines()]
 if len(rows)!=steps+1 or any(x.get('controller')is not None for x in rows):raise ValueError('wrong trace alignment or privileged online controller telemetry')
 return dict(passed=True,applied_controls=steps,dataset_sha256=DATA_SHA256,
             action_log_sha256=hashlib.sha256(logs[0].read_bytes()).hexdigest(),
             trace_sha256=hashlib.sha256((run/'trajectory.jsonl').read_bytes()).hexdigest(),
             scope='Actual commands match pinned offline-generated aim path; independent score audit required')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path);print(json.dumps(audit(p.parse_args().run),indent=2))
