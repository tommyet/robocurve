"""Read-only native fingertip forces for carton diagnostics and flap acquisition.

Family sums make no column-order claim. Selected-flap reads use separately
configured singleton filters and verify native target paths and fingertip row
order before exposing an acquisition signal. This reader never applies force.
"""
import numpy as np
TARGETS=('north','east','south','west','north_top','east_top','south_top','west_top','north_bottom','east_bottom','south_bottom','west_bottom')
SIDES=('left','right')
FLAPS=('east_top','west_top','north_top','south_top')
def add_sensors(embodiment):
 from isaaclab.sensors import ContactSensorCfg
 from isaaclab_arena.utils.configclass import make_configclass
 from yam_arena.robot import asset_link_paths
 paths=asset_link_paths();a,b=paths['tip_left'],paths['tip_right']
 if a.rsplit('/',1)[0]!=b.rsplit('/',1)[0]:raise RuntimeError('unverified fingertip hierarchy')
 cfg=embodiment.scene_config;fields=[(n,type(getattr(cfg,n)),getattr(cfg,n))for n in cfg.__class__.__annotations__]
 for side,root in [('left','LeftArm'),('right','RightArm')]:
  sensor=ContactSensorCfg(prim_path='{ENV_REGEX_NS}/'+root+a.rsplit('/',1)[0]+'/tip_.*',update_period=0.,track_pose=False,filter_prim_paths_expr=['{ENV_REGEX_NS}/'+n for n in TARGETS])
  fields.append((side+'_carton_contacts',ContactSensorCfg,sensor))
  for target in FLAPS:
   selected=ContactSensorCfg(prim_path='{ENV_REGEX_NS}/'+root+a.rsplit('/',1)[0]+'/tip_.*',update_period=0.,track_pose=False,filter_prim_paths_expr=['{ENV_REGEX_NS}/'+target])
   fields.append((side+'_closure_'+target+'_contacts',ContactSensorCfg,selected))
 embodiment.scene_config=make_configclass('PackingClosureContactCfg',fields)()
def summarize(force,names,targets=TARGETS):
 force=np.asarray(force,float)
 if force.shape!=(1,2,len(targets),3)or len(names)!=2 or set(names)!={'tip_left','tip_right'}:raise ValueError('carton contact shape/body mismatch')
 if not np.isfinite(force).all():raise ValueError('nonfinite carton contact force')
 net=force[0].sum(axis=(0,1))
 return dict(body_names=list(names),configured_target_family=list(targets),individual_filter_column_order_native_verified=False,normal_force_matrix_w=force[0].tolist(),family_normal_force_on_fingertips_w_N=net.tolist(),family_normal_force_norm_N=float(np.linalg.norm(net)),family_sum_of_normal_force_magnitudes_N=float(np.linalg.norm(force[0],axis=-1).sum()))
def native_array(value):
 value=value.torch if hasattr(value,'torch') else value
 if hasattr(value,'detach'):return value.detach().cpu().numpy()
 if hasattr(value,'numpy'):return value.numpy()
 return np.asarray(value)

def _paths(value):
 if isinstance(value,str):return [value]
 if isinstance(value,bytes):return [value.decode()]
 if isinstance(value,np.ndarray):value=value.tolist()
 if isinstance(value,(list,tuple)):return [path for item in value for path in _paths(item)]
 raise ValueError('unrecognized native contact path binding')

def verify_singleton_binding(sensor,target,side):
 """Check native target/body paths, not just configured filter expressions."""
 if target not in FLAPS or side not in SIDES:raise ValueError('invalid singleton contact binding request')
 view=getattr(sensor,'contact_view',None)
 if view is None:raise ValueError('native contact view binding unavailable')
 if not hasattr(view,'filter_paths') or not hasattr(view,'sensor_paths'):raise ValueError('native contact path readback unavailable')
 raw_filters=list(view.filter_paths);bodies=list(view.sensor_paths);expected='/World/envs/env_0/'+target
 if getattr(view,'sensor_count',None)!=2 or getattr(view,'filter_count',None)!=1:raise ValueError('native singleton sensor/filter count mismatch: '+repr((getattr(view,'sensor_count',None),getattr(view,'filter_count',None))))
 if raw_filters and not isinstance(raw_filters[0],str):
  rows=[list(row) for row in raw_filters]
  if len(rows)!=2 or any(row!=[expected] for row in rows):raise ValueError('native singleton per-body filter target mismatch: '+repr(rows))
  filters=rows[0]
 else:filters=raw_filters
 if len(filters)!=1:raise ValueError('native singleton filter count mismatch')
 if not filters or set(filters)!={expected}:raise ValueError('native singleton filter target mismatch: '+repr(filters))
 root='/World/envs/env_0/'+('LeftArm' if side=='left' else 'RightArm')+'/'
 if len(bodies)!=2 or any(not path.startswith(root) for path in bodies)or {p.rsplit('/',1)[-1]for p in bodies}!={'tip_left','tip_right'}:raise ValueError('native singleton fingertip path mismatch: '+repr(bodies))
 if len(set(bodies))!=2:raise ValueError('duplicate native fingertip paths')
 if [p.rsplit('/',1)[-1] for p in bodies]!=list(sensor.body_names):raise ValueError('native fingertip force row order mismatch: '+repr((bodies,list(sensor.body_names))))
 return dict(native_verified=True,target=target,filter_paths=filters,sensor_paths=bodies,scope='Singleton native filter binding; no multi-column ordering assumption')

