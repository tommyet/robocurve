"""Screen the relocated route against fixed measured wheel/grasp examples.

This is a counterfactual CPU check, not a rollout or prediction of contact.
It uses every future command, actual robot hulls and the authored fixture.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from motion_plan import load
from fixture_layout import RELOCATED, offset
from tool_pose_servo import ToolPoseServo
from thread_coupling import rotation
from wheel_scene import quat


def screen(plan_path, trace_path):
    from yam_arena import ik, station
    from yam_arena.analysis import link_hulls
    from audit_native_trace import inspect
    plan, _ = load(plan_path)
    if plan.get('fixture_layout') != RELOCATED:
        raise ValueError('Expected the explicitly relocated candidate')
    with gzip.open(trace_path, 'rt') as stream:
        rows = {row['step']: row for row in map(json.loads, stream)}
    hulls = link_hulls()
    reports = []
    for fixture_step, grasp_step in ((148, 84), (174, 174)):
        reference = rows[fixture_step]
        poses = np.asarray(reference['body_poses']).copy()
        wi = reference['body_names'].index('wrench')
        ni = reference['body_names'].index('wheel/nipple_00')
        for index, name in enumerate(reference['body_names']):
            if name.startswith('wheel/'):
                poses[index, :3] += offset(RELOCATED)
        source = rows[grasp_step]
        actual = np.asarray(source['body_poses'][wi])
        p, R = ik.tcp_pose(np.asarray(source['joint_pos'])[7:13], station.BASES['right'])
        tool_R = rotation(actual[3:])
        gp, gR = tool_R.T@(p-actual[:3]), tool_R.T@R
        servo = ToolPoseServo(plan, nipple_feedback=True)
        q = np.asarray(plan['frames'][81]['action14'])
        samples, failure = [], None
        for step in range(83, len(plan['frames'])+1):
            p, R = ik.tcp_pose(q[7:13], station.BASES['right'])
            tool_R = R@gR.T
            tool_p = p-tool_R@gp
            try:
                q = servo.command(step, plan['frames'][step-1]['action14'], q,
                                  np.r_[tool_p, quat(tool_R)], poses[ni])
            except Exception as error:
                failure = dict(step=step, stage=plan['frames'][step-1]['stage'], error=str(error))
                break
            p, R = ik.tcp_pose(q[7:13], station.BASES['right'])
            tool_R = R@gR.T
            tool_p = p-tool_R@gp
            bodies = poses.copy()
            bodies[wi] = np.r_[tool_p, quat(tool_R)]
            counterfactual = dict(reference, step=step, time_s=step/20,
                stage=plan['frames'][step-1]['stage'], fixture_layout=RELOCATED,
                joint_pos=q.tolist(), body_poses=bodies.tolist())
            check = inspect(counterfactual, hulls)
            check['ik_position_error_m'] = servo.last['ik_position_error_m']
            check['commanded_joint_pos'] = q.tolist()
            samples.append(check)
        report = dict(fixture_reference_action=fixture_step, grasp_reference_action=grasp_step,
            samples=samples, failure=failure,
            unexpected_intersections=sum(len(x['unexpected_intersections']) for x in samples),
            maximum_ik_position_error_m=max((x['ik_position_error_m'] for x in samples), default=0.))
        reports.append(report)
        print(json.dumps({key: value for key, value in report.items() if key!='samples'}), flush=True)
    return dict(kind='counterfactual_relocated_native_fixture_and_fixed_grasp_screen',
        native_validated=False, score=None, reports=reports,
        plan_sha256=hashlib.sha256(Path(plan_path).read_bytes()).hexdigest(),
        trace_sha256=hashlib.sha256(Path(trace_path).read_bytes()).hexdigest(),
        source_sha256={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                       for name in ('screen_relocated_plan.py','audit_native_trace.py','audit_robot_plan.py',
                                    'tool_pose_servo.py','wheel_scene.py','fixture_layout.py')},
        limitations=['Fixed measured wheel state and grasp; cannot predict slip or robot tracking.',
                     'Exact authored rim/jaw hulls; conservative enclosures for round rods.',
                     'Sampled command poses only; native continuous-time contacts remain unproven.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    parser.add_argument('--measured-trace', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = screen(args.plan, args.measured_trace)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2)+'\n')
