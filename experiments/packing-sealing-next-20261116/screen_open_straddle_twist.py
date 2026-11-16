"""Continuous tangent-plane wrist yaw; same real innerpad/contactface throughout."""
import json,time,argparse
from pathlib import Path
from screen_open_straddle_push import OpenStraddleSearch,ik
class TwistSearch(OpenStraddleSearch):
 def __init__(self,start,end,finish):super().__init__();self.start=start;self.end=end;self.finish=finish
 def point(self,name,angle,radius,yaw,offset,clearance=0,roll=0):
  blend=ik.smoothstep((angle-self.start)/(self.end-self.start));initial=yaw if yaw<=180 else yaw-360;finish=self.finish;effective=initial+(finish-initial)*blend;p,R,w=super().point(name,angle,radius,effective,offset,clearance,roll);w.update(tool_tangent_yaw_deg=effective,yaw_blend=blend);return p,R,w

def run(out):
 results=[];started=time.monotonic()
 for start,end,finish in[(-140.,-70.,0.),(-130.,-60.,0.),(-120.,-50.,0.),(-150.,-80.,0.),(-140.,-70.,180.)]:
  s=TwistSearch(start,end,finish)
  for r in(.075,.065,.055,.045):
   for offset in(-.073,-.077,-.067,-.050):
    for arm,yaw,roll,actualoffset in [('left',90.,180.,offset),('right',270.,0.,-offset)]:
     item=s.candidate('east',arm,r,yaw,actualoffset,[],roll=roll);item.update(twist_start_deg=start,twist_end_deg=end,finish_tangent_yaw_deg=finish);results.append(item);out.write_text(json.dumps(dict(scope='CPU continuous innerpad yaw route ONLY; no native/runtime change',elapsed_s=time.monotonic()-started,results=results),indent=2)+'\n');print(arm,r,actualoffset,start,end,finish,item.get('failure','ARC_PASS'),item.get('angle'),flush=True)
     if item.get('success'):return results
 return results
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.out)
