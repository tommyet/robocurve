"""Load a frozen diagnostic joint trajectory. No object-state policy feedback.

The 14-D actions are normal YAM joint and finger commands. A file passing this
check says nothing about physical cloth contact, knot topology or task success.
The runner separately checks the ordinary adapter limits and command speeds.
"""
import json
from pathlib import Path
import numpy as np


def load(path):
    data=json.loads(Path(path).read_text())
    if data.get('schema')!='cloth-fixed-motion-v1' or data.get('control_hz')!=20:
        raise ValueError('Unexpected motion schema or rate')
    frames=data.get('frames',[])
    actions=np.asarray([f['action14'] for f in frames],dtype=float)
    if actions.ndim!=2 or actions.shape[1]!=14 or not 1<=len(actions)<=1200 or not np.isfinite(actions).all():
        raise ValueError('A motion probe needs 1–1200 finite 14-D joint commands')
    if np.any(actions[:,[6,13]]<0.) or np.any(actions[:,[6,13]]>1.):
        raise ValueError('Grippers must be normalized to [0,1]')
    return data,actions
