"""SI units; fixed first prototype, not yet validated in the simulator."""
TOP = .7475
CAN_START = (.18, .16, TOP + .07)
CAP_START = (.18, .16, TOP + .157)
BUTTON_START = (.18, .16, TOP + .147)
CAP_PAD = (.13, -.22, TOP + .001)
CAN_PAD = (.18, .16, TOP + .001)
TARGET_X = .43
TARGET_CENTER = (0., TOP + .20)  # y,z
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
INSTRUCTION = ('Remove the cap from the spray-paint can and put it on the blue pad. '
               'Spray a blue coat over the white panel, keeping paint off the surrounding backing. '
               'Leave the can upright on its grey pad with the nozzle released.')
