"""Passive rest initialization and native energy protocol; no physics startup."""
import importlib.util
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
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

    def test_timestep_selection_restores_adapter_global_and_keeps_twenty_hz_control(self):
        # Execute the actual pinned adapter callback body without loading Isaac.
        import ast
        import yam_arena
        source=Path(yam_arena.__file__).with_name('scene.py').read_text()
        tree=ast.parse(source);callback=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='env_cfg_callback')
        namespace=dict(PHYSICS_DT=1/240,DECIMATION=24,RENDER_INTERVAL=24,
                       make_configclass=lambda *a:lambda:None,
                       RecorderManagerBaseCfg=lambda **kw:None,DatasetExportMode=SimpleNamespace(EXPORT_NONE=0),
                       VisualizerCfg=lambda **kw:None,WINDOW_EYE=(0,0,0),WINDOW_LOOKAT=(0,0,0))
        exec(compile(ast.Module(body=[callback],type_ignores=[]),'<pinned env_cfg_callback>','exec'),namespace)
        class SceneProxy:
            @property
            def PHYSICS_DT(self):return namespace['PHYSICS_DT']
            @PHYSICS_DT.setter
            def PHYSICS_DT(self,value):namespace['PHYSICS_DT']=value
        scene=SceneProxy()
        for hz,decimation in ((240,12),(960,48)):
            with runner.physics_timestep(scene,hz):
                cfg=SimpleNamespace(sim=SimpleNamespace())
                namespace['env_cfg_callback'](control_hz=20)(cfg)
                base=SimpleNamespace(cfg=cfg,step_dt=cfg.sim.dt*cfg.decimation)
                result=runner.physics_timing_readback(base,hz)
                self.assertEqual(result['decimation'],decimation)
                self.assertAlmostEqual(result['control_dt_s'],.05)
            self.assertEqual(scene.PHYSICS_DT,1/240)
        with self.assertRaisesRegex(RuntimeError,'construction failed'):
            with runner.physics_timestep(scene,960):raise RuntimeError('construction failed')
        self.assertEqual(scene.PHYSICS_DT,1/240)
        with self.assertRaisesRegex(RuntimeError,'timing readback'):
            runner.physics_timing_readback(base,240)

    def test_unsupported_physics_rate_rejected_before_output_or_simulation(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'must-not-exist'
            result=subprocess.run([sys.executable,str(PATH),'--physics-hz','480','--log-dir',str(out)],capture_output=True,text=True)
            self.assertEqual(result.returncode,2);self.assertIn('invalid choice',result.stderr);self.assertFalse(out.exists())

    def test_contact_reporting_options_are_opt_in_and_cannot_enable_on_full_task(self):
        defaults=dict(track_contact_points=False,track_friction_forces=False,max_contact_data_count_per_prim=4)
        configs=[SimpleNamespace(**defaults),SimpleNamespace(**defaults)]
        runner.configure_contact_diagnostic(configs,False)
        for cfg in configs:self.assertEqual(vars(cfg),defaults)
        runner.configure_contact_diagnostic(configs,True)
        for cfg in configs:self.assertEqual(vars(cfg),dict(track_contact_points=True,track_friction_forces=True,max_contact_data_count_per_prim=64))
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'must-not-exist'
            result=subprocess.run([sys.executable,str(PATH),'--policy','demo','--stage','full','--contact-diagnostic','--log-dir',str(out)],capture_output=True,text=True)
            self.assertEqual(result.returncode,2);self.assertIn('unscored',result.stderr);self.assertFalse(out.exists())

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
