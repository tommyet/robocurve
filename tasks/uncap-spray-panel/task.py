"""Uncap a spray can, coat a panel, and put the can down. Use run.py."""
from yam_arena.task_file import Box
from config import *

SCENE = 'station'
SUCCESS_HOLD_S = 0.
SCORE_OVER = 'end'
OBJECTS = [
    # run.py replaces the three proxies with compound cylindrical colliders.
    Box('spray_can', pos=CAN_START, size=(.052,.052,.14), mass=.25, color=CAN_COLOR),
    Box('cap', pos=CAP_START, size=(.06,.06,.034), mass=.018, color=CAP_COLOR),
    Box('button', pos=BUTTON_START, size=(.018,.018,.010), mass=.003, color=(.9,.9,.9)),
    Box('work_mat', pos=(.30,0.,TOP+.0005), size=(.57,.63,.001), color=WORKTOP_COLOR),
    Box('cap_pad', pos=CAP_PAD, size=(.10,.10,.002), color=(.42,.72,.95)),
    Box('can_pad', pos=CAN_PAD, size=(.10,.10,.002), color=(.20,.23,.26)),
    Box('can_riser',pos=(CAN_PAD[0],CAN_PAD[1],TOP+RISER_HEIGHT/2),
        size=(.08,.08,RISER_HEIGHT),color=(.48,.50,.52)),
    Box('backing', pos=(TARGET_X+.008,0.,TARGET_CENTER[1]),
        size=(.012,.36,.36), color=BACKING_COLOR),
    Box('panel', pos=(TARGET_X+.001,0.,TARGET_CENTER[1]),
        size=(.002,.14,.14), color=(.95,.95,.95)),
    Box('stand', pos=(TARGET_X+.05,0.,TOP),
        size=(.12,.29,.45), color=(.18,.24,.28)),
]
_tracker = None
_diagnostic = False

def score(objects):
    if _tracker is None:
        raise RuntimeError('Use run.py: native cap and nozzle mechanics are required')
    return 0. if _diagnostic else _tracker.value

def success(objects):
    return score(objects) == 1.

def demo():
    """Diagnostic cap-removal attempt; not a full-score painting demo."""
    from yam_arena.demo import Waypoint as W
    from yam_arena.constants import FINGER_OPEN as O
    x,y,_=CAN_START
    return {
        'left':[W(2.,(x,y,TOP+.26),O),W(2.,(x,y,TOP+.08),O),
                W(2.,(x,y,TOP+.08),-.024),W(24.,(x,y,TOP+.08),-.024)],
        'right':[W(7.,(x,y,TOP+.29),O),W(3.,(x,y,TOP+.157),O),
                 W(2.,(x,y,TOP+.157),-.028),W(3.,(x,y,TOP+.27),-.028),
                 W(3.,(CAP_PAD[0],CAP_PAD[1],TOP+.27),-.028),
                 W(3.,(CAP_PAD[0],CAP_PAD[1],TOP+.019),-.028),
                 W(2.,(CAP_PAD[0],CAP_PAD[1],TOP+.019),O),
                 W(3.,(CAP_PAD[0],CAP_PAD[1],TOP+.25),O)],
    }
