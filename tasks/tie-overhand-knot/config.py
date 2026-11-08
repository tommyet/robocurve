"""Physical dimensions and fixed layout. All values are metres, kg and seconds.

This is a development configuration; validation records, not this file, establish
whether the robot can complete the task or whether the rope model is adequate.
"""
import numpy as np

TABLE_TOP = .7475
RADIUS = .004
LENGTH = .96
SEGMENT = .01
MASS = .0375
RUN_LIMIT = 2400
INSTRUCTION = (
    "Tie one overhand knot in the blue cord, then let go. "
    "The knot will be tested with a gentle pull."
)


def initial_nodes():
    """Untied U: 34 straight links, 28 around a semicircle, 34 straight."""
    radius = SEGMENT / (2 * np.sin(np.pi / 56))
    a = np.column_stack((np.linspace(-.02, .32, 35), np.zeros(35)))
    theta = np.linspace(np.pi / 2, -np.pi / 2, 29)
    b = np.column_stack((.32 + radius * np.cos(theta),
                         -radius + radius * np.sin(theta)))
    c = np.column_stack((np.linspace(.32, -.02, 35), np.full(35, -2 * radius)))
    xy = np.vstack((a, b[1:], c[1:]))
    return np.column_stack((xy, np.full(len(xy), TABLE_TOP + RADIUS + .0005)))


CONFIG = dict(radius=RADIUS, length=LENGTH, segment=SEGMENT, mass=MASS,
              table_top=TABLE_TOP, run_limit=RUN_LIMIT, instruction=INSTRUCTION,
              friction=.8, bend_stiffness=.0002, bend_damping=.00002,
              linear_damping=.5, angular_damping=2.,
              contact_offset=.0005, solver_position_iterations=64,
              solver_velocity_iterations=16, anchor_start=True,
              proof_load_n=.981, proof_seconds=5.)
