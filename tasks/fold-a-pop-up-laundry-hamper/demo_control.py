"""Robot-only tracking correction; never changes task objects."""
import numpy as np
from scipy.optimize import least_squares
class DemoControl:
 def __init__(self):
  import json
  from pathlib import Path
  self.offset=None;self.waypoints={};frames=json.loads(Path(__file__).with_name('demo-plan.json').read_text())['frames'];self.stages={};self.labels=[]
  for index,f in enumerate(frames,1):
   label=f['stage'];self.labels.append(label)
   if label not in self.stages:self.stages[label]=[index,index]
   self.stages[label][1]=index
 def action(self,k,wanted,m,observed,hands):
  from yam_arena import ik,station
  if self.offset is None:
    from geometry import FRAME_POINTS,GRIP_INDICES
    self.offset={s:m.nodes['frame'][i]-FRAME_POINTS[i] for s,i in zip(['left','right'],GRIP_INDICES)}
  out=wanted.copy()
  for side,o in [('left',0),('right',7)]:
   target,R=ik.tcp_pose(wanted[o:o+6],station.BASES[side])
   target+=min(1.,k/60)*max(0.,min(1.,(740-k)/40))*self.offset[side]
   label=self.labels[k-1]
   specs=[('left','approach the far loop','fold the far loop onto the centre',0,np.array([.33,.185,.83])),('right','approach the right outer loop','stack the right loop',(60,90),np.array([.40,0,.96])),('left','approach the left outer loop','stack the left loop',(12,40),np.array([.20,0,.96]))]
   for arm,approach,press,indices,nominal in specs:
    if arm!=side or label not in (approach,press):continue
    if approach not in self.waypoints:
     points=m.nodes['frame']
     index=indices if isinstance(indices,int) else indices[0]+int(np.argmax(points[indices[0]:indices[1],2]))
     self.waypoints[approach]=points[index]-nominal
    lo,hi=self.stages[label];u=ik.smoothstep((k-lo+1)/(hi-lo+1));target+=(u if label==approach else 1-u)*self.waypoints[approach]
   seed=np.clip(observed[o:o+6],ik.LOWER+1e-6,ik.UPPER-1e-6)
   p0,R0=ik.tcp_pose(seed,station.BASES[side]);bias=hands[side]['tcp']-p0;rbias=hands[side]['rotation']@R0.T
   def residual(q):
    pp,rr=ik.tcp_pose(q,station.BASES[side]);return np.r_[pp+bias-target,.10*ik._rot_error(R,rbias@rr),.001*(q-seed)]
   out[o:o+6]=least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=25).x
  return out
