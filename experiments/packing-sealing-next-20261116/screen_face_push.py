"""Finite CPU ordinary broad-face push search; NO native/contact-force claim.

Object poses below are hypothetical geometry for planning only. Never applied to
native actors. All315 pieces, otherarm, products/tape/cutter and finite flaps stay
in every guard. Same+flapZ face throughout, no handles/grasp attachments.
"""
import sys,json,argparse,time,copy
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tasks/pack-and-tape-carton'))
from yam_arena import ik
from yam_arena.constants import READY
from yam_arena.urdf import quat_xyzw_to_matrix
from carton_scene import layout
from roll_probe import Geometry,BASES
from closure_geometry import rx
from config import BOARD
F=json.loads(Path(__file__).with_name('closure002-fixture-report.json').read_text())

def rotation(axis,deg):
 t=np.radians(deg);c,s=np.cos(t),np.sin(t)
 return np.array([[1,0,0],[0,c,-s],[0,s,c]])if axis==0 else np.array([[c,-s,0],[s,c,0],[0,0,1]])

class Search:
 def __init__(self):
  self.g=Geometry(fast_certificates=True);self.poses={n:(np.asarray(v[:3]),quat_xyzw_to_matrix(np.asarray(v[3:])))for n,v in F['prestate']['poses'].items()};parts,hinges=layout();self.parts={p['name']:p for p in parts};self.hinges={h['a']:h for h in hinges if h['b'].endswith('_top')};self.fingers=[-.00075]*2;self.pad=[]
  p,R=ik.tcp_pose(READY,BASES['left'])
  for n,t in self.g.pieces('left',READY,self.fingers):
   if n in('tip_left','tip_right'):self.pad.append((n,(t.reshape(-1,3)-p)@R))
 def pose(self,name,angle):
  wp,wr=self.poses[name];h=self.hinges[name];fr=wr@rx(angle);hp=wp+wr@np.asarray(h['anchor_a']);return hp-fr@np.asarray(h['anchor_b']),fr
 def point(self,name,angle,radius,yaw,tilt,clearance=0,roll=0):
  fp,fr=self.pose(name,angle);hand=np.column_stack((fr[:,0],-fr[:,1],-fr[:,2]))@rotation(2,yaw)@rotation(0,tilt)@rotation(2,roll);push=-fr[:,2];local=np.array([0.,self.hinges[name]['anchor_b'][1]-radius,BOARD/2]);surface=fp+fr@local
  # All tipcollider vertices participate; support maximizes projection onpush.
  support=[];maximum=max(float((v@hand.T@push).max())for _,v in self.pad)
  for n,v in self.pad:
   proj=v@hand.T@push;selected=v[proj>=maximum-1e-7]
   if len(selected):support.extend([(n,x)for x in selected])
  witness=np.mean([v for _,v in support],axis=0);tcp=surface-hand@witness-push*clearance;world=np.array([tcp+hand@v for _,v in support]);onface=(world-fp)@fr;size=np.asarray(self.parts[name+'_top']['size']);margin=float(np.min(size[:2]/2-np.abs(onface[:,:2])))
  return tcp,hand,dict(contact_face_local=local.tolist(),push_world=push.tolist(),support_projection_m=maximum,support_vertices_count=len(support),support_body_names=sorted(set(n for n,_ in support)),support_face_edge_margin_m=margin,support_face_depth_range_m=[float(onface[:,2].min()-BOARD/2),float(onface[:,2].max()-BOARD/2)])
 def poses_at(self,name,angle,closed):
  poses=copy.deepcopy(self.poses)
  for n in('east','west','north','south'):poses[n+'_top']=self.pose(n,angle if n==name else 0. if n in closed else -175.)
  return poses
 def candidate(self,name,arm,radius,yaw,tilt,closed,roll=0):
  record=dict(flap=name,arm=arm,radius_m=radius,yaw_deg=yaw,tilt_deg=tilt,roll_deg=roll,closed_prior=closed);side=0 if arm=='left' else 1;seed=np.array(READY,float);angles=[-175.,-160.,-135.,-90.,-45.,0.];points=[]
  # Initial witness/guardprune avoids spending denseIK on tableblockedfamily.
  p,R,w=self.point(name,-175,radius,yaw,tilt,roll=roll)
  if w['support_face_edge_margin_m']<.005:return dict(record,failure='finite_contact_patch_edge_margin',witness=w)
  q,pe,re=ik.solve(p,ik.matrix_to_quat_xyzw(R),seed,base_pos=BASES[arm],iters=100,tol=1e-6)
  if pe>.0003 or re>.003:
   native_seed=np.array(F['prestate']['hands'][side]['joints']);aq,ap,ar=ik.solve(p,ik.matrix_to_quat_xyzw(R),native_seed,base_pos=BASES[arm],iters=150,tol=1e-6)
   if ap+.05*ar<pe+.05*re:q,pe,re=aq,ap,ar
  if pe>.0003 or re>.003:return dict(record,failure='initial_IK',position_error_m=pe,rotation_error_rad=re)
  qs=[np.array(READY,float),np.array(READY,float)];qs[side]=q;fs=[[-.04695]*2,[-.04695]*2];fs[side]=self.fingers;g=self.g.check(qs,fs,self.poses_at(name,-175,closed),True,contact_targets={name+'_top'},contact_side=side)
  if not g['safe']:return dict(record,failure='initial_full315_guard',guard=g,witness=w)
  # Continuous denseIK along the entirearc, no isolatedconfiguration stitching.
  seed=q;minimum=[10,None];dense=sorted(set(np.linspace(-175,0,36).tolist()+[-160.]))
  for a in dense:
   p,R,w=self.point(name,a,radius,yaw,tilt,roll=roll)
   if w['support_face_edge_margin_m']<.005:return dict(record,failure='finite_contact_patch_edge_margin',angle=a,witness=w)
   q,pe,re=ik.solve(p,ik.matrix_to_quat_xyzw(R),seed,base_pos=BASES[arm],iters=100,tol=1e-6)
   if pe>.0003 or re>.003:return dict(record,failure='continuous_arc_IK',angle=a,position_error_m=pe,rotation_error_rad=re)
   qs[side]=q;g=self.g.check(qs,fs,self.poses_at(name,a,closed),True,contact_targets={name+'_top'},contact_side=side)
   if not g['safe']:return dict(record,failure='continuous_arc_full315_guard',angle=a,guard=g,witness=w)
   if g['hard_gap_m']<minimum[0]:minimum=[g['hard_gap_m'],a,g['hard_pair']]
   points.append(dict(angle_deg=a,q=q.tolist(),witness=w,guard=g));seed=q
  return dict(record,success=True,scope='Contactarc only; ready/hover/enter/retract notyetvalidated; hypothetical geometry NOTnative execution',minimum_hard_gap=minimum,points=points)

def run(out,flaps):
 s=Search();results=[];started=time.monotonic()
 for name in flaps:
  closed=[]if name=='east'else['east']if name=='west'else['east','west']if name=='north'else['east','west','north'];arms=['left','right']if name in('east','west')else['left']if name=='north'else['right'];found=False
  for tilt in(75.,-75.,90.,-90.):
   if found:break
   for radius in(.055,.045,.065):
    if found:break
    for yaw in(0.,90.,180.,270.):
     if found:break
     for arm in arms:
      for roll in(0.,90.,180.,270.):
       r=s.candidate(name,arm,radius,yaw,tilt,closed,roll=roll);results.append(r)
       if r.get('success'):break
      results.pop();results.append(r);out.write_text(json.dumps(dict(scope='CPU geometric planning only; no source/runtime/physics change',elapsed_s=time.monotonic()-started,results=results),indent=2)+'\n');print(name,arm,radius,yaw,tilt,r.get('failure','ARC_PASS'),r.get('angle'),flush=True)
      if r.get('success'):found=True;break
 return results
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--flaps',nargs='+',default=['east','west','north','south']);a=p.parse_args();run(a.out,a.flaps)
