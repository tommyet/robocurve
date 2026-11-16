"""Finite-board support solver; all complete geometry remains in315guard.

The normal placement is derived from ALL tiptriangle portions overlapping the
finite board face. Only a real DISTAL triangle patch may certify contact. Thus a
proximal piece inside the finite face cannot be hidden by a distal-only witness.
"""
import json,argparse,time
from pathlib import Path
import numpy as np
from screen_distal_face_push import DistalSearch,clip,ik,READY,BASES,BOARD
class FiniteSearch(DistalSearch):
 def __init__(self):
  super().__init__();p,R=ik.tcp_pose(READY,BASES['left']);self.fulltips=[(n,(tri-p)@R)for n,t in self.g.pieces('left',READY,self.fingers)if n in('tip_left','tip_right')for tri in t]
 def point(self,name,angle,radius,yaw,offset,clearance=0,roll=0):
  tcp,hand,w=super().point(name,angle,radius,yaw,offset,clearance=0,roll=roll);fp,fr=self.pose(name,angle);size=np.asarray(self.parts[name+'_top']['size']);minimum=10.
  for body,tri in self.fulltips:
   poly=(tri@hand.T+tcp-fp)@fr
   for axis,bound,greater in [(0,-size[0]/2,True),(0,size[0]/2,False),(1,-size[1]/2,True),(1,size[1]/2,False)]:poly=clip(poly,axis,bound,greater)
   if len(poly):minimum=min(minimum,float(poly[:,2].min()))
  if minimum==10.:return tcp,hand,dict(w,largest_single_real_triangle_contact_patch_area_m2=0.,finite_support_failure='no_tip_overlap_in_finite_face')
  shift=BOARD/2-minimum;tcp=tcp+fr[:,2]*(shift+clearance);area=0.;align=0.;patch_centre=None
  for body,poly in self.distal:
   if len(poly)<3:continue
   normal=np.cross(poly[1]-poly[0],poly[2]-poly[0]);length=np.linalg.norm(normal)
   if length<1e-12:continue
   agreement=float((hand@(normal/length))@(-fr[:,2]))
   if agreement<.25:continue
   clipped=(poly@hand.T+tcp-fp)@fr
   for axis,bound,greater in [(0,-size[0]/2+.002,True),(0,size[0]/2-.002,False),(1,-size[1]/2+.002,True),(1,size[1]/2-.002,False),(2,BOARD/2-.0002,True),(2,BOARD/2+.0002,False)]:clipped=clip(clipped,axis,bound,greater)
   if len(clipped)>=3:
    xy=clipped[:,:2];value=abs(float(np.sum(xy[:,0]*np.roll(xy[:,1],-1)-xy[:,1]*np.roll(xy[:,0],-1))/2))
    if value>area:area=value;align=agreement;patch_centre=clipped.mean(0)
  w.update(normal_finite_support_correction_m=shift,largest_single_real_triangle_contact_patch_area_m2=area,patch_outward_normal_alignment=align,actual_patch_centre_flap_m=patch_centre.tolist()if patch_centre is not None else None,support_face_edge_margin_m=.002 if area>0 else -1.,scope='ALLtiptriangles clipped toPHYSICAL finiteface determine normalplacement; realDISTALsingletriangle clipped inside2mmmargin and±.2mmslab certifiesnonzeroarea; FULL315guardremainsindependent')
  return tcp,hand,w

def run(out,flaps):
 s=FiniteSearch();results=[];started=time.monotonic()
 for name in flaps:
  closed=[]if name=='east'else['east']if name=='west'else['east','west']if name=='north'else['east','west','north'];width=s.parts[name+'_top']['size'][0];found=False
  families=[(r,sign*(width/2-inset),yaw)for inset in(.005,.002,.010)for r in(.055,.065,.075)for sign in(-1,1)for yaw in(90.,270.)]+[(r,0.,yaw)for r in(.065,.075)for yaw in(0.,180.)]
  for radius,offset,yaw in families:
   if found:break
   for polarity in(0.,180.):
    if found:break
    for arm in('left','right'):
     r=s.candidate(name,arm,radius,yaw,offset,closed,roll=polarity);results.append(r);out.write_text(json.dumps(dict(scope='CPU finite-full-tip support planning only; no native/runtime changes',elapsed_s=time.monotonic()-started,results=results),indent=2)+'\n');print(name,arm,radius,offset,yaw,polarity,r.get('failure','ARC_PASS'),r.get('angle'),flush=True)
     if r.get('success'):found=True;break
 return results
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--flaps',nargs='+',default=['east','west','north','south']);a=p.parse_args();run(a.out,a.flaps)
