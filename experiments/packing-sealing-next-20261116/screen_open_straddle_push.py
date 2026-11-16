"""OPEN20mm straddling-rim inner-pad push; full315 remains unchanged.

Only the selected finger's real inner pad is the contact witness. Opposite
finger is not forced onto the same halfspace; it stays in the independent full
finite-board collision guard, like every proximal carrier piece.
"""
import json,argparse,time
from pathlib import Path
import numpy as np
from screen_distal_face_push import DistalSearch,clip,ik,READY,BASES
class OpenStraddleSearch(DistalSearch):
 def __init__(self):
  super().__init__();self.fingers=[-.010]*2;self.distal=[];p,R=ik.tcp_pose(READY,BASES['left'])
  for n,t in self.g.pieces('left',READY,self.fingers):
   if n not in('tip_left','tip_right'):continue
   for tri in(t-p)@R:
    poly=clip(tri,2,-.015,True)
    if len(poly):self.distal.append((n,poly))
 def adjust_hand(self,hand,angle):
  t=np.radians(getattr(self,'rock_deg',0.)*np.cos(np.radians(angle)));c,s=np.cos(t),np.sin(t);return hand@np.array([[c,0,s],[0,1,0],[-s,0,c]])
 def point(self,name,angle,radius,yaw,offset,clearance=0,roll=0):
  # handX=+flapZ forroll0 =>push=-handX =>RIGHTinnerpad;
  # handX=-flapZ forroll180 =>push=+handX =>LEFTinnerpad.
  chosen='tip_right'if roll==0 else'tip_left';all_distal=self.distal;self.distal=[(n,p)for n,p in all_distal if n==chosen]
  try:p,R,w=super().point(name,angle,radius,yaw,offset,clearance,roll)
  finally:self.distal=all_distal
  w.update(selected_inner_pad=chosen,physical_jaw_opening_m=.020,scope='One real openfinger INNERpad distaltriangle witness; opposingfinger remains fullyguarded on oppositeboard side, not removed or constrained to same plane')
  return p,R,w

def run(out,flaps):
 s=OpenStraddleSearch();results=[];started=time.monotonic()
 for name in flaps:
  closed=[]if name=='east'else['east']if name=='west'else['east','west']if name=='north'else['east','west','north'];width=s.parts[name+'_top']['size'][0];found=False
  families=[(r,sign*(width/2-inset),yaw)for inset in(.014,.010,.020)for r in(.055,.065,.075,.045)for sign in(-1,1)for yaw in(90.,270.)]
  for radius,offset,yaw in families:
   if found:break
   for polarity in(180.,0.):
    if found:break
    for arm in('left','right'):
     r=s.candidate(name,arm,radius,yaw,offset,closed,roll=polarity);results.append(r);out.write_text(json.dumps(dict(scope='CPU open20mm straddling innerpad push; no native/runtime changes',elapsed_s=time.monotonic()-started,results=results),indent=2)+'\n');print(name,arm,radius,offset,yaw,polarity,r.get('failure','ARC_PASS'),r.get('angle'),flush=True)
     if r.get('success'):found=True;break
 return results
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--flaps',nargs='+',default=['east','west','north','south']);a=p.parse_args();run(a.out,a.flaps)
