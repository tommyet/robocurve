"""Controller gates and kinematic feasibility; run in the Arena environment."""
import unittest
from types import SimpleNamespace
from pathlib import Path
import numpy as np
from yam_arena import ik, station, task_file
from yam_arena.constants import READY
from yam_arena.demo import grip_rotation
from demo_policy import ParcelFeedbackPolicy, flap_target, rx
from config import TOP
import telemetry


def initial_sample():
    hands=[]
    for side in ('left','right'):
        p,r=ik.tcp_pose(np.array(READY),station.BASES[side])
        hands.append(dict(tcp=p.tolist(),tcp_rotation=r.tolist(),joints=list(READY),opening=1.))
    return dict(time=0.,hands=hands,flap_angles=[0.,0.],held=False,
                metrics=dict(score=0.,cut_segments=0),flaps={})

class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.task=task_file.load(Path(__file__).with_name('task.py'))
        telemetry.latest=initial_sample();telemetry.events.clear()
        self.policy=ParcelFeedbackPolicy()
        self.policy._bases=station.BASES;self.policy._task=self.task
        self.policy.reset(None);self.policy.initialize()

    def test_incomplete_cut_cannot_enter_opening(self):
        telemetry.latest['metrics']['cut_segments']=20
        t=self.policy.cut_plan.duration+.1;telemetry.latest['time']=t
        chunk=self.policy.act(SimpleNamespace(state_time=t))
        self.assertTrue(chunk.actions[0].meta['request_stop'])
        self.assertEqual(self.policy.phase,'failed')
        self.assertFalse(any(e['kind']=='approach_flap' for e in telemetry.events))

    def test_tool_must_be_released_before_opening(self):
        telemetry.latest['metrics']['cut_segments']=21;telemetry.latest['held']=True
        t=self.policy.cut_plan.duration+.1;telemetry.latest['time']=t
        self.policy.act(SimpleNamespace(state_time=t))
        self.assertEqual(self.policy.phase,'failed')

    def test_stalled_flap_stops_after_bounded_retries(self):
        p=self.policy;p.phase='rotate_flap';p.side='left';p.now=3.
        p.last_angle=0.;p.last_progress=0.;p.rotate_start=0.;p.retries['left']=2
        p.advance()
        self.assertEqual(p.phase,'failed')
        self.assertIn('stalled',p.failure)

    def test_transport_preserves_gripper_preload(self):
        # A loaded jaw remains wider than its commanded gap. Starting a carry
        # from the measured width would release the established contact force.
        p=self.policy
        telemetry.latest['hands'][1]['opening']=.426
        tcp=np.array(telemetry.latest['hands'][1]['tcp'])
        r=np.array(telemetry.latest['hands'][1]['tcp_rotation'])
        p.target['right']=(tcp,r,.405)
        p.move('right',tcp+[.05,0.,0.],r,.405,2.,'item_front')
        p.now=1.;p.advance()
        self.assertEqual(p.target['right'][2],.405)
        self.assertEqual(p.motion['g0'],p.motion['g1'])

    def test_precut_diagnostic_cannot_earn_task_credit(self):
        m=self.task.module;m._tracker=SimpleNamespace(value=1.);m._diagnostic=True
        self.assertFalse(m.success({}));self.assertEqual(m.score({}),0.)
        m._diagnostic=False
        self.assertTrue(m.success({}));self.assertEqual(m.score({}),1.)

    def test_reachable_opening_arc_with_capped_wrist_rotation(self):
        for side in ('left','right'):
            sign=1 if side=='left' else -1
            q=np.array(READY)
            for angle in range(0,109,4):
                pos,_=flap_target(side,angle)
                rot=rx(-sign*min(angle,80.))@grip_rotation()
                q,pe,re=ik.solve(pos,ik.matrix_to_quat_xyzw(rot),q,base_pos=station.BASES[side],iters=150)
                self.assertLess(pe,.0005,(side,angle,pe))
                self.assertLess(re,.002,(side,angle,re))
                self.assertTrue(np.all(q>=ik.LOWER) and np.all(q<=ik.UPPER))

if __name__=='__main__':unittest.main()
