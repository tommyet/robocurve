import unittest
import numpy as np
from demo_control import validate


class OrdinaryControlTests(unittest.TestCase):
    def payload(self,actions):
        return dict(schema='ordinary-demo-actions-v1',start_step=2181,final=True,
                    frames=[dict(action14=a) for a in actions])

    def check(self,payload,**updates):
        args=dict(step=2181,previous=np.zeros(14),low=np.full(14,-1.),high=np.ones(14),limits=np.full(14,.1),remaining=5)
        args.update(updates)
        return validate(payload,**args)

    def test_accepts_bounded_motion_and_preserves_actions(self):
        values=np.linspace(0,.2,4)[:,None]*np.ones((1,14))
        np.testing.assert_array_equal([f['action14'] for f in self.check(self.payload(values.tolist()))],values)

    def test_rejects_wrong_boundary_and_over_budget(self):
        p=self.payload([[0.]*14]);p['start_step']=2182
        with self.assertRaises(ValueError):self.check(p)
        with self.assertRaises(ValueError):self.check(self.payload([[0.]*14]*6))

    def test_rejects_nonfinite_unbounded_or_fast_commands(self):
        for value in (float('nan'),1.2,.2):
            with self.assertRaises(ValueError):self.check(self.payload([[value]*14]))


if __name__=='__main__':unittest.main()
