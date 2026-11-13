"""Unbox a taped delivery parcel using a guarded cutter.

A plain brown cardboard parcel is held in a packing fixture at world (0.27, 0).
Its two long-edge top flaps meet at y=0. Brown tape seals the 21 cm seam along x.
The orange guarded cutter is on the left; the blue 4 cm item is inside.
Cut the whole seam, return the cutter to its orange pad, physically open both
flaps, and put the item on the green pad on the right. Use run.py: it installs
hinges and the tape fracture approximation and records measured object poses.
"""
from yam_arena.task_file import Box
from config import *
SCENE = 'station'
SUCCESS_HOLD_S = 0.
SCORE_OVER = 'end'
BROWN = (.58, .36, .16)
OBJECTS = [
    Box('bottom', pos=(*CENTER, TOP + WALL/2), size=(LENGTH, WIDTH, WALL), color=BROWN),
    Box('front', pos=(CENTER[0]-LENGTH/2+WALL/2, 0., TOP+HEIGHT/2), size=(WALL, WIDTH, HEIGHT), color=BROWN),
    Box('back', pos=(CENTER[0]+LENGTH/2-WALL/2, 0., TOP+HEIGHT/2), size=(WALL, WIDTH, HEIGHT), color=BROWN),
    Box('left_wall', pos=(CENTER[0], WIDTH/2-WALL/2, TOP+HEIGHT/2), size=(LENGTH, WALL, HEIGHT), color=BROWN),
    Box('right_wall', pos=(CENTER[0], -WIDTH/2+WALL/2, TOP+HEIGHT/2), size=(LENGTH, WALL, HEIGHT), color=BROWN),
    Box('left_flap', pos=(CENTER[0], WIDTH/4+.001, LID_Z), size=(LENGTH, WIDTH/2-.002, WALL), mass=.018, color=BROWN),
    Box('right_flap', pos=(CENTER[0], -WIDTH/4-.001, LID_Z), size=(LENGTH, WIDTH/2-.002, WALL), mass=.018, color=BROWN),
    Box('cutter', pos=CUTTER_START, size=(.14,.025,.025), mass=.055, color=(1.,.28,.03)),
    Box('item', pos=(*CENTER,TOP+WALL+.02), size=(.04,.04,.04), mass=.06, color=(.08,.35,.9)),
    Box('cutter_pad',pos=(.13,.19,TOP+.001),size=(.17,.07,.002),color=(.9,.35,.08)),
    Box('cutter_cradle',pos=(.13,.19,TOP+.00575),size=(.08,.04,.0075),color=(.75,.25,.04)),
    Box('destination',pos=(*DESTINATION,TOP+.001),size=(.10,.10,.002),color=(.1,.6,.22)),
]
_tracker = None

def success(objects):
    if _tracker is None:
        raise RuntimeError('Use run.py to install the hinged box and tape mechanics')
    return _tracker.value == 1.

def score(objects):
    return _tracker.value if _tracker else 0.

def demo():
    """Experimental robot-only plan; not yet a validated full-score demonstration."""
    from yam_arena.demo import Waypoint as W
    from yam_arena.constants import FINGER_OPEN as O
    from math import sin, cos, radians
    grip = -.011  # 22 mm jaw gap, small squeeze on 25 mm handle
    hover = TOP+.17
    x,y,z=CUTTER_START
    left=[W(2,(x,y,hover),O),W(2,(x,y,z+.006),O),W(1,(x,y,z+.006),grip),
          W(2,(x,y,hover),grip), W(2,(SEAM[0]-.070,0.,LID_Z+.06),grip),
          W(2,(SEAM[0]-.070,0.,LID_Z+.020+.006),grip),
          W(6,(SEAM[1]-.045,0.,LID_Z+.020+.006),grip),
          W(2,(SEAM[1]-.045,0.,hover),grip),W(2,(x,y,hover),grip),
          W(2,(x,y,z+.006),grip),W(1,(x,y,z+.006),O),W(2,(x,y,hover),O)]
    # Both jaws grasp a thickened flap tab. Circular lift about the long-edge fold.
    for angle in (0,20,45,70,100):
        a=radians(angle)
        pos=(.27,.09-.055*cos(a),LID_Z+.055*sin(a)+.008)
        if angle==0:
            left += [W(2,(.27,.035,hover),O),W(2,pos,O),W(1,pos,-.004)]
        else: left += [W(2,pos,-.004)]
    left += [W(1,pos,O),W(2,(.12,.22,hover),O)]
    right=[W(29,(.13,-.22,hover),O)]
    for angle in (0,20,45,70,100):
        a=radians(angle)
        pos=(.27,-.09+.055*cos(a),LID_Z+.055*sin(a)+.008)
        if angle==0: right += [W(2,(.27,-.035,hover),O),W(2,pos,O),W(1,pos,-.004)]
        else: right += [W(2,pos,-.004)]
    right += [W(1,pos,O),W(2,(.27,-.15,hover),O)]
    from yam_arena.demo import pick_place_waypoints
    right += pick_place_waypoints((.27,0.,TOP+.03),(*DESTINATION,TOP+.03),travel_z=hover)
    return {'left':left,'right':right}
