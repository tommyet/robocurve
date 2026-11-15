"""Data-only ordinary-action input for a continuous teleoperated demonstration.

The simulator waits between control actions while an operator plans a segment.
This module cannot change scene state or run supplied code. Every accepted
segment is bounded, saved and replayable as ordinary joint/finger commands.
"""
import json
import time
from pathlib import Path
import numpy as np


def validate(payload, *, step, previous, low, high, limits, remaining):
    if payload.get('schema')!='ordinary-demo-actions-v1' or payload.get('start_step')!=step:
        raise ValueError('Control segment belongs to a different action boundary')
    frames=payload.get('frames')
    if not isinstance(frames,list) or not 1<=len(frames)<=remaining:
        raise ValueError('Control segment exceeds the remaining action limit')
    if type(payload.get('final')) is not bool:
        raise ValueError('Control segment must declare whether it finishes the demo')
    actions=np.asarray([f['action14'] for f in frames],float)
    if actions.shape!=(len(frames),14) or not np.isfinite(actions).all():
        raise ValueError('Expected finite ordinary 14-dimensional actions')
    if np.any(actions<low) or np.any(actions>high):
        raise ValueError('Control segment exceeds ordinary joint bounds')
    if np.any(abs(np.diff(np.vstack((previous,actions)),axis=0))>limits*1.001):
        raise ValueError('Control segment exceeds ordinary joint speeds')
    return [dict(action14=a.tolist(),stage=str(f.get('stage','operator-planned action')))
            for a,f in zip(actions,frames)]


def wait(directory, step, timeout_s=1800):
    path=Path(directory)/f'actions-{step:04d}.json'
    deadline=time.monotonic()+timeout_s
    while not path.is_file():
        if time.monotonic()>deadline:
            raise TimeoutError('No ordinary demonstration actions arrived within the planning timeout')
        time.sleep(.25)
    return json.loads(path.read_text())
