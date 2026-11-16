"""Quiet restored postcut start and an explicitly reviewed diagnostic-route factory."""
import hashlib,json
from pathlib import Path
import numpy as np
from capture import array

CONTROLLERS={}

def load_route(path,snapshot_path):
 if path is None:return None
 route=json.loads(Path(path).read_text(),parse_constant=lambda value:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
 json.dumps(route,allow_nan=False)
 if route.get('reviewed') is not True:raise ValueError('opening route requires explicit review')
 if route.get('snapshot_sha256')!=hashlib.sha256(Path(snapshot_path).read_bytes()).hexdigest():raise ValueError('route snapshot hash mismatch')
 if route.get('active_hand') not in ('left','right'):raise ValueError('explicit active hand required')
 if route.get('prepare_aperture_m') not in (None,.006):raise ValueError('only reviewed6mm preparation aperture supported')
 if not isinstance(route.get('controller'),str) or not route['controller']:raise ValueError('explicit reviewed controller required')
 if not isinstance(route.get('phases'),list) or not route['phases']:raise ValueError('explicit reviewed phases required')
 return route

def controller_factory(route,env,snapshot):
 if route is None:return None
 if route['controller'] not in CONTROLLERS:raise ValueError('no reviewed opening controller registered: '+route['controller'])
 return CONTROLLERS[route['controller']](env,snapshot,route)

def contact_sensor_specs(active_hand,link_paths,panel_names):
 if active_hand not in ('left','right') or len(set(panel_names))!=12:raise ValueError('one actual hand and twelve unique panels required')
 prefix='{ENV_REGEX_NS}/'+('LeftArm' if active_hand=='left' else 'RightArm')
 return {name:dict(prim_path=prefix+link_paths[name],filter_prim_paths_expr=['{ENV_REGEX_NS}/'+n for n in panel_names])for name in ('gripper','tip_left','tip_right')}

class OpeningCoupon:
 """Only ordinary last-command holding until native quiet state is established."""
 def __init__(self,env,snapshot,route=None):
  self.env=env;self.snapshot=snapshot;self.previous=np.array(snapshot['held_action_14d'],dtype=float);self.route=route
  self.controller=controller_factory(route,env,snapshot);self.failure=None;self.done=False;self.safe_start_passed=False;self.quiet=0;self.events=[];self.started=None;self.controller_started=False
 def observe(self,*,time,crease_separation,velocities,first_step_translation=0.,first_step_rotation=0.):
  values=np.array(list(velocities.values()),dtype=float)
  if values.shape!=(13,6) or not np.isfinite(values).all():self.failure='missing/nonfinite native object COM velocities';return
  if not np.isfinite(crease_separation) or crease_separation>.004:self.failure='restored crease separation exceeds4mm'
  if first_step_translation>.005 or first_step_rotation>np.radians(5):self.failure='restored first-step panel pose jump'
  maxv=float(np.linalg.norm(values[:,:3],axis=1).max());maxw=float(np.linalg.norm(values[:,3:],axis=1).max())
  self.quiet=self.quiet+1 if maxv<.01 and maxw<.05 and not self.failure else 0
  if not self.safe_start_passed and time>=2. and self.quiet>=5:
   self.safe_start_passed=True;self.started=time;self.events.append(dict(event='quiet_postcut_start_passed',time_s=time,max_native_linear_speed_m_s=maxv,max_native_angular_speed_rad_s=maxw))
  if time>=5. and not self.safe_start_passed and not self.failure:self.failure='restored postcut bodies did not settle quietly'
 def command(self,time):
  if self.failure or not self.safe_start_passed or self.controller is None:
   if not self.failure and self.route and self.route.get('prepare_aperture_m')==.006:
    from yam_arena.constants import FINGER_OPEN
    i=6 if self.route['active_hand']=='left' else 13
    initial=self.snapshot['held_action_14d'][i];f=min(1.,max(0.,time)/2.);f=f*f*(3-2*f)
    goal=initial+f*((.006/(2*abs(FINGER_OPEN)))-initial)
    self.previous[i]=float(np.clip(goal,self.previous[i]-.05,self.previous[i]+.05))
   return self.previous.copy(),[dict(phase='postcut_safe_hold',safe_start_passed=self.safe_start_passed,quiet_frames=self.quiet,failure=self.failure)]
  if not self.controller_started:
   if hasattr(self.controller,'begin'):self.controller.begin(self.previous.copy())
   self.controller_started=True
  action,report=self.controller.command(time-self.started)
  action=np.asarray(action,dtype=float)
  if action.shape!=(14,) or not np.isfinite(action).all() or np.any(action<self.env._low) or np.any(action>self.env._high):self.failure='invalid reviewed ordinary action';return self.previous.copy(),[dict(phase='failed',failure=self.failure)]
  if np.any(abs(action-self.previous)>np.array([.04]*6+[.05]+[.04]*6+[.05])+1e-12):self.failure='reviewed action exceeded existing joint slew bounds';return self.previous.copy(),[dict(phase='failed',failure=self.failure)]
  idle=slice(7,14)if self.route['active_hand']=='left' else slice(0,7)
  if not np.array_equal(action[idle],np.array(self.snapshot['held_action_14d'])[idle]):self.failure='reviewed route changed idle-arm command';return self.previous.copy(),[dict(phase='failed',failure=self.failure)]
  self.previous=action.copy();self.failure=self.controller.failure;self.done=self.controller.done
  return self.previous.copy(),report

# Diagnostic-only controller: registration does not authorize a native trial.
from scoop_controller import OuterNorthScoop
CONTROLLERS['north_outer_scoop']=OuterNorthScoop
