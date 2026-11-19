"""Complete robot-only replacement sequence; native validation is pending."""
from pathlib import Path
import json,numpy as np
from scipy.spatial.transform import Rotation as Rot
from planner import Plan
from geometry import PLUG,CARRIER,TOOL,FC,PLUG_ROT
from common import down
p=Plan();RL=Rot.from_euler('x',45,degrees=True).as_matrix()@np.array([[1.,0,0],[0,0,-1],[0,1,0]]);RR=down(180);RT=down(180);L=PLUG+[0,.018,0]
p.add(3,'approach the plug and screwdriver',{'left':(L+[0,.07,0],RL,.65),'right':(TOOL+[0,0,.07],RR,.4)},'joint')
p.add(2,'grip the moulded plug body and tool handle',{'left':(L,RL,.65),'right':(TOOL,RR,.35)})
p.add(2,'close the fingers',{'left':(L,RL,0.),'right':(TOOL,RR,0.)})
p.add(3,'lift the unplugged plug for access',{'left':(L+[0,-.08,.12],RL,0.),'right':(TOOL+[0,0,.08],RR,0.)})
edge=PLUG+PLUG_ROT.apply(FC+[.0155,0,-.0005])+[0,-.08,.12];outside=edge+PLUG_ROT.apply([.009,0,0]);fulcrum=PLUG+PLUG_ROT.apply(FC+[.023,0,-.0006])+[0,-.08,.12];tip_offset=np.array([0,.119,0]);tcp=edge-tip_offset
p.add(3,'align the blade outside the carrier lip',{'right':(outside-tip_offset,RT,0.)})
p.add(2,'slide the blade beneath the carrier face',{'right':(tcp,RT,0.)})
rotation=PLUG_ROT.as_matrix()@Rot.from_euler('y',45,degrees=True).as_matrix()@PLUG_ROT.as_matrix().T;pry=fulcrum+rotation@(tcp-fulcrum)
p.add(4,'lever the carrier against the plug rim',{'right':(pry,rotation@RT,0.)})
p.add(3,'lift the levered carrier clear of its detents',{'right':(pry+[0,0,.008],rotation@RT,0.)})
p.add(2,'hold for inspection',{})
from sequence import append_plan
append_plan(p,left_return=(L+[0,-.08,.04],RL,0.))
p.add(4,'return the plug to the table',{'left':(L,RL,0.)})
p.add(1,'release the plug',{'left':(L,RL,.7)})
p.add(3,'withdraw both hands',{'left':(L+[0,.08,.06],RL,.7)})
p.add(4,'inspect the released parts',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
