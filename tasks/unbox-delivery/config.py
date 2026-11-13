"""Fixed prototype geometry, SI units."""
TOP = .7475
CENTER = (.27, 0.)
LENGTH, WIDTH, HEIGHT, WALL = .22, .18, .075, .003
LID_Z = TOP + HEIGHT + WALL / 2
SEAM = (.27 - .105, .27 + .105)
CUTTER_START = (.13, .19, TOP + .022)
TIP_LOCAL = (.065, 0., -.020)
DESTINATION = (.18, -.23)
INSTRUCTION = ('Use the orange package cutter to cut the tape along the top seam of the parcel. '
               'Put the cutter back on its orange pad, open both top flaps, and place the blue item on the green pad.')
