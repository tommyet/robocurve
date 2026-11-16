"""Fixed ordinary joint commands. Offline positions never read rope at run time."""
from pathlib import Path
import json,numpy as np
from planner import Plan
from common import down
if __name__=='__main__':
 p=Plan();D=down(-90);G=down(0);a=np.radians(20);c,s=np.cos(a),np.sin(a)
 S=np.array([[1,0,0],[0,c,-s],[0,s,c]])@D
 F=np.array([[1,0,0],[0,-s,-c],[0,c,-s]])
 arch=np.array([.3624,.0479,.7525]);red=np.array([.3217,.1657,.7525])
 def move(side,point,R=D,opening=0.,seconds=2.,label='move'):
  p.add(seconds,label,{side:(np.array(point)-.009*R[:,2],R,opening)})
 p.add(3.,'approach the loose knot',{'left':(np.array([.18,.36,.91]),G,.8),'right':(arch+[0,0,.03],D,.8)},'joint')
 move('right',arch,D,.8,2.,'reach the upper strand beside the crossing')
 move('right',arch,D,0.,1.,'grasp the loop')
 move('right',arch+[0,0,.03],S,0.,2.,'tilt the support wrist clear')
 move('right',arch+[0,0,.15],S,0.,4.,'lift a local arch')
 move('left',red+[0,0,.09],G,.8,2.,'approach the red end')
 move('left',red,G,.8,2.,'reach the red end')
 move('left',red,G,0.,1.,'grasp the red end')
 move('left',red+[0,0,.07],G,0.,2.,'lift the red end')
 move('left',[.328,.19,.82],F,0.,3.,'face the open arch')
 move('left',[.328,.19,.762],F,0.,2.,'lower outside the loop')
 move('left',[.328,-.025,.762],F,0.,4.,'feed the end back through the arch')
 # Carry the tip beyond the far edge of the loop before lifting it.
 move('left',[.328,-.14,.762],F,0.,3.,'carry the end fully through the loop')
 # Release outside the loop before returning either wrist.
 from yam_arena import ik,station
 targets={}
 for side,offset in [('left',0),('right',7)]:
  point,rotation=ik.tcp_pose(p.a[offset:offset+6],station.BASES[side]);targets[side]=(point,rotation,.8)
 p.add(1.,'release the unthreaded cord',targets)
 p.add(4.,'clear the table',{'left':(np.array([.18,.36,.96]),G,.8),'right':(np.array([.25,-.30,.98]),D,.8)})
 p.add(6.,'released judging',{})
 print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
