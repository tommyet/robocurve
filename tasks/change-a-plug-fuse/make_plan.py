"""Initial lever-and-extract probe, not yet a complete fuse-change demo."""
from pathlib import Path
import json,numpy as np
from scipy.spatial.transform import Rotation as Rot
from planner import Plan
from geometry import PLUG,CARRIER,TOOL,FC
from common import down
p=Plan();RL=down(180);RR=down(180);RT=down(-90);L=PLUG+[0,0,.004]
p.add(3,'approach the plug and screwdriver',{'left':(L+[0,0,.07],RL,.8),'right':(TOOL+[0,0,.07],RR,.4)},'joint')
p.add(2,'grip the moulded plug body and tool handle',{'left':(L,RL,.8),'right':(TOOL,RR,.35)})
p.add(2,'close the fingers',{'left':(L,RL,0.),'right':(TOOL,RR,0.)})
p.add(3,'lift the unplugged plug for access',{'left':(L+[0,0,.04],RL,0.),'right':(TOOL+[0,0,.08],RR,0.)})
edge=CARRIER+[.016,0,.04-.0008];fulcrum=edge+[.009,0,0];tip_offset=np.array([-.069,0,0]);tcp=edge-tip_offset
p.add(4,'place the flat blade beneath the carrier lip',{'right':(tcp,RT,0.)})
rotation=Rot.from_euler('y',15,degrees=True).as_matrix();pry=fulcrum+rotation@(tcp-fulcrum)
p.add(4,'lever the carrier against the plug rim',{'right':(pry,rotation@RT,0.)})
p.add(3,'hold for inspection',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
