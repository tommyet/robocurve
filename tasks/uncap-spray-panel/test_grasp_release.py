"""Coordinates, physical release evidence and aborts; no simulator required."""
from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType,SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from control_math import (GRASP_OFFSET,GRASP_Z,calibrated_hand_target,grasp_drift,
                          release_target,release_clearance,release_gate_frames)
from config import CAN_REST_HEIGHT,CAN_PAD,CAN_START,CAP_START,TARGET_CENTER


class GraspReleaseTests(unittest.TestCase):
    def test_all_can_goals_and_return_use_one_calibrated_offset(self):
        actual=np.array((.001,-.002,.006))
        origins=[np.array(CAN_START),np.array((CAN_PAD[0],CAN_PAD[1],CAN_REST_HEIGHT))]
        origins.extend(np.array((CAN_START[0],y,TARGET_CENTER[1]-.077+z)) for y,z in ((-.035,-.035),(-.035,.035),(.035,.035),(.035,-.035)))
        self.assertEqual(GRASP_Z,.005)
        for origin in origins:
            hand=calibrated_hand_target(origin+GRASP_OFFSET,actual)
            np.testing.assert_allclose(hand-actual,origin,atol=1e-15)
        self.assertAlmostEqual(origins[1][2],CAN_REST_HEIGHT)

    def test_grasp_drift_angle_offset_tilt_and_nonfinite_fail_closed(self):
        can=np.zeros(3);R=np.eye(3);offset=GRASP_OFFSET.copy()
        self.assertIsNone(grasp_drift(can,R,offset,R,offset,R))
        self.assertIn('offset',grasp_drift(can,R,offset+[.0081,0,0],R,offset,R))
        a=np.radians(15.1);turn=np.array(((np.cos(a),-np.sin(a),0),(np.sin(a),np.cos(a),0),(0,0,1)))
        self.assertIn('relative angle',grasp_drift(can,R,offset,turn,offset,R))
        a=np.radians(25.1);tilt=np.array(((1,0,0),(0,np.cos(a),-np.sin(a)),(0,np.sin(a),np.cos(a))))
        self.assertIn('tilted',grasp_drift(can,tilt,tilt@offset,tilt,offset,R))
        self.assertIn('nonfinite',grasp_drift(can,R,[np.nan,0,0],R,offset,R))

    def test_latched_retreat_is_continuous_and_keeps_achieved_rotation(self):
        start=np.array((.26,0,1.));R=np.array(((0,-1,0),(1,0,0),(0,0,1.)))
        axis=np.array((0,-.5,np.sqrt(.75)))
        previous=start.copy()
        for elapsed in np.arange(0,6,.05):
            p,r=release_target(start,R,axis,float(elapsed))
            self.assertLessEqual(np.linalg.norm(p-previous),.0005+1e-15)
            np.testing.assert_array_equal(r,R);self.assertFalse(np.shares_memory(r,R))
            previous=p
        np.testing.assert_allclose(previous,start+.030*axis)

    def test_release_gate_uses_actual_face_and_button_and_requires_five_frames(self):
        face=json.loads(Path(__file__).with_name('press_face.json').read_text())
        R=np.array(face['rotation_can_from_tcp']);vertices=np.array(face['triangle_tcp'])
        button=np.array((.26,0,.95));axis=np.array((0,0,1.))
        contact=button+.005*axis-R@np.array(face['point_tcp'])
        gap=release_clearance(contact,R,vertices,-.028,button,axis,axis)
        self.assertAlmostEqual(gap,0,delta=1e-8)
        self.assertEqual(release_gate_frames(0.,gap,4),0)
        gap=release_clearance(contact+.021*axis,R,vertices,-.028,button,axis,axis)
        count=0
        for i in range(5):count=release_gate_frames(.00049,gap,count);self.assertEqual(count,i+1)
        self.assertEqual(release_gate_frames(.0005,gap,count),0)
        self.assertEqual(release_gate_frames(0.,.0199,count),0)
        self.assertEqual(release_gate_frames(0.,np.nan,count),0)


def policy_module():
    """Stub only the unavailable action transport; retain real YAM IK."""
    from yam_arena import ik
    @dataclass
    class Info:name:str='test'
    class Base:
        def __init__(self):self.info=Info();self._dt=.05;self._bases={'left':(0,.305,.75),'right':(0,-.305,.75)}
    modules={name:ModuleType(name) for name in ('yam_arena.scripted','inspect_robots','inspect_robots.types','inspect_robots_yam','inspect_robots_yam.packing')}
    modules['yam_arena.scripted'].YamScriptedPolicy=Base
    modules['inspect_robots.types'].Action=SimpleNamespace;modules['inspect_robots.types'].ActionChunk=SimpleNamespace
    modules['inspect_robots_yam.packing'].pack=lambda *actions:np.concatenate(actions)
    spec=importlib.util.spec_from_file_location('_spray_policy_test',Path(__file__).with_name('demo_policy.py'))
    module=importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules,modules):spec.loader.exec_module(module)
    return module


