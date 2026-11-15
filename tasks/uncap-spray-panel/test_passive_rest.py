"""Passive rest initialization and native energy protocol; no physics startup."""
import importlib.util
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import numpy as np
from config import TOP,RISER_HEIGHT,CAP_PAD

PATH=Path(__file__).with_name('run.py')
spec=importlib.util.spec_from_file_location('_passive_rest_runner',PATH)
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)


class PassiveRestTests(unittest.TestCase):
    def test_one_degree_can_is_supported_and_button_starts_joint_consistent(self):
        poses=runner.passive_rest_initial();can,q=poses['spray_can'];button,button_q=poses['button']
        angle=math.radians(1);c,s=math.cos(angle),math.sin(angle)
        rotation=np.array(((1.,0.,0.),(0.,c,-s),(0.,s,c)))
        self.assertTrue(all(type(v) is float for pose in poses.values() for part in pose for v in part))
        self.assertEqual(q,button_q);self.assertAlmostEqual(sum(v*v for v in q),1.)
        self.assertAlmostEqual(can[2]-.070*c-.026*s,TOP+RISER_HEIGHT)
        np.testing.assert_allclose(rotation.T@(np.array(button)-can),(0,0,.077),atol=1e-15)
        self.assertEqual(poses['cap'][0],(CAP_PAD[0],CAP_PAD[1],TOP+.019))

    def test_native_actor_inertia_and_com_velocity_energy_use_correct_frames(self):
        rotation=np.array(((0.,-1,0),(1,0,0),(0,0,1)))
        result=runner.passive_body_energy(.25,np.diag([1.,2.,3.]).reshape(-1,order='F'),rotation,
                                         [0,0,2,0,0,0,1],[1,2,3,0,1,0],[0,0,-9.81])
        self.assertAlmostEqual(result['linear_kinetic_J'],1.75)
        self.assertAlmostEqual(result['rotational_kinetic_J'],.5)
        self.assertAlmostEqual(result['gravitational_J'],4.905)

    def test_solver_override_cannot_modify_an_ordinary_task_run(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'must-not-exist'
            result=subprocess.run([sys.executable,str(PATH),'--policy','demo','--rest-solver','32-8','--log-dir',str(out)],capture_output=True,text=True)
            self.assertEqual(result.returncode,2);self.assertIn('rest-probe',result.stderr);self.assertFalse(out.exists())

    def test_passive_coupon_rejects_camera_mitigation_flags_before_startup(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'must-not-exist'
            result=subprocess.run([sys.executable,str(PATH),'--policy','rest-probe','--render-sync','--log-dir',str(out)],capture_output=True,text=True)
            self.assertEqual(result.returncode,2);self.assertIn('--no-video',result.stderr);self.assertFalse(out.exists())


if __name__=='__main__':unittest.main()
