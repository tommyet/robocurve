"""Read-only fingertip normal forces filtered to the twelve carton panels.

Column ordering is not asserted. Only the sum over the entire named panel
family is interpreted; vectors are forces on the sensor fingertips, not on the
carton. This diagnostic never applies force or gates controller progress.
"""
import numpy as np
TARGETS=('north','east','south','west','north_top','east_top','south_top','west_top','north_bottom','east_bottom','south_bottom','west_bottom')
SIDES=('left','right')
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
 embodiment.scene_config=make_configclass('CartonTurnoverContactCfg',fields)()
def summarize(force,names):
 force=np.asarray(force,float)
 if force.shape!=(1,2,len(TARGETS),3)or len(names)!=2 or set(names)!={'tip_left','tip_right'}:raise ValueError('carton contact shape/body mismatch')
 if not np.isfinite(force).all():raise ValueError('nonfinite carton contact force')
 net=force[0].sum(axis=(0,1))
 return dict(body_names=list(names),configured_target_family=list(TARGETS),individual_filter_column_order_native_verified=False,normal_force_matrix_w=force[0].tolist(),family_normal_force_on_fingertips_w_N=net.tolist(),family_normal_force_norm_N=float(np.linalg.norm(net)),family_sum_of_normal_force_magnitudes_N=float(np.linalg.norm(force[0],axis=-1).sum()))
class Reader:
 def __init__(self,base):self.sensors={s:base.scene[s+'_carton_contacts']for s in SIDES}
 def read(self,time):
  result={}
  for side,sensor in self.sensors.items():
   value=sensor.data.force_matrix_w;value=value.torch if hasattr(value,'torch')else value
   value=value.detach().cpu().numpy()if hasattr(value,'detach')else np.asarray(value)
   result[side]=summarize(value,list(sensor.body_names))
  return dict(requested_control_time_s=float(time),measurement_phase='post_step_sensor_read',force_sample_interval='latest native sensor substep, not control-interval impulse',sides=result)
