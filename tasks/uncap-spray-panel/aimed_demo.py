"""Clock-only replay of an offline common-TCP translation of the original demo.

Online access is ONLY Observation.state_time. No FK, scene, geometry, contacts,
actor state or scorer are imported or read here. Native feasibility is pending.
"""
import hashlib,json,math
from pathlib import Path
import numpy as np
DATA_SHA256='a355dc44db2a9a238eb23617c947650560f40444ae953efee4c17d73526feb05'
METADATA_SHA256='bc0ceb26ada7826af44df2ddb94e38e66c37f583361ca83cee523bf810b63e22'


def load_dataset(folder=None):
 folder=Path(folder)if folder is not None else Path(__file__).parent
 raw=(folder/'aimed_demo_actions.jsonl').read_bytes();meta_raw=(folder/'aimed_demo_metadata.json').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=DATA_SHA256 or hashlib.sha256(meta_raw).hexdigest()!=METADATA_SHA256:raise ValueError('aimed action/metadata hash mismatch')
 meta=json.loads(meta_raw)
 if meta['dataset_sha256']!=DATA_SHA256 or meta['action_count']!=779 or meta['hold_steps']!=40 or meta['total_action_steps']!=819 or meta['control_hz']!=20:raise ValueError('aimed action protocol changed')
 if meta['offset_world_m']!=[.022,-.002,0.]or meta['ramp_start_action']!=530 or meta['ramp_end_action']!=610:raise ValueError('aimed geometry protocol changed')
 rows=[json.loads(line)for line in raw.splitlines()];header=rows.pop(0)
 if header['kind']!='header'or header['action_dim']!=14 or len(rows)!=779 or[r['t']for r in rows]!=list(range(779)):raise ValueError('aimed sequence changed')
 actions=np.asarray([r['action']for r in rows],dtype=float);low=np.asarray(meta['action_lower']);high=np.asarray(meta['action_upper'])
 if actions.shape!=(779,14)or not np.isfinite(actions).all()or low.shape!=(14,)or high.shape!=(14,)or np.any(actions<low)or np.any(actions>high):raise ValueError('aimed action outside original bounds')
 actions.setflags(write=False);return actions,meta


class PlaybackClock:
 def __init__(self,folder=None):self.actions,self.metadata=load_dataset(folder);self.reset()
 def reset(self):self.last_index=None;self.stopped=False
 def command(self,state_time):
  if isinstance(state_time,(bool,np.bool_))or not isinstance(state_time,(int,float,np.integer,np.floating))or not math.isfinite(state_time)or not 0<=state_time<120:raise ValueError('finite20Hz clock required')
  index=round(float(state_time)*20)
  if abs(index/20-float(state_time))>1e-6:raise ValueError('clock must be on20Hz ticks')
  if self.last_index is None and index!=0:raise ValueError('fresh time-zero reset required')
  if self.last_index is not None and index not in(self.last_index,self.last_index+1):raise ValueError('clock skipped or reversed an action')
  if self.stopped and index!=self.last_index:raise RuntimeError('playback already requested stop')
  if index>=819:raise RuntimeError('aimed playback exceeded bounded budget')
  self.last_index=index;self.stopped=index==818
  return self.actions[min(index,778)].copy(),self.stopped


class AimedDemo:
 def __init__(self):
  from inspect_robots.policy import PolicyInfo
  from inspect_robots_yam.config import action_box
  self.clock=PlaybackClock();m=self.clock.metadata
  self.info=PolicyInfo(name='spray_aimed_demo',action_space=action_box(np.asarray(m['action_lower']),np.asarray(m['action_upper'])))
 def bind(self,embodiment_info):
  if float(embodiment_info.control_hz)!=20:raise ValueError('aimed policy requires20Hz')
 def reset(self,scene):self.clock.reset()
 def act(self,observation):
  from inspect_robots.types import Action,ActionChunk
  command,stop=self.clock.command(observation.state_time)
  return ActionChunk(actions=[Action(data=command,meta={'request_stop':True}if stop else{})],control_hz=20.)


def register_policy():
 from inspect_robots.policy import PolicyBase
 from inspect_robots.registry import register
 class AimedPolicy(AimedDemo,PolicyBase):pass
 register('policy','spray_aimed_demo')(AimedPolicy)
 return 'spray_aimed_demo'
