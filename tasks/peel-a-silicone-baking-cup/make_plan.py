from pathlib import Path
import numpy as np,json
from scipy.spatial.transform import Rotation
from planner import Plan
from common import down,TABLE
from geometry import C
p=Plan();RL=Rotation.from_euler('z',-20,degrees=True).as_matrix()@Rotation.from_euler('x',-15,degrees=True).as_matrix()@down(0);RR=Rotation.from_euler('x',160,degrees=True).as_matrix()@np.array([[0,-1,0],[0,0,-1],[1,0,0.]])
L=C+[0,0,.052]-.006*RL[:,2];Q=C+[0,-.048,.032]-.006*RR[:,2]
p.add(3,'approach the muffin',{'left':(L+[0,0,.10],RL,.9),'right':(Q+[0,-.06,.10],RR,.12)},'joint')
p.add(2,'enclose the muffin gently',{'left':(L,RL,.8)})
p.add(5,'support the muffin',{'left':(L,RL,.716)})
p.add(2,'lift with its baking cup',{'left':(L+[0,0,.09],RL,.716)})
p.add(2,'enclose the near cup rim',{'right':(Q+[0,0,.09],RR,.12)})
p.add(1,'grip the cup rim',{'right':(Q+[0,0,.09],RR,0.)})
p.add(4,'peel the rim out and down',{'right':(Q+[0,-.08,.025],RR,0.)})
p.add(3,'peel the cup from the base',{'right':(Q+[0,-.10,.005],RR,0.)})
p.add(2,'return empty cup over the tray',{'right':(Q+[0,-.06,.005],RR,0.)})
p.add(1,'release empty cup',{'right':(Q+[0,-.06,.005],RR,.7)})
p.add(2,'lower muffin to tray',{'left':(L+[0,.045,0],RL,.716),'right':(Q+[0,-.13,.15],RR,.7)})
p.add(1,'release muffin',{'left':(L+[0,.045,0],RL,.9)})
p.add(2,'withdraw',{'left':(L+[0,.09,.11],RL,.9)})
p.add(4,'released outcome',{})
print(json.dumps(p.save(Path(__file__).with_name('demo-plan.json'))))
