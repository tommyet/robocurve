"""Ordinary robot tracking and measured object-pose compensation."""
import numpy as np
from scipy.optimize import least_squares
class DemoControl:
 def __init__(self):
  import json
  from pathlib import Path
  self.plan=json.loads(Path(__file__).with_name('demo-plan.json').read_text())['frames'];self.offset={s:np.zeros(3) for s in ['left','right']};self.tail_rotation=None
 def action(self,k,wanted,m,observed,hands):
  from yam_arena import ik,station
  from geometry import TAIL,TOOL,C
  from common import down
  from scipy.spatial.transform import Rotation
  GRIP_R=down(0)@Rotation.from_euler("x",50,degrees=True).as_matrix()
  out=wanted.copy();stage=self.plan[k-1]['stage']
  if stage=='lift the scaler' and (not m.tail_pinch.held or not m.tool_pinch.held):raise RuntimeError('Demo pickup failed: tail and scaler must both be held.')
  for side,o in [('left',0),('right',7)]:
   target,R=ik.tcp_pose(wanted[o:o+6],station.BASES[side]);name='tail_grip' if side=='left' else 'scaler';rest=TAIL if side=='left' else TOOL;pinch=m.tail_pinch if side=='left' else m.tool_pinch
   if stage in ['place fingers around tail and handle','grip tail and scaler handle']:
    if stage.startswith('place'):self.offset[side]=m.p(name)-rest
    target+=self.offset[side]
   elif side=='left' and 'release' not in stage and stage!='leave hands clear' and stage!='inspect remaining scales and intact skin':target+=self.offset[side]
   elif side=='right' and ('scraping lane' in stage or stage.startswith('scrape lane')):
    F=m.orientation('fish');target=m.p('fish')+F@(target-C);R=F@R
   if side in pinch.held and stage not in ['release scaler and fish','leave hands clear','inspect remaining scales and intact skin']:
    grip=pinch.held[side]
    if side=='left':
     if self.tail_rotation is None:self.tail_rotation=m.orientation('tail_grip').copy()
     body_R=self.tail_rotation
    else:body_R=R@GRIP_R.T
    R=body_R@grip['local_rotation'].T;target-=R@grip['local_point']
   seed=np.clip(observed[o:o+6],ik.LOWER+1e-6,ik.UPPER-1e-6);p0,R0=ik.tcp_pose(seed,station.BASES[side]);bias=hands[side]['tcp']-p0;rbias=hands[side]['rotation']@R0.T
   def residual(q):
    p,r=ik.tcp_pose(q,station.BASES[side]);return np.r_[p+bias-target,.1*ik._rot_error(R,rbias@r),.001*(q-seed)]
   out[o:o+6]=least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=25).x
  return out
