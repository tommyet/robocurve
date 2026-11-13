"""State-assisted scripted demo, issuing ordinary bounded robot joint targets.

This controller is explicitly privileged relative to Dream: it observes the
native wrench pose to estimate the current grasp. It never writes any object
pose, attachment, force, material, score or actuator limit. Dream does not use it.
"""
import numpy as np
import re
from thread_coupling import rotation


def nipple_alignment(nominal_position,nominal_rotation,measured_pose):
    """Choose the nearest equivalent square-flat orientation, before a turn.

    Rotation is latched for each quarter-turn, so successful nipple rotation
    never moves the target further away. Actual centre translation may follow
    the physically deforming rim. The four equivalent square orientations
    keep each return stroke within the original wrist workspace.
    """
    from wheel_scene import spoke_phase
    pose=np.asarray(measured_pose,float)
    if pose.shape!=(7,) or not np.isfinite(pose).all():raise ValueError('Finite nipple pose required')
    actual=rotation(pose[3:]);nominal=np.asarray(nominal_rotation,float)
    alternatives=[actual@spoke_phase(k*np.pi/2)@nominal.T for k in range(4)]
    index=int(np.argmax([np.trace(r) for r in alternatives]))
    correction=alternatives[index]
    return correction,dict(square_symmetry_quarters=index,
        orientation_correction_rad=float(np.arccos(np.clip((np.trace(correction)-1)/2,-1.,1.))),
        centre_correction_m=float(np.linalg.norm(pose[:3]-nominal_position)))


def compensated_tcp(nominal_tcp, nominal_rotation, measured_tcp, measured_rotation,
                    measured_tool_pose, reference_grip_position, reference_grip_rotation):
    pose=np.asarray(measured_tool_pose,float)
    if pose.shape!=(7,) or not np.isfinite(pose).all():
        raise ValueError('Finite measured tool pose required')
    R=rotation(pose[3:])
    grasp_position=R.T@(np.asarray(measured_tcp)-pose[:3])
    grasp_rotation=R.T@measured_rotation
    desired_tool_rotation=nominal_rotation@reference_grip_rotation.T
    desired_tool_position=nominal_tcp-desired_tool_rotation@reference_grip_position
    desired_tcp=desired_tool_position+desired_tool_rotation@grasp_position
    desired_rotation=desired_tool_rotation@grasp_rotation
    return desired_tcp,desired_rotation,dict(
        measured_grasp_position_in_tool_m=grasp_position.tolist(),
        measured_grasp_rotation_in_tool=grasp_rotation.tolist(),
        desired_tool_position_m=desired_tool_position.tolist(),
        desired_tool_rotation=desired_tool_rotation.tolist(),
        current_tool_position_error_m=float(np.linalg.norm(pose[:3]-desired_tool_position)),
        tcp_correction_m=float(np.linalg.norm(desired_tcp-nominal_tcp)))


class ToolPoseServo:
    def __init__(self,plan,*,nipple_feedback=False):
        cal=plan['held_grasp_calibration']
        self.position=np.array(cal['tcp_position_in_tool_m'])
        self.rotation=np.array(cal['tcp_rotation_in_tool'])
        self.first_step=int(cal['applies_from_step'])
        self.release_step=int(plan.get('released_tool',{}).get('from_step',10**9))
        self.plan=plan;self.nipple_feedback=bool(nipple_feedback)
        self.latched_key=None;self.nipple_rotation=None
        self.last=None

    def target_spoke(self,step):
        if not self.nipple_feedback or not 1<=step<=len(self.plan['frames']):return None
        match=re.search(r'[Nn]ipple (\d+)',self.plan['frames'][step-1]['stage'])
        return None if match is None else int(match.group(1))

    def command(self,step,nominal,measured_joint_positions,measured_tool_pose,measured_nipple_pose=None):
        from yam_arena import ik,station
        target=np.asarray(nominal,float).copy()
        if step<self.first_step or step>=self.release_step:
            self.last={'active':False};return target
        q=np.asarray(measured_joint_positions,float)[7:13]
        p,R=ik.tcp_pose(target[7:13],station.BASES['right'])
        nipple_diagnostic=None
        spoke=self.target_spoke(step)
        if spoke is not None:
            if measured_nipple_pose is None:raise ValueError('Native nipple feedback requested but missing')
            from plan_turns import nominal_nipple
            frame=self.plan['frames'][step-1]
            centre,nR=nominal_nipple(spoke,np.deg2rad(self.plan['nipple_flat_phase_deg']),
                                   np.deg2rad(frame['nominal_wheel_clocking_deg']))
            quarter=re.search(r'quarter (\d+)',frame['stage'])
            key=(spoke,0 if quarter is None else int(quarter.group(1)))
            if key!=self.latched_key:
                self.nipple_rotation,nipple_diagnostic=nipple_alignment(centre,nR,measured_nipple_pose)
                self.latched_key=key
            else:
                nipple_diagnostic={'latched_from_earlier_frame':True}
            original_p=p.copy();original_R=R.copy()
            p=np.asarray(measured_nipple_pose)[:3]+self.nipple_rotation@(p-centre)
            R=self.nipple_rotation@R
            nipple_diagnostic.update(spoke=spoke,quarter=key[1],rotation_is_latched=True,
                target_translation_correction_m=float(np.linalg.norm(p-original_p)),
                target_orientation_correction_rad=float(np.arccos(np.clip((np.trace(R@original_R.T)-1)/2,-1,1))))
        actual_p,actual_R=ik.tcp_pose(q,station.BASES['right'])
        desired_p,desired_R,diagnostic=compensated_tcp(p,R,actual_p,actual_R,measured_tool_pose,self.position,self.rotation)
        if diagnostic['tcp_correction_m']>.06:
            raise RuntimeError('Tool grasp changed by more than60mm; stop scripted servo')
        solution,pe,rotation_error=ik.solve(desired_p,ik.matrix_to_quat_xyzw(desired_R),target[7:13],
            station.BASES['right'],iters=150,damping=.008,tol=1e-7)
        if pe>.0002 or rotation_error>.002:
            raise RuntimeError(f'Tool servo IK failed: position={pe}, rotation={rotation_error}')
        target[7:13]=solution
        self.last={'active':True,**diagnostic,'nipple_target':nipple_diagnostic,'ik_position_error_m':float(pe),'ik_rotation_error_rad':float(rotation_error)}
        return target