class PolicyGuardTests(unittest.TestCase):
    def setUp(self):
        try:self.module=policy_module()
        except ModuleNotFoundError:self.skipTest('pinned YAM source is required for policy/IK checks')

    def sample(self):
        from yam_arena.constants import READY
        from yam_arena import ik
        hands=[]
        for side in ('left','right'):
            p,r=ik.tcp_pose(np.array(READY),(0,.305 if side=='left' else -.305,.75))
            hands.append(dict(tcp=p.tolist(),rotation=r.tolist(),joints=list(READY),opening=1.,finger_joints=[-.04695]*2))
        return dict(time=0.,hands=hands,can=list(CAN_START),cap=list(CAP_START),can_rotation=np.eye(3).tolist())

    def test_grasp_abort_emits_previous_action_without_solving_new_ik(self):
        sample=self.sample();self.module.telemetry.latest=sample
        policy=self.module.SprayDemo();policy.initialize();policy.grasp_calibrated=True;policy.holding_can=True
        policy.grasp_offset=np.zeros(3);policy.grasp_rotation=np.eye(3)
        previous=np.concatenate(policy.last_actions)
        with patch.object(self.module.ik,'solve',side_effect=AssertionError('must not solve after abort')):
            action=policy.act(SimpleNamespace(state_time=0.))
        self.assertIn('grasp offset',policy.failure);self.assertTrue(action.actions[0].meta['request_stop'])
        np.testing.assert_array_equal(action.actions[0].data,previous)

    def test_new_free_approach_and_cap_paths_fit_initial_ik_guard(self):
        from yam_arena import ik
        sample=self.sample();self.module.telemetry.latest=sample;policy=self.module.SprayDemo();policy.initialize()
        poses=[(np.array(h['tcp']),np.array(h['rotation'])) for h in sample['hands']]
        joints=[np.array(h['joints']) for h in sample['hands']]
        for move in policy.moves:
            if move['label']=='can_lift':break
            for i,key in enumerate(('L','R')):
                if move[key] is None:continue
                end,rotation,_=move[key];start,startR=poses[i]
                for s in np.linspace(0,1,21):
                    p=start+s*(end-start);r=ik.slerp_matrix(startR,rotation,s)
                    q,pe,re=ik.solve(p,ik.matrix_to_quat_xyzw(r),joints[i],base_pos=policy._bases['left' if i==0 else 'right'],iters=90)
                    self.assertLessEqual(pe,.015,(move['label'],pe));self.assertLessEqual(re,.12,(move['label'],re));joints[i]=q
                poses[i]=(end,rotation)

    def test_intentional_opening_and_retreat_disable_only_the_grasp_loss_guard(self):
        sample=self.sample();self.module.telemetry.latest=sample
        policy=self.module.SprayDemo();policy.initialize();policy.grasp_calibrated=True;policy.holding_can=True
        policy.grasp_offset=np.zeros(3);policy.grasp_rotation=np.eye(3)
        for phase in ('can_release','brace_retreat','finish_hold'):
            policy.index=next(i for i,m in enumerate(policy.moves) if m['label']==phase)-1
            policy.next(0.)
            self.assertFalse(policy.holding_can)
            with patch.object(self.module,'grasp_drift',side_effect=AssertionError('intentional release is not grasp loss')),patch.object(self.module.ik,'solve',side_effect=lambda p,r,q,**kw:(q.copy(),0.,0.)):
                policy.act(SimpleNamespace(state_time=0.))
            self.assertIsNone(policy.failure)

    def test_unreachable_paint_ik_returns_previous_action(self):
        sample=self.sample();self.module.telemetry.latest=sample
        policy=self.module.SprayDemo();policy.initialize()
        policy.index=next(i for i,m in enumerate(policy.moves) if m['label']=='press_approach')-1;policy.next(0.)
        previous=np.concatenate(policy.last_actions)
        with patch.object(self.module.ik,'solve',side_effect=lambda p,r,q,**kw:(q.copy(),.006,0.)):
            action=policy.act(SimpleNamespace(state_time=0.))
        self.assertIn('IK exceeds 5 mm',policy.failure)
        self.assertTrue(action.actions[0].meta['request_stop']);np.testing.assert_array_equal(action.actions[0].data,previous)


if __name__=='__main__':unittest.main()
