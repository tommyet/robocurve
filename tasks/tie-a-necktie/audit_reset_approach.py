"""Reject unintended cloth contact before the intended physical pinch.

All commanded approach hulls are checked against the measured untied reset
with1mm inflation. This is a sampled rejection screen, not contact proof.
No simulator state is changed.
"""
import numpy as np

def screen(plan,nodes,faces,steps=range(1,81),side='right'):
 from yam_arena.analysis import link_hulls,fk_link_poses_world
 from yam_arena import station
 from yam_arena.constants import ARM_JOINTS,FINGER_OPEN
 from audit_robot_contact import clipped_triangle
 hulls=link_hulls();tri=nodes[faces];low=tri.min(1);high=tri.max(1);out=[]
 for i,f in enumerate(plan['frames']):
  if steps is not None and i+1 not in steps:continue
  offset=0 if side=='left' else 7
  a=np.array(f['action14'])[offset:offset+7];q=dict(zip(ARM_JOINTS,a[:6]));q.update(joint7=a[6]*FINGER_OPEN,joint8=a[6]*FINGER_OPEN);ps=fk_link_poses_world(q,station.BASES[side]);hits=[]
  for name,hs in hulls.items():
   R=ps[name][:3,:3];t=ps[name][:3,3]
   for j,h in enumerate(hs):
    w=h.vertices@R.T+t;ids=np.flatnonzero(np.all(high>=w.min(0)-.001,1)&np.all(low<=w.max(0)+.001,1));local=(tri[ids]-t)@R
    touched=[int(ix) for ix,v in zip(ids,local) if clipped_triangle(v,h.planes,-.001)]
    if touched:hits.append(dict(link=name,hull=j,faces=touched))
  if hits:out.append(dict(step=i+1,stage=f['stage'],hits=hits))
 return out
