"""Uncap a spray can, coat a panel, and put the can down. Use run.py."""
from yam_arena.task_file import Box
from config import *

SCENE = 'station'
SUCCESS_HOLD_S = 0.
SCORE_OVER = 'end'
OBJECTS = [
    # run.py replaces the three proxies with compound cylindrical colliders.
    Box('spray_can', pos=CAN_START, size=(.052,.052,.14), mass=.25, color=(.15,.35,.8)),
    Box('cap', pos=CAP_START, size=(.06,.06,.034), mass=.018, color=(.10,.20,.50)),
    Box('button', pos=BUTTON_START, size=(.018,.018,.010), mass=.003, color=(.9,.9,.9)),
    Box('cap_pad', pos=CAP_PAD, size=(.10,.10,.002), color=(.15,.35,.9)),
    Box('can_pad', pos=CAN_PAD, size=(.10,.10,.002), color=(.45,.45,.45)),
    Box('backing', pos=(TARGET_X+.008,0.,TARGET_CENTER[1]),
        size=(.012,.36,.36), color=(.55,.52,.48)),
    Box('panel', pos=(TARGET_X+.001,0.,TARGET_CENTER[1]),
        size=(.002,.14,.14), color=(.95,.95,.95)),
    Box('stand', pos=(TARGET_X+.028,0.,TOP+.10),
        size=(.035,.06,.20), color=(.2,.2,.2)),
]
_tracker = None

def score(objects):
    if _tracker is None:
        raise RuntimeError('Use run.py: native cap and nozzle mechanics are required')
    return _tracker.value

def success(objects):
    return score(objects) == 1.

def demo():
    """Diagnostic cap-removal attempt; not a full-score painting demo."""
    from yam_arena.demo import Waypoint as W
    from yam_arena.constants import FINGER_OPEN as O
    x,y,_=CAN_START
    return {
        'left':[W(2.,(x,y,TOP+.26),O),W(2.,(x,y,TOP+.08),O),
                W(2.,(x,y,TOP+.08),.024),W(24.,(x,y,TOP+.08),.024)],
        'right':[W(7.,(x,y,TOP+.29),O),W(3.,(x,y,TOP+.157),O),
                 W(2.,(x,y,TOP+.157),.028),W(3.,(x,y,TOP+.27),.028),
                 W(3.,(CAP_PAD[0],CAP_PAD[1],TOP+.27),.028),
                 W(3.,(CAP_PAD[0],CAP_PAD[1],TOP+.019),.028),
                 W(2.,(CAP_PAD[0],CAP_PAD[1],TOP+.019),O),
                 W(3.,(CAP_PAD[0],CAP_PAD[1],TOP+.25),O)],
    }
