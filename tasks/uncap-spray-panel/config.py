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
TARGET_CENTER = (0., TOP + .24)  # y,z
TARGET_HALF = .07
BOARD_HALF = .18
CELL = .01
GRID = 36
NOZZLE_LOCAL = (.009, 0., .077)
PRESS_TRAVEL = .002
SPRAY_HALF_ANGLE = 12.  # degrees
MIN_RANGE, MAX_RANGE = .12, .30
COAT_DOSE = .08  # effective seconds at plume centre
MAX_SPRAY_SECONDS = 12.
CAN_COLOR = (1., .26, .025)
CAP_COLOR = (.055, .065, .075)
BACKING_COLOR = (.60, .63, .66)
WORKTOP_COLOR = (.36, .39, .42)
INSTRUCTION = ('Remove the cap from the spray-paint can and put it on the blue pad. '
               'Spray a blue coat over the white panel, keeping paint off the surrounding backing. '
               'Leave the can upright on its grey pad with the nozzle released.')
