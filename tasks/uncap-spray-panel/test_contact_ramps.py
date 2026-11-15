"""Command-rate regressions for preload transitions and the moving press face."""
import math
import unittest
from control_math import ramp_scalar,ramp_translation


class ContactRampTests(unittest.TestCase):
    def test_preload_builds_and_releases_gradually_without_overshoot(self):
        current=0.
        for target in (.014,0.):
            values=[]
            for _ in range(80):
                previous=current;current=ramp_scalar(current,target,.005,.05)
                self.assertLessEqual(abs(current-previous),.00025+1e-15)
                self.assertGreaterEqual(current,0.);self.assertLessEqual(current,.014)
                values.append(current)
            self.assertAlmostEqual(current,target)
            self.assertNotEqual(values[0],target)

    def test_full_hover_to_press_approach_has_bounded_euclidean_speed(self):
        current=[.3,.02,.105];target=[.3,.02,.082-.0027]
        initial=current.copy();steps=0
        while math.dist(current,target)>1e-12:
            previous=current;current=ramp_translation(current,target,.010,.05)
            self.assertIsNot(current,previous)
            self.assertLessEqual(math.dist(current,previous),.0005+1e-15)
            steps+=1
            self.assertLess(steps,60)
        self.assertEqual(initial,[.3,.02,.105])
        self.assertEqual(steps,52) # 2.6 seconds leaves room in the 8s shot.

    def test_diagonal_follow_uses_vector_norm_and_close_target_does_not_overshoot(self):
        current=ramp_translation([0.,0.,0.],[1.,1.,1.],.010,.05)
        self.assertAlmostEqual(math.sqrt(sum(v*v for v in current)),.0005)
        target=[.00001,0.,0.]
        self.assertEqual(ramp_translation([0.,0.,0.],target,.010,.05),target)
        self.assertEqual(ramp_translation([0.,0.,0.],target,.010,0),[0.,0.,0.])

    def test_nonfinite_or_invalid_rate_inputs_rejected(self):
        for speed,dt in ((-1,.05),(1,-.1),(1,.11),(math.inf,.05),(1,math.nan)):
            with self.assertRaises(ValueError):ramp_scalar(0.,.014,speed,dt)
            with self.assertRaises(ValueError):ramp_translation([0.]*3,[1.]*3,speed,dt)


if __name__=='__main__':unittest.main()
