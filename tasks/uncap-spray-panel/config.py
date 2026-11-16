"""SI units; fixed first prototype, not yet validated in the simulator."""
TOP = .7475
RISER_HEIGHT = .05
CAN_REST_HEIGHT = TOP + RISER_HEIGHT + .07
CAN_START = (.26, 0., CAN_REST_HEIGHT)
CAP_START = (.26, 0., CAN_REST_HEIGHT + .087)
BUTTON_START = (.26, 0., CAN_REST_HEIGHT + .077)
CAP_PAD = (.34, -.10, TOP + .001)
CAN_PAD = (.26, 0., TOP + .001)
TARGET_X = .47
TARGET_CENTER = (-.035, TOP + .205)  # fixed plaque y,z
TARGET_RADIUS = .040
# Transit remains the old four-zone anchor; changing the target must not shift it.
SPRAY_TRANSIT_CAN = (.26, 0., .9105)
SPRAY_HELD_CAN = (.26, -.035, .8755)
BOARD_HALF = .18
CELL = .01
GRID = 36
NOZZLE_LOCAL = (.009, 0., .077)
PRESS_TRAVEL = .002
SPRAY_HALF_ANGLE = 12.  # degrees
MIN_RANGE, MAX_RANGE = .12, .30
COAT_DOSE = .08  # effective seconds at plume centre
# Photo-area rubric, fixed before rescoring the historical run. A visible coat
# is at least the midpoint blend from the original surface to displayed blue.
VISIBLE_COAT_FRACTION = .5
VISIBLE_DOSE = VISIBLE_COAT_FRACTION*COAT_DOSE
PLAQUE_AREA_M2 = 3.141592653589793*TARGET_RADIUS**2
MAX_OFF_PLAQUE_AREA_M2 = .15*PLAQUE_AREA_M2  # 7.539822 cm², fixed plaque reference
SPRAY_DOMAIN_TOLERANCE_M = 1e-9
MAX_SPRAY_SECONDS = 12.
CAN_COLOR = (1., .26, .025)
CAP_COLOR = (.055, .065, .075)
BACKING_COLOR = (.60, .63, .66)
WORKTOP_COLOR = (.36, .39, .42)
INSTRUCTION = ('Remove the cap from the spray-paint can and put it on the blue pad. '
               'Spray a blue coat over the single white circular plaque, keeping paint off the surrounding backing. '
               'Finish holding the can upright and steady in the left gripper, with its nozzle released and the right hand clear.')
