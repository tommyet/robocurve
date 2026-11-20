"""Robot-only tracking correction; never changes task objects."""
import numpy as np
from scipy.optimize import least_squares
class DemoControl:
 def __init__(self):
  import json
  from pathlib import Path
  self.prefix=np.asarray(json.loads(Path(__file__).with_name('demo-prefix.json').read_text())['actions'],float)
  assert self.prefix.shape==(761,14) and np.isfinite(self.prefix).all()
  self.offset=None;self.grip_offset=None;self.waypoints={};self.retainer=None;frames=json.loads(Path(__file__).with_name('demo-plan.json').read_text())['frames'];self.stages={};self.labels=[]
  for index,f in enumerate(frames,1):
   label=f['stage'];self.labels.append(label)
   if label not in self.stages:self.stages[label]=[index,index]
   self.stages[label][1]=index
 def action(self,k,wanted,m,observed,hands):
  if 160<=k<=700 and set(m.grasp_state)!={'left','right'}:
   raise RuntimeError('Scripted demonstration lost a required grip; stop this diagnostic before further motion.')
  if 700<k<self.stages['release the right edge'][0] and 'right' not in m.grasp_state:raise RuntimeError('Right hand lost the central crossing before the first loop was stacked.')
  if 141<=k<=900:
   # Replay only ordinary robot commands from the earlier intact initial twist.
   # The scene, contacts and deformable objects continue evolving natively.
   replay=self.prefix[k-140].copy()
   for side,i in [('left',6),('right',13)]:
    if side in m.grasp_state and replay[i]<=.13:replay[i]=.06
   return replay
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
   contact_phase=False;approaching=False
   offset=self.offset[side]
   if self.grip_offset is not None:
    weight=float(np.clip((k-100)/20,0,1));offset=(1-weight)*offset+weight*self.grip_offset[side]
   target+=min(1.,k/60)*max(0.,min(1.,(820-k)/120))*offset
   if 100<=k<=140:
    from geometry import GRIP_BODIES
    # Track the actual bound edge while the jaws close; long fingers can
    # displace it during approach. This changes only robot joint targets.
    target=m.p(GRIP_BODIES[0 if side=='left' else 1]).copy()
    if k==140:self.grip_offset[side]=target-ik.tcp_pose(wanted[o:o+6],station.BASES[side])[0]
   label=self.labels[k-1]
   specs=[('left','approach the far loop','fold the far loop onto the centre',0,np.array([.43,.185,.83])),('right','approach the right outer loop','stack the right loop',(12,40),np.array([.50,0,.96])),('left','approach the left outer loop','stack the left loop',(75,96),np.array([.30,0,.96]))]
   for arm,approach,press,indices,nominal in specs:
    enclose=approach.replace('approach','enclose');pinch=approach.replace('approach','pinch')
    if arm!=side or label not in (approach,enclose,pinch,press):continue
    contact_phase=label in (enclose,pinch);approaching=label==approach
    if approach not in self.waypoints:
     from scipy.spatial.transform import Rotation as Rot
     from geometry import N,GRIP_INDICES
     # Choose a raised outer segment from current geometry. Fixed index ranges
     # can select the central crossing after the strip twists.
     avoid=list(GRIP_INDICES)+[int(g['body'].rsplit('_',1)[1]) for g in m.pinch.held.values() if g['body'].startswith('bound_edge_')]
     candidates=[]
     other='right' if side=='left' else 'left'
     for index in range(N):
      if any(min((index-i)%N,(i-index)%N)<=5 for i in avoid):continue
      body=f'bound_edge_{index:03d}';pos=m.p(body)
      if np.linalg.norm(pos-hands[other]['tcp'])<.06:continue
      candidates.append((float(pos[2]),body,pos.copy()))
     candidates.sort(reverse=True,key=lambda item:item[0])
     seed0=np.clip(observed[o:o+6],ik.LOWER+1e-6,ik.UPPER-1e-6);selection=None
     for height,body,pos in candidates[:16]:
      tangent=m.orientation(body)[:,2].copy();tangent/=max(np.linalg.norm(tangent),1e-12)
      z0=np.array([0.,0.,-1.]);z0-=tangent*float(z0@tangent)
      if np.linalg.norm(z0)<1e-5:continue
      z0/=np.linalg.norm(z0);choices=[]
      for sign in [-1.,1.]:
       y=sign*tangent
       for angle in [-60.,-30.,0.,30.,60.]:
        z=Rot.from_rotvec(tangent*np.deg2rad(angle)).apply(z0);candidate=np.column_stack([np.cross(y,z),y,z]);goal=pos+.010*z
        def loss(q):
         pp,rr=ik.tcp_pose(q,station.BASES[side]);return np.r_[pp-goal,.10*ik._rot_error(candidate,rr)]
        sol=least_squares(loss,seed0,bounds=(ik.LOWER,ik.UPPER),max_nfev=100)
        choices.append((float(np.linalg.norm(sol.fun)),candidate))
      error,chosen=min(choices,key=lambda a:a[0])
      if error<.005:selection=(body,pos,chosen);break
     if selection is None:raise RuntimeError('No raised outer-loop segment has a reachable transverse grasp.')
     body,pos,chosen=selection
     self.waypoints[approach]=dict(body=body,point=pos.copy(),rotation=chosen,start_tcp=hands[side]['tcp'].copy(),start_rotation=hands[side]['rotation'].copy())
     m.events.append(dict(event='demo_outer_loop_target',side=side,body=body,time=m.time,point=pos.tolist()))
    entry=self.waypoints[approach];body=entry['body'];pos=m.p(body);chosen=entry['rotation']
    if label in (approach,enclose,pinch) and side not in m.pinch.held:
     tangent=m.orientation(body)[:,2].copy()
     if tangent@chosen[:,1]<0:tangent=-tangent
     tangent/=max(np.linalg.norm(tangent),1e-12);z=chosen[:,2]-tangent*float(chosen[:,2]@tangent)
     if np.linalg.norm(z)>.2:
      z/=np.linalg.norm(z);chosen=np.column_stack([np.cross(tangent,z),tangent,z]);entry['rotation']=chosen
    lo,hi=self.stages[label];u=ik.smoothstep((k-lo+1)/(hi-lo+1))
    if label==approach:
     target=(1-u)*entry['start_tcp']+u*(pos-.06*chosen[:,2]);R=ik.slerp_matrix(entry['start_rotation'],chosen,u)
    elif label==enclose:target=pos-.06*(1-u)*chosen[:,2]+.010*u*chosen[:,2];R=chosen
    elif label==pinch:target=pos+.010*chosen[:,2];R=chosen
    elif label==press:
     if side not in m.pinch.held:raise RuntimeError('The outer loop was not grasped; stop before stacking.')
     held=m.pinch.held[side]['body']
     selected_index=int(body.rsplit('_',1)[1]);held_index=int(held.rsplit('_',1)[1])
     from geometry import N
     if not held.startswith('bound_edge_') or min((selected_index-held_index)%N,(held_index-selected_index)%N)>2:
      raise RuntimeError('A different edge was captured; stop before stacking the wrong loop.')
     if 'stack_start' not in entry:entry['stack_start']=hands[side]['tcp'].copy();entry['stack_R']=hands[side]['rotation'].copy()
     target=(1-u)*entry['stack_start']+u*target;R=ik.slerp_matrix(entry['stack_R'],R,u)
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
   if side in m.pinch.held:
    # Re-centre the real closing faces around a rolling bound edge. This
    # bounded robot-only correction preserves contact during compliant twist.
    g=m.pinch.held[side];H=hands[side]
    local=(m.p(g['body'])-H['tcp'])@H['rotation']
    finger_q=np.asarray(H['finger_joint_positions']);face_centre=(finger_q[0]-finger_q[1])/2
    shift=float(np.clip(.7*(local[0]-face_centre),-.004,.004))
    target+=H['rotation'][:,0]*shift
   seed=np.clip(observed[o:o+6],ik.LOWER+1e-6,ik.UPPER-1e-6)
   p0,R0=ik.tcp_pose(seed,station.BASES[side]);bias=hands[side]['tcp']-p0;rbias=hands[side]['rotation']@R0.T
   def residual(q):
    pp,rr=ik.tcp_pose(q,station.BASES[side]);grasping=contact_phase;weight=20. if grasping else 3. if approaching else 1.
    return np.r_[weight*(pp+bias-target),(.02 if grasping else .10)*ik._rot_error(R,rbias@rr),.001*(q-seed)]
   out[o:o+6]=least_squares(residual,seed,bounds=(np.maximum(ik.LOWER,seed-.12),np.minimum(ik.UPPER,seed+.12)),max_nfev=25).x
  for side,i in [('left',6),('right',13)]:
   if side in m.grasp_state and out[i]<=.13:out[i]=.06
  return out
