"""Fixed pre-wrapped, unthreaded starting layout shared by all policies.

The wide end has a short free tail above an open front loop. The right hand
holds its outer band; the narrow blade is routed inside the wrap.
The robot must thread the end, tighten, fit and release the knot. This file is
loaded only during reset, never to prescribe runtime cloth motion.
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
