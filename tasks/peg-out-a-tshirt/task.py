"""Peg a flexible cotton T-shirt onto a clothesline with two passive spring pegs.

Development scene. The full-score controller and final evidence are not yet
available. Neither fixture nor peg ever attaches to cloth in software.
"""
from arena_cloth import Cloth
from arena_props import SpringPeg,Fixture
from cloth_mesh import tshirt
from native_cloth import Fabric
from scene import initial_layout,TABLE,LINE_X,LINE_Z,LINE_HALF_SPAN

SCENE='station'
SCORE_OVER='end'
SUCCESS_HOLD_S=0.
INSTRUCTION='Hang the T-shirt from the clothesline using the two pegs, then let go and leave it secure and clear of the table.'
DEVELOPMENT_ONLY=True
MESH=tshirt()
INITIAL=initial_layout(MESH)
OBJECTS=[
    Cloth('tshirt',pos=(.33,0.,TABLE+.003),size=(.30,.40,.0016),
          color=(.08,.35,.72),mesh=MESH,initial=INITIAL,fabric=Fabric()),
    Fixture('rack',pos=(LINE_X,0.,(TABLE+LINE_Z)/2),
            size=(.15,2*LINE_HALF_SPAN+.095,LINE_Z-TABLE),kind='clothesline'),
    SpringPeg('left_peg',pos=(.12,.20,TABLE+.014),size=(.070,.010,.022)),
    SpringPeg('right_peg',pos=(.12,-.20,TABLE+.014),size=(.070,.010,.022)),
]


def success(objects):
    # No smoke run can accidentally become a successful competition episode.
    return False
