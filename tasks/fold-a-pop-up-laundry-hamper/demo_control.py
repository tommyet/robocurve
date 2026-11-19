"""Robot-only tracking correction; never changes task objects."""
import numpy as np
from scipy.optimize import least_squares
class DemoControl:
 def __init__(self):
  import json
  from pathlib import Path
  self.offset=None;self.grip_offset=None;self.waypoints={};self.retainer=None;frames=json.loads(Path(__file__).with_name('demo-plan.json').read_text())['frames'];self.stages={};self.labels=[]
  for index,f in enumerate(frames,1):
   label=f['stage'];self.labels.append(label)
   if label not in self.stages:self.stages[label]=[index,index]
   self.stages[label][1]=index
 def action(self,k,wanted,m,observed,hands):
  if 160<=k<=700 and set(m.grasp_state)!={'left','right'}:
   raise RuntimeError('Scripted demonstration lost a required grip; stop this diagnostic before further motion.')
  if 700<k<=840 and 'left' not in m.grasp_state:raise RuntimeError('Left hand lost the central crossing before table support.')
  from yam_arena import ik,station
  label=self.labels[k-1]
  if label=='hold the packet beside the retaining path' and k==self.stages[label][0]:
   q=m.measure()
   if max(q['bundle_long_mm'],q['bundle_short_mm'])>220 or q['thickness_mm']>60:
    raise RuntimeError('The packet is not compact; stop before the retaining phase.')
  if self.offset is None:
    from geometry import GRIP_POINTS,GRIP_BODIES
    self.offset={side:m.p(name)-point for side,name,point in zip(['left','right'],GRIP_BODIES,GRIP_POINTS)}
  if k==100:
    from geometry import GRIP_POINTS,GRIP_BODIES
    self.grip_offset={}
    for side,o,name,point in zip(['left','right'],[0,7],GRIP_BODIES,GRIP_POINTS):
     expected,_=ik.tcp_pose(wanted[o:o+6],station.BASES[side])
     self.grip_offset[side]=m.p(name)-expected
  out=wanted.copy()
  for side,o in [('left',0),('right',7)]:
   target,R=ik.tcp_pose(wanted[o:o+6],station.BASES[side])
   offset=self.offset[side]
   if self.grip_offset is not None:
    weight=float(np.clip((k-100)/20,0,1));offset=(1-weight)*offset+weight*self.grip_offset[side]
   target+=min(1.,k/60)*max(0.,min(1.,(820-k)/120))*offset
   label=self.labels[k-1]
   specs=[('left','approach the far loop','fold the far loop onto the centre',0,np.array([.43,.185,.83])),('right','approach the right outer loop','stack the right loop',(60,90),np.array([.50,0,.96])),('left','approach the left outer loop','stack the left loop',(12,40),np.array([.30,0,.96]))]
   for arm,approach,press,indices,nominal in specs:
    if arm!=side or label not in (approach,press):continue
    if approach not in self.waypoints:
     points=m.nodes['frame']
     index=indices if isinstance(indices,int) else indices[0]+int(np.argmax(points[indices[0]:indices[1],2]))
     self.waypoints[approach]=points[index]-nominal
    lo,hi=self.stages[label];u=ik.smoothstep((k-lo+1)/(hi-lo+1));target+=(u if label==approach else 1-u)*self.waypoints[approach]
   if side=='left' and label=='approach the loose retaining loop' and self.retainer is None:
    band=m.nodes['band'];point=band[64];normal=np.cross(band[128]-band[0],band[65]-band[127]);normal/=max(np.linalg.norm(normal),1e-12)
    direction=point-np.asarray(station.BASES['left']);direction-=normal*float(direction@normal);direction/=max(np.linalg.norm(direction),1e-12)
    seed0=np.clip(observed[:6],ik.LOWER+1e-6,ik.UPPER-1e-6);choices=[]
    for sx in [-1.,1.]:
     for sz in [-1.,1.]:
      x=sx*normal;z=sz*direction;candidate=np.column_stack([x,np.cross(z,x),z])
      def loss(q):
       pp,rr=ik.tcp_pose(q,station.BASES['left']);return np.r_[pp-point,.1*ik._rot_error(candidate,rr)]
      sol=least_squares(loss,seed0,bounds=(ik.LOWER,ik.UPPER),max_nfev=150)
      choices.append((float(np.linalg.norm(sol.fun)),candidate))
    error,chosen=min(choices,key=lambda item:item[0])
    if error>.025:raise RuntimeError('The retaining loop is not reachable from this fold.')
    self.retainer=(point.copy(),chosen)
   if side=='left' and self.retainer is not None:
    point,chosen=self.retainer
    if label=='approach the loose retaining loop':
     lo,hi=self.stages[label];u=ik.smoothstep((k-lo+1)/(hi-lo+1));target+=u*(point-np.array([.39,.11,.7475+.055]));R=ik.slerp_matrix(R,chosen,u)
    elif label=='pinch the retaining loop':target=point.copy();R=chosen
    elif label=='lift the retaining loop over the packet':
     lo,hi=self.stages[label];u=ik.smoothstep((k-lo+1)/(hi-lo+1));target+=(1-u)*(point-np.array([.39,.11,.7475+.055]));R=chosen
    elif k>=self.stages['stretch the loop across the packet'][0]:R=chosen
    if self.stages['lift the retaining loop over the packet'][0]<=k<=self.stages['slip the loop below the far edge'][1]:
     if not m.grasp_state.get('left',{}).get('body','').startswith('band_contact_'):raise RuntimeError('The retaining loop is not held; stop the diagnostic.')
   seed=np.clip(observed[o:o+6],ik.LOWER+1e-6,ik.UPPER-1e-6)
   p0,R0=ik.tcp_pose(seed,station.BASES[side]);bias=hands[side]['tcp']-p0;rbias=hands[side]['rotation']@R0.T
   def residual(q):
    pp,rr=ik.tcp_pose(q,station.BASES[side]);return np.r_[pp+bias-target,.10*ik._rot_error(R,rbias@rr),.001*(q-seed)]
   out[o:o+6]=least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=25).x
  return out
