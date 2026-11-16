"""Finite distal-tip broad-face search: all other geometry remains guarded.

Clipping below constructs a contact WITNESS only, never removes robot triangles
from collision tests. Objects are hypothetical CPU planning poses, not actorwrites.
"""
import sys,json,argparse,time,copy
from pathlib import Path
import numpy as np
from screen_face_push import Search,F,ROOT,ik,BASES,READY,BOARD,rotation

def clip(poly,axis,bound,keep_greater):
 out=[]
 if not len(poly):return np.empty((0,3))
 a=poly[-1];va=(a[axis]-bound)*(1 if keep_greater else -1)
 for b in poly:
  vb=(b[axis]-bound)*(1 if keep_greater else -1)
  if (va>=0)!=(vb>=0):out.append(a+(b-a)*va/(va-vb))
  if vb>=0:out.append(b)
  a,va=b,vb
 return np.asarray(out).reshape(-1,3)

class DistalSearch(Search):
 def __init__(self):
  super().__init__();self.distal=[];p,R=ik.tcp_pose(READY,BASES['left'])
  for n,t in self.g.pieces('left',READY,self.fingers):
   if n not in('tip_left','tip_right'):continue
   for tri in(t-p)@R:
    clipped=clip(tri,2,-.015,True)
    if len(clipped):self.distal.append((n,clipped))
 def adjust_hand(self,hand,angle):return hand
 def point(self,name,angle,radius,yaw,tilt,clearance=0,roll=0):
  # yaw selects radial(+/-Y) or hinge-parallel(+/-X) approach; roll polarity
  # selects which actual distal finger face presses. No fictitiousTCPoffset.
  fp,fr=self.pose(name,angle);z=fr[:,1]*np.cos(np.radians(yaw))+fr[:,0]*np.sin(np.radians(yaw));x=fr[:,2]*(1 if roll==0 else -1);y=np.cross(z,x);hand=self.adjust_hand(np.column_stack((x,y,z)),angle);push=-fr[:,2];maximum=max(float((v@hand.T@push).max())for _,v in self.distal);support=[]
  for n,v in self.distal:
   proj=v@hand.T@push
   for vv in v[proj>=maximum-1e-7]:support.append((n,vv))
  witness=np.mean([v for _,v in support],axis=0);h=self.hinges[name];local=np.array([tilt,h['anchor_b'][1]-radius,BOARD/2]);surface=fp+fr@local;tcp=surface-hand@witness-push*clearance;world=np.array([tcp+hand@v for _,v in support]);onface=(world-fp)@fr;size=np.asarray(self.parts[name+'_top']['size']);margin=float(np.min(size[:2]/2-np.abs(onface[:,:2])))
  patch_area=0.;alignment=0.
  for body,poly in self.distal:
   if len(poly)<3:continue
   normal=np.cross(poly[1]-poly[0],poly[2]-poly[0]);length=np.linalg.norm(normal)
   if length<1e-12:continue
   align=float((hand@(normal/length))@push)
   if align<.25:continue
   localpoly=(poly@hand.T+tcp-fp)@fr
   for axis,bound,greater in [(0,-size[0]/2+.002,True),(0,size[0]/2-.002,False),(1,-size[1]/2+.002,True),(1,size[1]/2-.002,False),(2,BOARD/2-.0002,True),(2,BOARD/2+.0002,False)]:localpoly=clip(localpoly,axis,bound,greater)
   if len(localpoly)>=3:
    xy=localpoly[:,:2];area=abs(float(np.sum(xy[:,0]*np.roll(xy[:,1],-1)-xy[:,1]*np.roll(xy[:,0],-1))/2))
    if area>patch_area:patch_area=area;alignment=align
  return tcp,hand,dict(contact_face_local=local.tolist(),push_world=push.tolist(),distal_clip_z_min_m=-.015,largest_single_real_triangle_contact_patch_area_m2=patch_area,patch_outward_normal_alignment=alignment,contact_slab_halfwidth_m=.0002,support_projection_m=maximum,support_vertices_count=len(support),support_body_names=sorted(set(n for n,_ in support)),support_face_edge_margin_m=margin,support_face_depth_range_m=[float(onface[:,2].min()-BOARD/2),float(onface[:,2].max()-BOARD/2)],scope='Distal clipped-triangle support witness ONLY; all315 complete meshes still checked')
 def candidate(self,name,arm,radius,yaw,offset,closed,roll=0):
  rec=dict(flap=name,arm=arm,radius_m=radius,approach_yaw_deg=yaw,lateral_offset_m=offset,polarity=roll,closed_prior=closed);side=0 if arm=='left' else 1;qs=[np.array(READY,float),np.array(READY,float)];fs=[[-.04695]*2,[-.04695]*2];fs[side]=self.fingers;p,R,w=self.point(name,-175,radius,yaw,offset,roll=roll)
  if w['support_face_edge_margin_m']<.002 or w['largest_single_real_triangle_contact_patch_area_m2']<1e-6:return dict(rec,failure='finite_distal_witness_margin',witness=w)
  seeds=[np.asarray(READY,float),np.asarray(F['prestate']['hands'][0]['joints']),np.asarray(F['prestate']['hands'][1]['joints']),np.array([-.8,2.3,1.3,.8,1.2,-1.4]),np.array([.8,2.3,1.3,.8,-1.2,1.4]),np.array([1.1443,1.6067,.0491,-1.4312,-1.1458,1.5986]),np.array([1.1443,1.6067,.0491,-1.4312,1.1458,1.5986]),np.array([-1.1443,1.6067,.0491,-1.4312,1.1458,-1.5986])];initial=[];branches=[]
  for seed in seeds:
   q,pe,re=ik.solve(p,ik.matrix_to_quat_xyzw(R),seed,base_pos=BASES[arm],iters=160,tol=1e-6)
   item=dict(position_error_m=pe,rotation_error_rad=re,q=q.tolist())
   if pe<=.0003 and re<=.003:
    qs[side]=q;g=self.g.check(qs,fs,self.poses_at(name,-175,closed),True,contact_targets={name+'_top'},contact_side=side);item['guard']=g
    if g['safe']:initial.append((q,g))
   else:item['ik_rejected']=True
   branches.append(item)
   if initial:break
  if not initial:return dict(rec,failure='all_initial_seed_branches_rejected',seed_branches=branches,witness=w)
  q=initial[0][0];points=[];minimum=[10,None]
  end_angle=getattr(self,'end_angle',0.);arc=list(np.arange(-175.,end_angle+.001,5.));arc.append(end_angle)
  for angle in sorted(set(arc+[-160.])):
   p,R,w=self.point(name,angle,radius,yaw,offset,roll=roll)
   if w['support_face_edge_margin_m']<.002 or w['largest_single_real_triangle_contact_patch_area_m2']<1e-6:return dict(rec,failure='finite_distal_witness_margin',angle=angle,witness=w)
   q,pe,re=ik.solve(p,ik.matrix_to_quat_xyzw(R),q,base_pos=BASES[arm],iters=160,tol=1e-6)
   if pe>.0003 or re>.003:return dict(rec,failure='continuous_arc_IK',angle=angle,position_error_m=pe,rotation_error_rad=re)
   qs[side]=q;g=self.g.check(qs,fs,self.poses_at(name,angle,closed),True,contact_targets={name+'_top'},contact_side=side)
   if not g['safe']:return dict(rec,failure='continuous_arc_full315_guard',angle=angle,guard=g,witness=w)
   if g['hard_gap_m']<minimum[0]:minimum=[g['hard_gap_m'],angle,g['hard_pair']]
   points.append(dict(angle_deg=angle,q=q.tolist(),witness=w,guard=g))
  return dict(rec,success=True,scope='Contactarc only; ready/hover/enter/retract pending; hypothetical CPUgeometry only',minimum_hard_gap=minimum,points=points)

def run(out,flaps):
 s=DistalSearch();results=[];started=time.monotonic()
 for name in flaps:
  closed=[]if name=='east'else['east']if name=='west'else['east','west']if name=='north'else['east','west','north'];arms=['left','right']if name in('east','west')else['left','right'];found=False;width=s.parts[name+'_top']['size'][0]
  families=[(r,0.,yaw)for r in(.065,.075)for yaw in(0.,180.)]+[(r,sign*(width/2-.010),yaw)for r in(.055,.065)for sign in(-1,1)for yaw in(90.,270.)]
  for radius,offset,yaw in families:
   if found:break
   for polarity in(0.,180.):
    if found:break
    for arm in arms:
     r=s.candidate(name,arm,radius,yaw,offset,closed,roll=polarity);results.append(r);out.write_text(json.dumps(dict(scope='CPU distalfinitepatch planning; no native/physics/sourcechange',elapsed_s=time.monotonic()-started,results=results),indent=2)+'\n');print(name,arm,radius,offset,yaw,polarity,r.get('failure','ARC_PASS'),r.get('angle'),flush=True)
     if r.get('success'):found=True;break
 return results
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--flaps',nargs='+',default=['east','west','north','south']);a=p.parse_args();run(a.out,a.flaps)
