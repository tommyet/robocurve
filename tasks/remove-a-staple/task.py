"""Native paper and free staple scene; development only, no task score yet."""
import numpy as np
from arena_paper import Paper
from arena_hardware import StapleHardware
from full_scene import paper_mesh,SHEET_CENTRES,PAPER_TOP

SCENE='station'
SCORE_OVER='end'
INSTRUCTION='Remove the staple without tearing either sheet, then separate the sheets.'
DEVELOPMENT_ONLY=True
OBJECTS=[]
for i,xy in enumerate(SHEET_CENTRES):
    mesh=paper_mesh(i);position=(*xy,PAPER_TOP-.00015+i*.0001)
    OBJECTS.append(Paper('paper_'+str(i),pos=position,size=(.21,.148,.0001),mesh=mesh,
        initial=mesh.rest+np.asarray(position)))
OBJECTS.append(StapleHardware('hardware',pos=(.25,-.13,.77),size=(.3,.3,.05)))

def score(objects):return 0.
def success(objects):return False
