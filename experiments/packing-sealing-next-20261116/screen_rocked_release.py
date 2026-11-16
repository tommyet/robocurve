"""Modest±3/6deg wristtilt search, actualinnerpad geometry+unchangedfull315."""
import json,argparse,time
from pathlib import Path
from screen_gravity_release import withdrawal
from screen_open_straddle_push import OpenStraddleSearch

def run(out,flaps):
 results=[];started=time.monotonic()
 for name in flaps:
  closed=['east']if name=='west'else['east','west']if name=='north'else['east','west','north'];found=False
  for rock in(3.,-3.,6.,-6.):
   if found:break
   s=OpenStraddleSearch();s.end_angle=-70.;s.rock_deg=rock;width=s.parts[name+'_top']['size'][0]
   for radius in(.075,.065,.055,.045):
    if found:break
    for inset in(.014,.020,.030,.010):
     if found:break
     for arm,yaw,pol,sign in[('left',270.,0.,1),('right',90.,180.,-1),('left',90.,180.,-1),('right',270.,0.,1)]:
      r=s.candidate(name,arm,radius,yaw,sign*(width/2-inset),closed,roll=pol);r.update(rock_deg=rock,release_angle_deg=s.end_angle)
      if r.get('success'):r['withdrawal']=withdrawal(s,r)
      results.append(r);out.write_text(json.dumps(dict(scope='CPU modestwristtilt+openstraddle+gravityrelease, notnativeproof',elapsed_s=time.monotonic()-started,results=results),indent=2)+'\n');print(name,arm,radius,inset,rock,r.get('failure','ARC_PASS'),r.get('angle'),r.get('withdrawal',{}).get('reason',r.get('withdrawal',{}).get('safe')),flush=True)
      if r.get('success')and r['withdrawal']['safe']:found=True;break
 return results
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--flaps',nargs='+',default=['west','north','south']);a=p.parse_args();run(a.out,a.flaps)
