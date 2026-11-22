"""Measured TCP and initial visor pose feedback; no object pose writes."""
import json,numpy as np
from pathlib import Path
from scipy.optimize import least_squares
from geometry import Rotation,OPEN,STARTS,NEW
from common import down
class DemoControl:
 def __init__(self):self.frames=json.loads(Path(__file__).with_name('demo-plan.json').read_text())['frames'];self.grip=None
 def action(self,k,wanted,m,observed,hands):
  from yam_arena import ik,station
  phase=self.frames[k-1]['stage'];out=wanted.copy()
  for side,o in [('left',0),('right',7)]:
   target,R=ik.tcp_pose(wanted[o:o+6],station.BASES[side]);h=hands[side]
   tag=None
   if side=='right' and phase in ['align spare','grip spare']:tag='new';point=np.array([.157,0,.030]);tilt=40
   if tag:
    Q=m.orientation(tag+'_visor');actual=m.p(tag+'_visor')+Q@point
    nominalQ=OPEN if tag=='old' else np.eye(3)
    nominalP=STARTS['old'] if tag=='old' else NEW
    # Preserve the authored approach interpolation: only correct reset drift.
    # Jumping straight to the final grasp at the first align step would strike it.
    target+=actual-(nominalP+nominalQ@point)
    R=Q@nominalQ.T@R
   if side=='right':
    point=np.array([.157,0,.030]);gripR=down(0)@Rotation.from_euler('x',20,degrees=True).as_matrix()
    if phase=='grip spare':
     Q=m.orientation('new_visor');self.grip=(Q.T@(h['tcp']-m.p('new_visor')),Q.T@h['rotation'])
    elif self.grip is not None and phase not in ['release spare','clear','open hands','settle']:
     desiredQ=R@gripR.T;origin=target-desiredQ@point
     target=origin+desiredQ@self.grip[0];R=desiredQ@self.grip[1]
   seed=np.clip(observed[o:o+6],ik.LOWER+1e-6,ik.UPPER-1e-6);p0,R0=ik.tcp_pose(seed,station.BASES[side]);bias=h['tcp']-p0;rbias=h['rotation']@R0.T
   def f(q):
    p,r=ik.tcp_pose(q,station.BASES[side]);return np.r_[p+bias-target,.15*ik._rot_error(R,rbias@r),.001*(q-seed)]
   out[o:o+6]=least_squares(f,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=25).x
  return out
