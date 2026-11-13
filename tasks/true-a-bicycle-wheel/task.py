"""Native compliant wheel, stand and wrench; preview-only until validated."""
from arena_wheel import WheelAssembly
SCENE = 'station'
SCORE_OVER = 'end'
INSTRUCTION = 'Adjust the spoke nipples to leave the bicycle wheel running straight and freely rotating.'
DEVELOPMENT_ONLY = True
OBJECTS = [WheelAssembly('wheel_station', pos=(.35, 0., 1.005), size=(.20, .45, .45))]

def score(objects):
    return 0.

def success(objects):
    return False
