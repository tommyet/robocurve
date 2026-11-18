from pathlib import Path
import json,numpy as np
from common import down,TABLE
from geometry import BRUSH,TOOL
from planner import Plan
p=Plan();R=down();RL=down(180);L=BRUSH+[0,.095,.002]
p.add(3,'approach brush handle and comb',{'left':(L+[0,0,.06],RL,.4),'right':(TOOL+[0,0,.06],R,.4)},'joint')
p.add(2,'lower to ordinary handles',{'left':(L,RL,.35),'right':(TOOL,R,.35)})
p.add(2,'hold brush and comb',{'left':(L,RL,0.),'right':(TOOL,R,0.)})
p.add(2,'lift comb clear of rest',{'right':(TOOL+[0,0,.07],R,0.)})
p.add(3,'place pin tail in a lane between bristles',{'right':([.3035,-.17,BRUSH[2]+.004],R,0.)})
p.add(6,'slide the tail beneath the trapped hair',{'right':([.3035,-.080,BRUSH[2]+.004],R,0.)})
p.add(3,'lift the hair out through the pins',{'right':([.3035,-.080,BRUSH[2]+.060],R,0.)})
p.add(3,'move the lifted hair above the dish',{'right':([.30,.045,BRUSH[2]+.065],R,0.)})
p.add(3,'draw the comb out over the dish',{'right':([.37,-.03,BRUSH[2]+.10],R,0.)})
p.add(3,'return the comb to its rest',{'right':(TOOL+[0,0,.025],R,0.)})
p.add(1,'let go of handles',{'left':(L,RL,.5),'right':(TOOL+[0,0,.025],R,.5)})
p.add(3,'move both hands clear',{'left':(L+[0,0,.10],RL,.7),'right':(TOOL+[0,0,.10],R,.7)})
p.add(4,'released inspection',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
