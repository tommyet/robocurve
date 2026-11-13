"""Full-size flexible panel-paper candidate; unscored until robot validation."""
import numpy as np
from arena_panels import PanelPaper
from arena_hardware import StapleHardware
from facet_paper import box_task_mesh
from paper import PaperMesh
from full_scene import SHEET_CENTRES,scene_layout
import runtime_config

SCENE='station'
SCORE_OVER='end'
INSTRUCTION='Remove the staple without tearing either sheet. Leave the complete staple at least10mm clear of both sheets.'
DEVELOPMENT_ONLY=True
OBJECTS=[]
layout=scene_layout(runtime_config.RESET_PROFILE)
for i,xy in enumerate(SHEET_CENTRES):
    mesh=box_task_mesh(i);position=np.array((*xy,layout['paper_centres_z'][i]))
    mesh=PaperMesh(mesh.rest+position,mesh.faces,mesh.holes)
    OBJECTS.append(PanelPaper('paper_'+str(i),pos=position,size=(.21,.148,.0001),mesh=mesh))
OBJECTS.append(StapleHardware('hardware',pos=(.25,-.13,.77),size=(.3,.3,.05)))

def score(objects):return 0.
def success(objects):return False
