from pathlib import Path
import json,numpy as np
from planner import Plan
from geometry import ELASTIC,HEAD
p=Plan()
RL=np.array([[0,-1,0],[0,0,-1],[1,0,0.]])
RR=np.array([[0,-1,0],[0,0,1],[-1,0,0.]])
L=ELASTIC+[0,.0175,0];R=ELASTIC+[0,-.0175,0]
p.add(3,'approach the plain elastic from its two sides',{'left':(L+[0,.045,.025],RL,.35),'right':(R+[0,-.045,.025],RR,.35)},'joint')
p.add(2,'place the pads around opposite parts of the elastic',{'left':(L,RL,.18),'right':(R,RR,.18)})
p.add(2,'grip the elastic',{'left':(L,RL,0.),'right':(R,RR,0.)})
p.add(4,'lift and stretch the elastic',{'left':(ELASTIC+[0,.045,.065],RL,0.),'right':(ELASTIC+[0,-.045,.065],RR,0.)})
p.add(4,'place the opening beneath the loose hair ends',{'left':([.303,.045,HEAD[2]-.235],RL,0.),'right':([.303,-.045,HEAD[2]-.235],RR,0.)})
p.add(7,'bring the loose hair through the elastic',{'left':([.303,.045,HEAD[2]-.100],RL,0.),'right':([.303,-.045,HEAD[2]-.100],RR,0.)})
p.add(3,'let the elastic gather the ponytail',{'left':([.303,.026,HEAD[2]-.100],RL,0.),'right':([.303,-.026,HEAD[2]-.100],RR,0.)})
p.add(2,'release the elastic',{'left':([.303,.026,HEAD[2]-.100],RL,.6),'right':([.303,-.026,HEAD[2]-.100],RR,.6)})
p.add(3,'withdraw from the ponytail',{'left':([.27,.14,HEAD[2]-.10],RL,.6),'right':([.27,-.14,HEAD[2]-.10],RR,.6)})
p.add(4,'released inspection',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
