"""Native paper and free staple scene; development only, no task score yet."""
import numpy as np
from arena_paper import Paper
from arena_hardware import StapleHardware
from full_scene import paper_mesh,SHEET_CENTRES,scene_layout
import runtime_config

SCENE='station'
SCORE_OVER='end'
INSTRUCTION='Remove the staple without tearing either sheet. Leave the complete staple at least 10 mm clear of both sheets.'
DEVELOPMENT_ONLY=True
OBJECTS=[]
layout=scene_layout(runtime_config.RESET_PROFILE)
for i,xy in enumerate(SHEET_CENTRES):
    mesh=paper_mesh(i,runtime_config.MESH_PROFILE);position=(*xy,layout['paper_centres_z'][i])
    OBJECTS.append(Paper('paper_'+str(i),pos=position,size=(.21,.148,.0001),mesh=mesh,
        initial=mesh.rest+np.asarray(position)))
OBJECTS.append(StapleHardware('hardware',pos=(.25,-.13,.77),size=(.3,.3,.05)))

def score(objects):return 0.
def success(objects):return False
