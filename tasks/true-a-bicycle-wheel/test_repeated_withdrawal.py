import copy
import unittest
import numpy as np
from tool_pose_servo import ToolPoseServo

class RepeatedWithdrawalTests(unittest.TestCase):
    def plan(self):
        return dict(held_grasp_calibration=dict(tcp_position_in_tool_m=[0.,-.195,.011],tcp_rotation_in_tool=np.eye(3).tolist(),applies_from_step=1),
            frames=[{}]*100,measured_axial_withdrawal=dict(from_step=20,move_through_step=30,through_step=40,distance_m=.016),
            additional_measured_axial_withdrawals=[dict(from_step=60,move_through_step=70,through_step=80,distance_m=.016)])
    def test_distinct_releases_keep_separate_native_latches(self):
        servo=ToolPoseServo(self.plan())
        self.assertEqual([x['from_step'] for x in servo.withdrawals],[20,60])
        self.assertIsNone(servo.withdrawal_start)
    def test_overlapping_or_truncated_releases_are_rejected(self):
        for updates in ({'from_step':40},{'through_step':101},{'move_through_step':59}):
            p=self.plan();p['additional_measured_axial_withdrawals'][0].update(updates)
            with self.assertRaises(ValueError):ToolPoseServo(p)
    def test_changed_reference_is_a_rigid_transform_and_ordered(self):
        p=self.plan();new=copy.deepcopy(p['held_grasp_calibration']);new['applies_from_step']=50;p['additional_grasp_calibrations']=[new]
        self.assertEqual(len(ToolPoseServo(p).references),2)
        for bad in (dict(applies_from_step=1),dict(tcp_rotation_in_tool=np.zeros((3,3)).tolist())):
            q=copy.deepcopy(p);q['additional_grasp_calibrations'][0].update(bad)
            with self.assertRaises(ValueError):ToolPoseServo(q)
