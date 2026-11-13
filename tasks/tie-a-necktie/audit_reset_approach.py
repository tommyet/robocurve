"""Reject unintended cloth contact before the intended physical pinch.

All commanded approach hulls are checked against the measured untied reset
with an explicit shell or proximity inflation. This is a sampled rejection
screen, not contact proof.
No simulator state is changed.
"""
import numpy as np

def screen(plan,nodes,faces,steps=range(1,81),side='right',inflation=.001):
 from yam_arena.analysis import link_hulls,fk_link_poses_world
 from yam_arena import station
 from yam_arena.constants import ARM_JOINTS,FINGER_OPEN
 from audit_robot_contact import clipped_triangles
 if not 0.<=inflation<=.002:raise ValueError('Unexpected approach inflation')
 hulls=link_hulls();tri=nodes[faces];low=tri.min(1);high=tri.max(1);out=[]
 for i,f in enumerate(plan['frames']):
  if steps is not None and i+1 not in steps:continue
  offset=0 if side=='left' else 7
  a=np.array(f['action14'])[offset:offset+7];q=dict(zip(ARM_JOINTS,a[:6]));q.update(joint7=a[6]*FINGER_OPEN,joint8=a[6]*FINGER_OPEN);ps=fk_link_poses_world(q,station.BASES[side]);hits=[]
  for name,hs in hulls.items():
   R=ps[name][:3,:3];t=ps[name][:3,3]
   for j,h in enumerate(hs):
    w=h.vertices@R.T+t;ids=np.flatnonzero(np.all(high>=w.min(0)-inflation,1)&np.all(low<=w.max(0)+inflation,1));local=(tri[ids]-t)@R
    touched=ids[clipped_triangles(local,h.planes,-inflation)].astype(int).tolist()
    if touched:hits.append(dict(link=name,hull=j,faces=touched))
  if hits:out.append(dict(step=i+1,stage=f['stage'],hits=hits))
 return out
