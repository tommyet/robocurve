"""Clock-only replay of disclosed fixed-layout teacher commands; fresh proof pending.

No teacher, telemetry, scene, object state, FK, native API, or feedback imports.
Only Observation.state_time is read. reset ignores the supplied scene entirely.
"""
import hashlib,json,math
from pathlib import Path
import numpy as np
DATA_SHA256='18c5770b6db55699669193644402a8e3ccc033e656436fc910a9111e3ff0bd63'
METADATA_SHA256='9db927ff0674d36e6a11d82f81e314dfad6eedbcabd1ae139879feb318d75d71'
TRACE_SHA256='724856a92bb31df854fd49403fdf10c83415855133be994331406b2ab5550997'

def load_dataset(folder=None):
 folder=Path(folder)if folder is not None else Path(__file__).parent
 raw=(folder/'recorded_demo_actions.jsonl').read_bytes();metadata_raw=(folder/'recorded_demo_metadata.json').read_bytes()
 if hashlib.sha256(metadata_raw).hexdigest()!=METADATA_SHA256:raise ValueError('recorded action metadata hash mismatch')
 meta=json.loads(metadata_raw)
 if hashlib.sha256(raw).hexdigest()!=DATA_SHA256 or meta['dataset_sha256']!=DATA_SHA256:raise ValueError('recorded applied-action dataset hash mismatch')
 if meta['teacher_trace_sha256']!=TRACE_SHA256 or meta['action_count']!=779 or meta['hold_steps']!=40 or meta['total_action_steps']!=819 or meta['control_hz']!=20:raise ValueError('recorded action protocol changed')
 rows=[json.loads(line)for line in raw.splitlines()];header=rows.pop(0)
 if header['kind']!='header' or header['action_dim']!=14 or header['labels']!=meta['action_order'] or len(rows)!=779 or [r['t']for r in rows]!=list(range(779)):raise ValueError('recorded action sequence changed')
 actions=np.array([r['action']for r in rows],dtype=np.float64);low=np.array(meta['action_lower']);high=np.array(meta['action_upper'])
 if actions.shape!=(779,14) or not np.isfinite(actions).all() or low.shape!=(14,)or high.shape!=(14,)or not np.isfinite([low,high]).all()or np.any(actions<low)or np.any(actions>high):raise ValueError('recorded action outside original finite14D bounds')
 actions.setflags(write=False)
 return actions,meta

class PlaybackClock:
 def __init__(self,folder=None):self.actions,self.metadata=load_dataset(folder);self.reset()
 def reset(self):self.last_index=None;self.stopped=False
 def command(self,state_time):
  if isinstance(state_time,(bool,np.bool_))or not isinstance(state_time,(int,float,np.integer,np.floating))or not math.isfinite(state_time)or state_time<0 or state_time>=120:raise ValueError('finite clock within0..120s required')
  index=round(float(state_time)*20)
  if abs(index/20-float(state_time))>1e-6:raise ValueError('clock must be on20Hz control ticks')
  if self.last_index is None and index!=0:raise ValueError('recorded policy requires fresh time-zero reset')
  if self.last_index is not None and index not in (self.last_index,self.last_index+1):raise ValueError('clock skipped or reversed a recorded action')
  if self.stopped and index!=self.last_index:raise RuntimeError('playback already requested stop')
  total=len(self.actions)+self.metadata['hold_steps']
  if index>=total:raise RuntimeError('recorded playback exceeded bounded action budget')
  self.last_index=index;self.stopped=index==total-1
  return self.actions[min(index,len(self.actions)-1)].copy(),self.stopped

class RecordedDemo:
 def __init__(self):
  from inspect_robots.policy import PolicyInfo
  from inspect_robots_yam.config import action_box
  self.clock=PlaybackClock();m=self.clock.metadata
  self.info=PolicyInfo(name='spray_recorded_demo',action_space=action_box(np.array(m['action_lower']),np.array(m['action_upper'])))
 def bind(self,embodiment_info):
  if float(embodiment_info.control_hz)!=20:raise ValueError('recorded policy requires20Hz')
 def reset(self,scene):self.clock.reset()
 def act(self,observation):
  from inspect_robots.types import Action,ActionChunk
  command,stop=self.clock.command(observation.state_time)
  return ActionChunk(actions=[Action(data=command,meta={'request_stop':True}if stop else {})],control_hz=20.)

def register_policy():
 from inspect_robots.policy import PolicyBase
 from inspect_robots.registry import register
 class RecordedPolicy(RecordedDemo,PolicyBase):pass
 register('policy','spray_recorded_demo')(RecordedPolicy)
 return 'spray_recorded_demo'
