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
                          release_target,release_clearance,release_gate_frames,release_command_target,MEASURED_DWELL,
                          minimum_future_seconds,press_contact_state,press_bias_step)
from config import CAN_REST_HEIGHT,CAN_PAD,CAN_START,CAP_START,TARGET_CENTER,SPRAY_TRANSIT_CAN,SPRAY_HELD_CAN


class GraspReleaseTests(unittest.TestCase):
    def contact_sample(self):
        matrix=np.zeros((9,5,3));matrix[7,1,2]=3.5
        return dict(right_contact_matrix=matrix.tolist(),hands=[{},dict(tcp=[0,0,.005],rotation=np.eye(3).tolist(),finger_joints=[-.028,-.028])],
                    can_rotation=np.eye(3).tolist(),button=[0,0,0],button_travel=.0018)

    def test_extra_press_budget_requires_real_contact_margin_and_rate_limit(self):
        sample=self.contact_sample();contact=press_contact_state(sample,np.zeros(3));self.assertTrue(contact['extra_pressure_allowed'])
        bias=np.array((0.,0.,-.020))
        updated=press_bias_step(bias,[0,0,-.01],.05,contact)
        self.assertAlmostEqual(updated[2],-.02025)
        for _ in range(80):
            previous=updated.copy();updated=press_bias_step(updated,[1.,-1.,-.01],.05,contact)
            self.assertLessEqual(previous[2]-updated[2],.00025+1e-15)
        np.testing.assert_allclose(updated,[.020,-.020,-.030])
        self.assertAlmostEqual(press_bias_step([0,0,0],[0,0,1],.05,contact)[2],.020)
        for field,value in (('force',.1),('radius',.0076),('travel',.0027)):
            changed=self.contact_sample()
            if field=='force':changed['right_contact_matrix'][7][1][2]=value
            if field=='radius':changed['hands'][1]['tcp'][0]=value
            if field=='travel':changed['button_travel']=value
            denied=press_contact_state(changed,np.zeros(3));self.assertFalse(denied['extra_pressure_allowed'])
            np.testing.assert_array_equal(press_bias_step(bias,[0,0,-.01],.05,denied),bias)

    def test_contact_gate_drop_keeps_accumulated_bias_and_allows_unwind(self):
        sample=self.contact_sample();sample['right_contact_matrix'][7][1][2]=0.
        contact=press_contact_state(sample,np.zeros(3));bias=np.array((0.,0.,-.025))
        np.testing.assert_array_equal(press_bias_step(bias,[0,0,-.01],.05,contact),bias)
        self.assertGreater(press_bias_step(bias,[0,0,.01],.05,contact)[2],bias[2])
        sample['button_travel']=.0027;contact=press_contact_state(sample,np.zeros(3))
        np.testing.assert_array_equal(press_bias_step(bias,[0,0,-.01],.05,contact),bias)
        self.assertGreater(press_bias_step(bias,[0,0,.01],.05,contact)[2],bias[2])

    def test_native_pressure_limits_missing_and_nonfinite_state_fail_closed(self):
        for mode in ('button8','unexpected','missing','nonfinite'):
            sample=self.contact_sample()
            if mode=='button8':sample['right_contact_matrix'][7][1][2]=8.
            if mode=='unexpected':sample['right_contact_matrix'][7][2][0]=1.001
            if mode=='missing':del sample['right_contact_matrix']
            if mode=='nonfinite':sample['right_contact_matrix'][7][1][2]=np.nan
            with self.subTest(mode=mode),self.assertRaises(ValueError):press_contact_state(sample,np.zeros(3))

    def test_future_budget_reserves_required_work_not_failure_deadlines(self):
        future=[dict(label='coat_shot_2',follow='press',seconds=8.),dict(label='coat_unpress_2',follow='release',seconds=10.),dict(label='can_lower',follow=False,seconds=3.)]
        self.assertAlmostEqual(minimum_future_seconds(future),1.+3.+2.8+.5+3.)

    def test_all_can_goals_and_return_use_one_calibrated_offset(self):
        actual=np.array((.001,-.002,.006))
        origins=[np.array(CAN_START),np.array((CAN_PAD[0],CAN_PAD[1],CAN_REST_HEIGHT))]
        origins.extend(np.array(p) for p in (SPRAY_TRANSIT_CAN,SPRAY_HELD_CAN))
        self.assertEqual(GRASP_Z,-.010)
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

    def test_transported_release_preserves_actual_face_gap_when_can_rises(self):
        from control_math import transport_can_reference
        face=json.loads(Path(__file__).with_name('press_face.json').read_text())
        pressR=np.array(face['rotation_can_from_tcp']);point=np.array(face['point_tcp']);tri=np.array(face['triangle_tcp'])
        C=np.array((.26,0,.8675));button=C+[0,0,.077]
        tcp=button+[0,0,.005+.025]-pressR@point
        a=.03;R=np.array(((1,0,0),(0,np.cos(a),-np.sin(a)),(0,np.sin(a),np.cos(a))))
        nowC=C+[0,0,.010];nowButton=nowC+R@np.array((0,0,.077));axis=R[:,2]
        moved,movedR=transport_can_reference(tcp,pressR,(C,np.eye(3)),(nowC,R))
        gap=release_clearance(moved,movedR,tri,-.028,nowButton,axis,axis)
        self.assertAlmostEqual(gap,.025,delta=1e-8)
        self.assertLess(release_clearance(tcp,pressR,tri,-.028,nowButton,axis,axis),.020)

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

    def test_command_path_unloads_inherited_offset_under_same_rate_limit(self):
        actual=np.array((.26,0.,1.));command=actual-[0,0,.0245529];goal=actual+[0,0,.03]
        previous=command.copy()
        for elapsed in np.arange(0.,5.6,.05):
            p,fraction,duration=release_command_target(command,goal,float(elapsed))
            self.assertLessEqual(np.linalg.norm(p-previous),.0005+1e-15);previous=p
        self.assertAlmostEqual(duration,5.45529);np.testing.assert_array_equal(previous,goal)
        self.assertLessEqual(duration+2.8+.5,9.)


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
        return dict(time=0.,hands=hands,can=list(CAN_START),cap=list(CAP_START),can_rotation=np.eye(3).tolist(),metrics=dict(score=0.),
                    button=[CAN_START[0],CAN_START[1],CAN_START[2]+.077],button_travel=0.,
                    nozzle=[.27,*TARGET_CENTER],axis=[1.,0.,0.],right_contact_matrix=np.zeros((9,5,3)).tolist())

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

    def test_yawed_grip_entry_and_all_left_waypoints_keep_safe_side_and_ik(self):
        from yam_arena import ik
        sample=self.sample();self.module.telemetry.latest=sample
        policy=self.module.SprayDemo();policy.initialize();moves={m['label']:m for m in policy.moves}
        R=self.module.LEFT_R
        np.testing.assert_array_equal(R[:,0],(0.,-1.,0.))
        self.assertAlmostEqual(R[2,2],-np.sin(np.radians(15.)))
        np.testing.assert_allclose(R.T@R,np.eye(3),atol=1e-15);self.assertAlmostEqual(np.linalg.det(R),1.)
        grasp=np.array(sample['can'])+GRASP_OFFSET
        placement=np.array((CAN_PAD[0],CAN_PAD[1],CAN_REST_HEIGHT))+GRASP_OFFSET
        np.testing.assert_allclose(moves['brace_approach']['L'][0],grasp+(-.060,0,.015))
        np.testing.assert_allclose(moves['brace_enter']['L'][0],grasp)
        # Front entry avoids sweeping open jaws across the can.
        self.assertLess(moves['brace_approach']['L'][0][0],grasp[0])
        start=np.array(sample['hands'][0]['tcp']);startR=np.array(sample['hands'][0]['rotation'])
        seed=np.array(sample['hands'][0]['joints'])
        for move in policy.moves:
            if move['L'] is None:continue
            end,rotation,_=move['L'];np.testing.assert_array_equal(rotation,R)
            for fraction in np.linspace(0,1,21):
                p=start+fraction*(end-start);r=ik.slerp_matrix(startR,rotation,fraction)
                seed,pe,re=ik.solve(p,ik.matrix_to_quat_xyzw(r),seed,base_pos=policy._bases['left'],iters=90)
                # Actual existing phase guard, including READY approach interpolation.
                early=move['label'].startswith('brace_')
                self.assertLessEqual(pe,.015 if early else .005,(move['label'],fraction,pe))
                self.assertLessEqual(re,.12 if early else .05,(move['label'],fraction,re))
                if fraction==1:self.assertLessEqual(pe,.0001,(move['label'],pe))
            start,startR=end,rotation

    def test_recorded_022_biased_command_has_joint_reserve_with_pitched_lower_grasp(self):
        from yam_arena import ik
        from yam_arena.urdf import axis_angle_matrix
        # Actual022 command rejected at29.05s: retain measured calibration and
        # accumulated correction, rather than testing only an unbiased waypoint.
        position=np.array((.2608570172620284,-.033393422571934075,.893862970657222))
        calibration=np.array(((-.006325689825803152,.0629604703781418,.9979959743495916),
                              (-.9999780533379853,-.002363795929586545,-.00618912846662249),
                              (.0019693883824218714,-.9980132221762228,.06297404124584018)))
        rv=np.array((-.044323377968408136,-.020497574595067097,-.004246474684677953))
        correction=axis_angle_matrix(rv/np.linalg.norm(rv),np.linalg.norm(rv))
        seed=np.array((-1.3033600556251954,2.1399736057875387,.8032035034966832,1.5708,-1.2845804946639516,.2219040002314723))
        oldR=correction@calibration
        _,old_pe,_=ik.solve(position,ik.matrix_to_quat_xyzw(oldR),seed,base_pos=(0,.305,.75),iters=90)
        self.assertGreater(old_pe,.005)
        old_nominal=np.array(((0.,0.,1.),(-1.,0.,0.),(0.,-1.,0.)))
        posture_change=self.module.LEFT_R@old_nominal.T
        newR=correction@posture_change@calibration
        position[2]+=GRASP_Z-.005
        q,pe,re=ik.solve(position,ik.matrix_to_quat_xyzw(newR),seed,base_pos=(0,.305,.75),iters=90)
        self.assertLess(pe,.0001);self.assertLess(re,.001)
        self.assertGreater(ik.UPPER[3]-q[3],np.radians(60.))
        self.assertGreater(np.min(np.minimum(q-ik.LOWER,ik.UPPER-q)),np.radians(10.))

    def test_single_plaque_sequence_preserves_transit_and_finishes_held(self):
        sample=self.sample();self.module.telemetry.latest=sample;policy=self.module.SprayDemo();policy.initialize()
        moves={m['label']:m for m in policy.moves};labels=list(moves)
        self.assertEqual([x for x in labels if x.startswith('coat_position_')],['coat_position_0'])
        self.assertEqual([x for x in labels if x.startswith('coat_shot_')],['coat_shot_0'])
        self.assertEqual([x for x in labels if x.startswith('coat_unpress_')],['coat_unpress_0'])
        self.assertLess(labels.index('cap_retreat'),labels.index('coat_position_0'))
        self.assertEqual(labels[-3:],['finish_coating','press_retreat','finish_hold'])
        self.assertFalse(any(label in labels for label in ('can_lower','can_release','brace_retreat')))
        self.assertTrue(all(m['L'] is None for m in policy.moves[labels.index('coat_unpress_0'):]))
        np.testing.assert_allclose(moves['can_lift']['L'][0]-GRASP_OFFSET,(.26,0,.9105))
        np.testing.assert_allclose(moves['coat_position_0']['L'][0]-GRASP_OFFSET,(.26,-.035,.8755))
        np.testing.assert_allclose(moves['press_approach']['R'][0],np.array((.26,0,.9105))+(0,-.08,.14))
        np.testing.assert_allclose(moves['press_retreat']['R'][0],np.array((.26,0,.9105))+(0,-.09,.07))
        self.assertEqual(moves['coat_aim_0']['aim'],TARGET_CENTER);self.assertEqual(moves['coat_shot_0']['aim'],TARGET_CENTER)
        self.assertEqual(moves['coat_shot_0']['seconds'],8.)

    def test_initial_grip_is_unchanged_and_loaded_hold_ramps_over_existing_lift(self):
        from yam_arena.constants import FINGER_OPEN,GRIPPER
        sample=self.sample();self.module.telemetry.latest=sample
        policy=self.module.SprayDemo();policy.initialize()
        moves={move['label']:move for move in policy.moves}
        self.assertAlmostEqual(moves['brace_grip']['L'][2]*FINGER_OPEN,-.021)
        self.assertAlmostEqual(moves['cap_grip']['R'][2]*FINGER_OPEN,-.025)
        self.assertEqual(moves['can_lift']['seconds'],2.)
        for phase in ('can_lift','coat_position_0'):
            self.assertAlmostEqual(moves[phase]['L'][2]*FINGER_OPEN,-.018)
        self.assertIsNone(moves['finish_hold']['L'])
        # Exercise the actual policy interpolation rather than a duplicated ramp.
        policy.targets[0][2]=policy.grip
        policy.index=next(i for i,m in enumerate(policy.moves) if m['label']=='can_lift')-1;policy.next(0.)
        policy.holding_can=False # Synthetic kinematics isolate the command ramp.
        previous=-.021;values=[]
        with patch.object(self.module.ik,'solve',side_effect=lambda p,r,q,**kw:(q.copy(),0.,0.)):
            for i in range(40):
                sample['time']=i*.05;action=policy.act(SimpleNamespace(state_time=sample['time']))
                command=action.actions[0].data[6]*FINGER_OPEN
                self.assertGreaterEqual(command,previous-1e-15);self.assertLessEqual(command,-.018+1e-15)
                self.assertLessEqual(command-previous,.003*1.5*.05/2.+1e-15)
                self.assertAlmostEqual(self.module.telemetry.command['left_command_finger_joint_m'],command)
                previous=command;values.append(command)
        self.assertLess(values[0],-.0209);self.assertAlmostEqual(values[-1],-.018)
        self.assertEqual(GRIPPER['effort'],50.)

    def test_held_finish_keeps_original_grasp_guard_active(self):
        sample=self.sample();self.module.telemetry.latest=sample
        policy=self.module.SprayDemo();policy.initialize();policy.grasp_calibrated=True;policy.holding_can=True
        policy.grasp_offset=np.zeros(3);policy.grasp_rotation=np.eye(3)
        policy.index=next(i for i,m in enumerate(policy.moves) if m['label']=='finish_hold')-1;policy.next(0.)
        self.assertTrue(policy.holding_can)
        with patch.object(self.module.ik,'solve',side_effect=AssertionError('must stop before new command')):
            action=policy.act(SimpleNamespace(state_time=0.))
        self.assertIn('grasp offset',policy.failure);self.assertTrue(action.actions[0].meta['request_stop'])

    def test_unreachable_paint_ik_returns_previous_action(self):
        sample=self.sample();self.module.telemetry.latest=sample
        policy=self.module.SprayDemo();policy.initialize()
        policy.index=next(i for i,m in enumerate(policy.moves) if m['label']=='press_approach')-1;policy.next(0.)
        previous=np.concatenate(policy.last_actions)
        with patch.object(self.module.ik,'solve',side_effect=lambda p,r,q,**kw:(q.copy(),.006,0.)):
            action=policy.act(SimpleNamespace(state_time=0.))
        self.assertIn('IK exceeds 5 mm',policy.failure)
        self.assertTrue(action.actions[0].meta['request_stop']);np.testing.assert_array_equal(action.actions[0].data,previous)

    def test_final_settle_holds_valid_commands_without_replanning_retreat_ik(self):
        sample=self.sample();sample['metrics']['score']=.75;self.module.telemetry.latest=sample
        policy=self.module.SprayDemo();policy.initialize()
        policy.index=next(i for i,m in enumerate(policy.moves) if m['label']=='finish_hold')-1;policy.next(0.)
        previous=np.concatenate(policy.last_actions);bias=[b.copy() for b in policy.position_bias]
        with patch.object(self.module.ik,'solve',side_effect=AssertionError('settling must retain previous valid joints')):
            for now in (0.,1.,2.5):
                sample['time']=now;action=policy.act(SimpleNamespace(state_time=now))
                np.testing.assert_array_equal(action.actions[0].data,previous)
                self.assertFalse(action.actions[0].meta.get('request_stop',False))
            sample['metrics']['score']=1.;sample['time']=2.55
            action=policy.act(SimpleNamespace(state_time=2.55))
        self.assertTrue(action.actions[0].meta['request_stop']);self.assertIsNone(policy.failure)
        for actual,expected in zip(policy.position_bias,bias):np.testing.assert_array_equal(actual,expected)

    def test_final_settle_timeout_does_not_claim_completion(self):
        sample=self.sample();sample['metrics']['score']=.75;self.module.telemetry.latest=sample
        policy=self.module.SprayDemo();policy.initialize()
        policy.index=next(i for i,m in enumerate(policy.moves) if m['label']=='finish_hold')-1;policy.next(0.)
        sample['time']=6.
        with patch.object(self.module.ik,'solve',side_effect=AssertionError('timeout must stop')):
            action=policy.act(SimpleNamespace(state_time=6.))
        self.assertIn('parking conditions',policy.failure);self.assertTrue(action.actions[0].meta['request_stop'])

    def test_outer_aim_gain_hard_cap_and_tiny_error_have_no_deadband(self):
        for error,expected in (((.001,-.002),(.00005,-.0001)),((.1,-.1),(.000175,-.000175)),
                               ((1e-8,-1e-8),(5e-10,-5e-10)),((0.,0.),(0.,0.))):
            with self.subTest(error=error):
                sample=self.sample();self.module.telemetry.latest=sample;policy=self.module.SprayDemo();policy.initialize()
                policy.index=next(i for i,m in enumerate(policy.moves) if m['label']=='coat_aim_0')-1;policy.next(0.)
                aim=np.array(policy.moves[policy.index]['aim']);sample['axis']=[1.,0.,0.]
                sample['nozzle']=[.27,*(aim-np.array(error))]
                before=policy.targets[0][0].copy()
                with patch.object(self.module.ik,'solve',side_effect=lambda p,r,q,**kw:(q.copy(),0.,0.)):
                    policy.act(SimpleNamespace(state_time=0.))
                np.testing.assert_allclose(policy.targets[0][0],before+np.array((0.,*expected)),atol=1e-15)
                self.assertLessEqual(max(abs(policy.targets[0][0][1:]-before[1:])),.000175+1e-15)

    def test_outer_aim_full_position_response_for_steady_and_followed_error(self):
        # Exercise actual target integration, with the action transport/IK only
        # stubbed. Fixed measured error must remain restorative at each tick.
        for follows in (False,True):
            sample=self.sample();self.module.telemetry.latest=sample;policy=self.module.SprayDemo();policy.initialize()
            policy.index=next(i for i,m in enumerate(policy.moves) if m['label']=='coat_aim_0')-1;policy.next(0.)
            aim=np.array(policy.moves[policy.index]['aim']);initial=np.array((.003,-.002));error=initial.copy()
            start=policy.targets[0][0].copy();sample['axis']=[1.,0.,0.]
            with patch.object(self.module.ik,'solve',side_effect=lambda p,r,q,**kw:(q.copy(),0.,0.)):
                for tick in range(20):
                    sample['nozzle']=[.27,*(aim-error)];sample['time']=tick*.05
                    policy.act(SimpleNamespace(state_time=sample['time']))
                    if follows:error=initial-(policy.targets[0][0][1:]-start[1:])
            accumulated=initial*(1-.95**20) if follows else initial*.05*20
            np.testing.assert_allclose(policy.targets[0][0],start+np.array((0.,*accumulated)),atol=1e-14)
            self.assertIsNone(policy.failure)

    def test_follow_uses_actual_face_point_but_keeps_desired_rotation_and_relative_ramp(self):
        sample=self.sample();self.module.telemetry.latest=sample;policy=self.module.SprayDemo();policy.initialize()
        a=.10;actualR=np.array(((1,0,0),(0,np.cos(a),-np.sin(a)),(0,np.sin(a),np.cos(a))))@self.module.PRESS_R
        sample['hands'][1]['rotation']=actualR.tolist();sample['hands'][1]['finger_joints'][0]=-.030
        policy.index=next(i for i,m in enumerate(policy.moves) if m['label']=='press_hover')-1;policy.next(0.)
        start=policy.targets[1][0].copy();point=self.module.PRESS_POINT.copy();point[0]+=-.030+.028
        expected_goal=np.array(sample['can'])+[0,0,.105]-actualR@point
        with patch.object(self.module.ik,'solve',side_effect=lambda p,r,q,**kw:(q.copy(),0.,0.)):
            policy.act(SimpleNamespace(state_time=0.))
        expected=np.array(self.module.can_frame_ramp_translation(start,expected_goal,None,(sample['can'],np.eye(3)),.1,.05))
        np.testing.assert_allclose(policy.targets[1][0],expected,atol=1e-15)
        np.testing.assert_allclose(policy.targets[1][1],self.module.PRESS_R,atol=1e-15)
        self.assertLessEqual(np.linalg.norm(expected-start),.005+1e-15)
        diag=self.module.telemetry.command
        self.assertIsNone(diag['witness_tangential_velocity_can_m_s']);self.assertIn('not contact center',diag['witness_velocity_scope'])
        sample['time']=.05;sample['hands'][1]['tcp'][0]+=.001
        with patch.object(self.module.ik,'solve',side_effect=lambda p,r,q,**kw:(q.copy(),0.,0.)):
            policy.act(SimpleNamespace(state_time=.05))
        np.testing.assert_allclose(self.module.telemetry.command['witness_tangential_velocity_can_m_s'],(.02,0),atol=1e-12)
        self.assertAlmostEqual(self.module.telemetry.command['selected_face_plane_angle_deg'],np.degrees(a),places=6)

    def test_follow_pose_persists_between_hover_press_and_clears_on_nonfollow(self):
        sample=self.sample();self.module.telemetry.latest=sample
        policy=self.module.SprayDemo();policy.initialize();self.assertIsNone(policy.follow_can_pose)
        pose=(np.array(sample['can']),np.eye(3));policy.follow_can_pose=pose
        for label in ('press_hover','coat_position_0','coat_aim_0','coat_shot_0'):
            policy.index=next(i for i,m in enumerate(policy.moves) if m['label']==label)-1;policy.next(0.)
            self.assertIs(policy.follow_can_pose,pose)
        policy.index=next(i for i,m in enumerate(policy.moves) if m['label']=='press_retreat')-1;policy.next(0.)
        self.assertIsNone(policy.follow_can_pose)

    def test_release_entry_preserves_motor_command_without_larger_integral(self):
        sample=self.sample();self.module.telemetry.latest=sample
        policy=self.module.SprayDemo();policy.initialize()
        original_q=policy.q[1].copy();commandp,commandR=self.module.ik.tcp_pose(original_q,policy._bases['right'])
        sample['hands'][1]['tcp']=(commandp+[0,0,.0245529]).tolist()
        policy.position_bias[1][:]=[0,0,-.02]
        policy.follow_can_pose=(np.array([1.,2.,3.]),np.eye(3))
        policy.index=next(i for i,m in enumerate(policy.moves) if m['label']=='coat_unpress_0')-1;policy.next(0.)
        self.assertIsNone(policy.failure)
        self.assertIsNone(policy.follow_can_pose)
        self.assertAlmostEqual(policy.release_path['duration'],5.45529)
        self.assertAlmostEqual(policy.moves[policy.index]['seconds'],5.45529+2.8+.5)
        with patch.object(self.module.ik,'solve',side_effect=lambda p,r,q,**kw:(q.copy(),0.,0.)) as solve:
            action=policy.act(SimpleNamespace(state_time=0.))
            self.assertEqual(solve.call_count,1) # Right first action reuses q exactly.
        np.testing.assert_array_equal(action.actions[0].data[7:13],original_q)
        np.testing.assert_array_equal(policy.position_bias[1],np.zeros(3));np.testing.assert_array_equal(policy.rotation_bias[1],np.zeros(3))
        sample['time']=.05
        with patch.object(self.module.ik,'solve',side_effect=lambda p,r,q,**kw:(q.copy(),0.,0.)) as solve:
            policy.act(SimpleNamespace(state_time=.05))
        expected,_,_=release_command_target(policy.release_path['start'],policy.release_path['goal'],.05)
        np.testing.assert_allclose(solve.call_args_list[-1].args[0],expected,atol=1e-15)
        self.assertIsNone(policy.follow_can_pose)
        np.testing.assert_array_equal(policy.position_bias[1],np.zeros(3))

    def test_release_tracks_can_motion_without_integral_or_entry_command_change(self):
        from control_math import transport_can_reference
        sample=self.sample();self.module.telemetry.latest=sample
        policy=self.module.SprayDemo();policy.initialize();initial_q=policy.q[1].copy()
        policy.position_bias[1][:]=(0,0,-.028)
        policy.index=next(i for i,m in enumerate(policy.moves) if m['label']=='coat_unpress_0')-1;policy.next(0.)
        entryC=np.array(sample['can']);entryR=np.array(sample['can_rotation'])
        with patch.object(self.module.ik,'solve',side_effect=lambda p,r,q,**kw:(q.copy(),0.,0.)):
            action=policy.act(SimpleNamespace(state_time=0.))
        np.testing.assert_array_equal(action.actions[0].data[7:13],initial_q)
        a=.03;canR=np.array(((1,0,0),(0,np.cos(a),-np.sin(a)),(0,np.sin(a),np.cos(a))))
        sample['can']=(entryC+[0,.002,.010]).tolist();sample['can_rotation']=canR.tolist();sample['time']=.05
        with patch.object(self.module.ik,'solve',side_effect=lambda p,r,q,**kw:(q.copy(),0.,0.)) as solve:
            policy.act(SimpleNamespace(state_time=.05))
        path=policy.release_path;p,f,_=release_command_target(path['start'],path['goal'],.05)
        r=self.module.ik.slerp_matrix(path['rotation'],path['goal_rotation'],f)
        expected,expectedR=transport_can_reference(p,r,(entryC,entryR),(sample['can'],canR))
        np.testing.assert_allclose(solve.call_args_list[-1].args[0],expected,atol=1e-15)
        np.testing.assert_allclose(self.module.ik.quat_xyzw_to_matrix(solve.call_args_list[-1].args[1]),expectedR,atol=1e-12)
        np.testing.assert_array_equal(policy.position_bias[1],np.zeros(3));np.testing.assert_array_equal(policy.rotation_bias[1],np.zeros(3))
        self.assertIsNone(policy.follow_can_pose)

    def test_first_shot_failure_is_not_overwritten_or_advanced(self):
        sample=self.sample();self.module.telemetry.latest=sample
        policy=self.module.SprayDemo();policy.initialize()
        policy.index=next(i for i,m in enumerate(policy.moves) if m['label']=='coat_shot_0')-1;policy.next(0.)
        previous=np.concatenate(policy.last_actions);index=policy.index;sample['time']=8.
        with patch.object(policy,'next',wraps=policy.next) as advance,patch.object(self.module.ik,'solve',side_effect=AssertionError('failed shot must stop')):
            action=policy.act(SimpleNamespace(state_time=8.))
        self.assertEqual(policy.failure,'insufficient measured spray contact');self.assertEqual(policy.index,index);advance.assert_not_called()
        np.testing.assert_array_equal(action.actions[0].data,previous)
        policy.next(9.);self.assertEqual(policy.index,index);self.assertEqual(policy.failure,'insufficient measured spray contact')

    def test_measured_dwell_is_seconds_and_requires_sixteen_qualified_ticks(self):
        self.assertEqual(MEASURED_DWELL,.8)
        sample=self.sample();sample['button_travel']=.0027;self.module.telemetry.latest=sample
        policy=self.module.SprayDemo();policy.initialize()
        policy.index=next(i for i,m in enumerate(policy.moves) if m['label']=='coat_shot_0')-1;policy.next(0.)
        with patch.object(self.module.ik,'solve',side_effect=lambda p,r,q,**kw:(q.copy(),0.,0.)):
            for i in range(16):
                sample['time']=1.+i*.05;policy.act(SimpleNamespace(state_time=sample['time']))
                self.assertAlmostEqual(policy.contact_time,(i+1)*.05)
                self.assertEqual(policy.moves[policy.index]['label'],'coat_unpress_0' if i==15 else 'coat_shot_0')

    def test_release_path_budget_is_bounded_by_unchanged_episode_limit(self):
        sample=self.sample();self.module.telemetry.latest=sample;policy=self.module.SprayDemo();policy.initialize()
        self.assertLess(minimum_future_seconds(policy.moves)+len(policy.moves)*policy._dt,120.)
        sample['hands'][1]['tcp'][2]+=1.
        policy.index=next(i for i,m in enumerate(policy.moves) if m['label']=='coat_unpress_0')-1
        policy.next(0.);self.assertIn('120 second episode budget',policy.failure)

    def test_hard_120s_stop_precedes_new_action_even_before_first_phase(self):
        sample=self.sample();self.module.telemetry.latest=sample;policy=self.module.SprayDemo();policy.initialize()
        previous=np.concatenate(policy.last_actions);sample['time']=120.
        with patch.object(policy,'next',side_effect=AssertionError('must not enter another phase')),patch.object(self.module.ik,'solve',side_effect=AssertionError('must not issue new IK')):
            action=policy.act(SimpleNamespace(state_time=120.))
        self.assertIn('120 second episode limit',policy.failure)
        self.assertTrue(action.actions[0].meta['request_stop']);np.testing.assert_array_equal(action.actions[0].data,previous)

    def test_even_minimum_future_work_rejects_impossible_release_budget(self):
        sample=self.sample();self.module.telemetry.latest=sample;policy=self.module.SprayDemo();policy.initialize()
        policy.index=next(i for i,m in enumerate(policy.moves) if m['label']=='coat_unpress_0')-1
        policy.next(115.)
        self.assertIn('remaining 120 second episode budget',policy.failure)


if __name__=='__main__':unittest.main()
