"""Native flat-fabric necktie and collar, for diagnostic YAM validation.

This untied half-wrap must settle before a reproducible task reset can be
certified. It is not a preformed knot or a successful demonstration.
"""
import os
from arena_cloth import Cloth
from arena_props import Fixture
from cloth_mesh import necktie
from layout import initial_layout,face_colors,NECK,TABLE
from native_cloth import Fabric

SCENE='station'
SCORE_OVER='end'
SUCCESS_HOLD_S=0.
INSIDE_OUT_RESET=os.environ.get('ROBOCURVE_TIE_INSIDE_OUT_RESET','0')=='1'
INSTRUCTION=('Tie a simple (Oriental) necktie knot' if INSIDE_OUT_RESET else 'Tie a four-in-hand necktie')+' on the collar form and leave it ready to wear.'
DEVELOPMENT_ONLY=True
MESH=necktie()
INITIAL=initial_layout(MESH,inside_out=INSIDE_OUT_RESET)
TIE_FABRIC=Fabric(thickness=.0012,density=500.,youngs_modulus=3e6,
                  dynamic_friction=.45,bend_modulus=2.5e5,
                  contact_offset=.001,rest_offset=.0006)
OBJECTS=[
    Cloth('tie',pos=tuple((INITIAL.min(0)+INITIAL.max(0))/2),
          size=tuple(INITIAL.max(0)-INITIAL.min(0)),color=(.50,.08,.17),
          mesh=MESH,initial=INITIAL,fabric=TIE_FABRIC,vertex_colors=face_colors(MESH)),
    Fixture('collar',pos=(.52,0.,(NECK[2]+TABLE)/2),size=(.22,.28,NECK[2]+.0325-TABLE),kind='collar'),
]


def success(objects):
    return False