class Reader:
 def __init__(self,base,target=None):
  if target is not None and target not in FLAPS:raise ValueError('unsupported singleton closure target')
  self.base=base;self.target=target;self.targets=TARGETS if target is None else (target,);self.selected_readers={}
  self.sensors={s:base.scene[s+'_carton_contacts' if target is None else s+'_closure_'+target+'_contacts']for s in SIDES};self.physics_dt=float(base.sim.get_physics_dt());self.last_clocks=None;self.last_requested=None;self.sample_id=0
  if not np.isfinite(self.physics_dt)or not 0<self.physics_dt<=1/120:raise ValueError('unsupported native sensor timestep')
 def read(self,time,phase='post_step',target=None,_expected_clocks=None):
  if target is not None:
   if self.target is not None:raise ValueError('cannot redirect a singleton contact reader')
   if target not in FLAPS:raise ValueError('unsupported singleton closure target')
   if target not in self.selected_readers:self.selected_readers[target]=Reader(self.base,target=target)
   anchor=self.read(time,phase)
   return self.selected_readers[target].read(time,phase,_expected_clocks=anchor['sensor_clock_s'])
  time=float(time)
  if not np.isfinite(time)or time<0:raise ValueError('invalid force measurement request time')
  result={};clocks={};updates={};tol=max(2e-6,self.physics_dt*.02)
  for side,sensor in self.sensors.items():
   result[side]=summarize(native_array(sensor.data.force_matrix_w),list(sensor.body_names),self.targets)
   if self.target is not None:
    result[side]['target_binding']=verify_singleton_binding(sensor,self.target,side)
    result[side]['individual_filter_column_order_native_verified']=True
   for field,dest in [('_timestamp',clocks),('_timestamp_last_update',updates)]:
    if not hasattr(sensor,field):raise ValueError('native sensor clock contract unavailable: '+field)
    value=np.asarray(native_array(getattr(sensor,field)),float)
    if value.shape!=(1,)or not np.isfinite(value).all()or value[0]<0:raise ValueError('invalid native sensor clock')
    dest[side]=float(value[0])
   if abs(clocks[side]-updates[side])>tol:raise ValueError('native contact buffer was not refreshed to sensor time')
  if abs(clocks['left']-clocks['right'])>tol:raise ValueError('left/right force clocks disagree')
  if _expected_clocks is not None and any(abs(clocks[side]-_expected_clocks[side])>tol for side in SIDES):raise ValueError('selected flap force does not match verified family clock')
  if self.last_clocks is None and _expected_clocks is None and abs(time)>tol:raise ValueError('first force sample requires reset-time or verified family clock anchor')
  if self.last_clocks is not None:
   requested_delta=time-self.last_requested
   if requested_delta<-tol:raise ValueError('force request clock moved backwards')
   deltas=[clocks[s]-self.last_clocks[s]for s in SIDES]
   if any(dt<-tol or abs(dt-requested_delta)>tol for dt in deltas):raise ValueError('stale/reset/unsynchronised native force sample')
   new=all(dt>tol for dt in deltas)
  else:new=True
  if new:self.sample_id+=1
  self.last_clocks=clocks.copy();self.last_requested=time
  return dict(requested_control_time_s=time,selected_target=self.target,native_filter_target_verified=self.target is not None,sensor_clock_s=clocks,sensor_update_time_s=updates,sample_id=self.sample_id,clock_verified=True,native_clock_fields=['_timestamp','_timestamp_last_update'],measurement_phase=phase,force_sample_interval='latest native sensor substep, not control-interval impulse',sides=result)
