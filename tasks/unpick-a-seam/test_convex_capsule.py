"""Physical-envelope checks; native cooking is separately measured on the GPU."""
import unittest
import numpy as np
from scipy.spatial import ConvexHull
from convex_capsule import capsule_points


class CapsuleEnvelopeTests(unittest.TestCase):
    def test_support_function_is_inscribed_and_within_declared_error(self):
        rng=np.random.default_rng(715)
        directions=rng.normal(size=(2000,3));directions/=np.linalg.norm(directions,axis=1)[:,None]
        for length,radius in ((.001,.0004),(.014,.0005)):
            points=capsule_points(length,radius)
            exact=abs(directions[:,0])*length/2+radius
            measured=(directions@points.T).max(1)
            bound=radius*(1-np.cos(np.pi/24)*np.cos(np.pi/20))
            self.assertTrue(np.all(measured<=exact+1e-14))
            self.assertLessEqual(float(max(exact-measured)),bound+1e-14)
            self.assertLessEqual(len(points),255)
            expected=np.pi*radius**2*length+4*np.pi*radius**3/3
            self.assertGreater(ConvexHull(points).volume/expected,.979)

    def test_nonphysical_dimensions_are_rejected(self):
        for length,radius in ((0.,.001),(.001,-.001),(float('nan'),.001)):
            with self.assertRaises(ValueError):capsule_points(length,radius)
