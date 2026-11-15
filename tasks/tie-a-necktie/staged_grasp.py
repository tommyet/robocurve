"""Fixed, untied experimenter-loaded starting grasps shared by every policy.

The left fingers hold the wide tip. The right fingers hold the two standing
strands together below the collar, before any wrap or threading. This array is
used only by reset; no runtime motion or knot is prescribed here.
"""
from pathlib import Path
import numpy as np

DATA = Path(__file__).with_name('staged-start.npz')


def initial_layout(mesh):
    with np.load(DATA) as data:
        if (not np.array_equal(mesh.faces, data['faces']) or
                not np.allclose(mesh.rest, data['rest'], rtol=0., atol=1e-12)):
            raise ValueError('Staged starting grasp does not match the tie mesh')
        return data['nodes'].copy()


def initial_action():
    with np.load(DATA) as data:
        return data['action'].copy()
