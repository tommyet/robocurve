"""Numerical checks for crease formation, independent of the demo path."""
import unittest
import numpy as np
from paper import Paper
from paper_solver import hinges


class PaperChecks(unittest.TestCase):
    def test_starts_uncreased_and_does_not_fold_itself(self):
        p = Paper()
        self.assertEqual(len(np.unique(p.bend_stiffness)), 1)
        self.assertTrue(np.all(p.rest_angle == 0))
        self.assertTrue(np.allclose(p.hinges()[0], 0))
        xy = p.p[:, :2].copy()
        for _ in range(25):
            p.step({})
        self.assertLess(float(np.max(abs(p.p[:, :2]-xy))), 1e-10)
        self.assertTrue(np.all(p.rest_angle == 0))
        self.assertFalse(p.failed)

    def test_bending_gradient_matches_finite_difference(self):
        rng = np.random.default_rng(5)
        p = rng.normal(size=(100*4, 3))
        bends = np.arange(len(p)).reshape(-1, 4)
        _, grad = hinges(p, bends)
        step = 1e-6
        for j in range(4):
            for k in range(3):
                a, b = p.copy(), p.copy()
                a[bends[:, j], k] += step
                b[bends[:, j], k] -= step
                difference = hinges(a, bends)[0]-hinges(b, bends)[0]
                numeric = np.arctan2(np.sin(difference), np.cos(difference))/(2*step)
                self.assertLess(float(np.max(abs(numeric-grad[:, j, k]))), 1e-5)


if __name__ == '__main__':
    unittest.main()
