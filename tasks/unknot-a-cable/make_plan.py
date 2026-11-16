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
 move('left',[.328,-.025,.815],F,0.,2.,'lift through the open loop')
 # Move the supporting loop away before returning the free end. Returning
 # the end along its entry corridor can thread it through the loop again.
 move('right',[.42,-.18,.82],S,0.,4.,'draw the loop away from the unthreaded end')
 move('left',[.328,-.025,.815],G,0.,2.,'turn the free end for withdrawal')
 move('left',[.28,.04,.89],G,0.,2.,'lift clear of the remaining cord')
 move('left',[.20,.30,.89],G,0.,3.,'draw the free end away above the cord')
 p.add(3.,'lay the opened cord down',{'left':(np.array([.20,.30,.754])-.009*G[:,2],G,0.),'right':(np.array([.42,-.18,.754])-.009*S[:,2],S,0.)})
 p.add(1.,'release the cord',{'left':(np.array([.20,.30,.754])-.009*G[:,2],G,.8),'right':(np.array([.42,-.18,.754])-.009*S[:,2],S,.8)})
 p.add(3.,'clear the table',{'left':(np.array([.18,.36,.96]),G,.8),'right':(np.array([.25,-.30,.98]),D,.8)})
 p.add(4.,'released judging',{})
 print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
