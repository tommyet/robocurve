"""Finite real-finger core clearance only; not a roll grasp or payout proof.

Tests whether a single open finger can fit inside the ordinary 76.2mm core
within the 48mm roll-width slab, without adding an axle/fixture. It does not
prove adequate insertion depth or axial retention. Every clipped
triangle vertex is retained. No actor state, joint or contact force is written.
"""
import json
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tasks/pack-and-tape-carton'))
from roll_probe import Geometry,BASES
from model import CORE_RADIUS,TAPE_WIDTH
from yam_arena import ik
from yam_arena.constants import READY


def clip(poly,z,above):
 out=[]
 for a,b in zip(poly,np.roll(poly,-1,axis=0)):
  ia=a[2]>=z if above else a[2]<=z
  ib=b[2]>=z if above else b[2]<=z
  if ia:out.append(a)
  if ia!=ib:out.append(a+(b-a)*((z-a[2])/(b[2]-a[2])))
 return np.asarray(out).reshape(-1,3)


def screen():
 geometry=Geometry(fast_certificates=True)
 q=np.asarray(READY,float);p,R=ik.tcp_pose(q,BASES['left'])
 pieces=[(name,(tri-p)@R)for name,tri in geometry.pieces('left',q,[-.04695]*2)]
 results=[]
 for name in ('tip_left','tip_right'):
  # Finger mesh XY bounding-centre provides a reproducible candidate axis.
  distal=np.concatenate([tri.reshape(-1,3)for n,tri in pieces if n==name])
  centre=(distal[:,:2].min(0)+distal[:,:2].max(0))/2
  for z in (-.005,-.010,-.015,-.020,-.025):
   slab=(z-TAPE_WIDTH/2,z+TAPE_WIDTH/2);own=[];other=[]
   for n,triangles in pieces:
    for tri in triangles:
     poly=clip(clip(tri,slab[0],True),slab[1],False)
     if len(poly):
      radii=np.linalg.norm(poly[:,:2]-centre,axis=1)
      (own if n==name else other).extend(radii.tolist())
   radius=max(own)if own else None
   results.append(dict(finger=name,roll_centre_in_tcp_m=[*map(float,centre),z],roll_axial_slab_m=slab,selected_mesh_max_radius_m=radius,core_radial_clearance_m=None if radius is None else CORE_RADIUS-radius,other_mesh_min_radius_m=min(other)if other else None,selected_section_fits=radius is not None and radius<CORE_RADIUS-.0002,scope='Axial slab clipping only; other finger/carrier radial values do not by themselves prove finite annulus clearance; no IK/table/film/retention validation'))
 return dict(scope=__doc__,core_radius_m=CORE_RADIUS,roll_width_m=TAPE_WIDTH,results=results)

if __name__=='__main__':
 out=Path(__file__).with_name('passive-axle-section.json');out.write_text(json.dumps(screen(),indent=2)+'\n');print(out)
