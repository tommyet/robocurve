"""One deterministic native reset shared by every policy.

Only env.reset writes initial nodal/rigid state. The next five seconds advance
normal native physics with ordinary ready-position joint targets. No sensor or
assessor reading changes those targets, the duration or any object state.
"""
import time
import numpy as np

RESET_SETTLE_STEPS=100
RESET_CONTROL_HZ=20


def reset_and_settle(emb):
    import torch
    base=emb._base
    start=time.monotonic()
    before=int(base.sim._physics_step_count)
    emb._env.reset()
    after_raw=int(base.sim._physics_step_count)
    ready=emb._ready.detach().clone()
    values=ready.detach().cpu().numpy()
    if values.shape!=(1,14) or not np.isfinite(values).all():
        raise ValueError('Invalid ordinary ready action during reset')
    if np.any(values[0]<emb._low) or np.any(values[0]>emb._high):
        raise ValueError('Ready action exceeds normal adapter limits')
    for _ in range(RESET_SETTLE_STEPS):
        emb._env.step(ready)
    emb._t=0.
    return dict(method='raw environment reset followed by fixed native settling',
                status='completed',physics_step_count_before=before,
                physics_step_count_after_raw_reset=after_raw,
                physics_step_count_after=int(base.sim._physics_step_count),
                settle_control_steps=RESET_SETTLE_STEPS,
                settle_simulated_seconds=RESET_SETTLE_STEPS/RESET_CONTROL_HZ,
                settle_action14=values[0].tolist(),wall_seconds=time.monotonic()-start,
                controller='constant ordinary ready joint targets; no object feedback',
                writes='initial state only inside reset events; no pose or node writes during settling',
                stability='must be assessed from evidence; fixed duration is not a stability certificate')


def reset_staged_and_settle(emb):
    """Load the declared untied grasps at reset, then advance ordinary physics."""
    import torch
    from yam_arena.constants import ARM_JOINTS,FINGER_JOINTS,FINGER_OPEN
    from staged_grasp import initial_action
    from pinch_constraint import install as install_pinches
    from collar_friction import install as install_collar
    base=emb._base
    start=time.monotonic()
    before=int(base.sim._physics_step_count)
    emb._env.reset()
    after_raw=int(base.sim._physics_step_count)
    action=initial_action()
    if action.shape!=(14,) or not np.isfinite(action).all() or np.any(action<emb._low) or np.any(action>emb._high):
        raise ValueError('Invalid staged reset joint positions')
    ids=torch.tensor([0],device=base.device,dtype=torch.long)
    for side,offset in (('left',0),('right',7)):
        robot=base.scene[side+'_robot']
        arm=robot.find_joints(list(ARM_JOINTS),preserve_order=True)[0]
        fingers=robot.find_joints(list(FINGER_JOINTS),preserve_order=True)[0]
        q=robot.data.default_joint_pos.torch.clone()
        q[0,arm]=torch.as_tensor(action[offset:offset+6],device=q.device,dtype=q.dtype)
        q[0,fingers]=float(action[offset+6])*FINGER_OPEN
        robot.write_joint_position_to_sim_index(position=q,env_ids=ids)
        robot.write_joint_velocity_to_sim_index(velocity=torch.zeros_like(q),env_ids=ids)
        robot.actuators.target_command.set_position_index(value=q,env_ids=ids)
        robot.actuators.target_command.set_velocity_index(value=torch.zeros_like(q),env_ids=ids)
    emb._ready=torch.as_tensor(action[None],device=base.device,dtype=torch.float32)
    base.sim.render()
    base.scene.update(0.)
    pinches=install_pinches(base,'tie')
    collar=install_collar(base)
    for _ in range(RESET_SETTLE_STEPS):
        emb._env.step(emb._ready)
    emb._t=0.
    report=dict(method='fixed untied experimenter-loaded grasps followed by native settling',
        status='completed',physics_step_count_before=before,
        physics_step_count_after_raw_reset=after_raw,
        physics_step_count_after=int(base.sim._physics_step_count),
        settle_control_steps=RESET_SETTLE_STEPS,
        settle_simulated_seconds=RESET_SETTLE_STEPS/RESET_CONTROL_HZ,
        settle_action14=action.tolist(),wall_seconds=time.monotonic()-start,
        controller='constant ordinary starting joint targets; no object feedback',
        writes='cloth and robot initial conditions at reset only; no pose or node writes during settling',
        starting_grasps='left wide tip; right two untied standing strands; no knot, wrap or threaded loop',
        acquired_contact_nodes={side:len(p.indices) for side,p in pinches.items()})
    if min(report['acquired_contact_nodes'].values())<3:
        raise RuntimeError('Declared initial grasp failed during native settling')
    return report,pinches,collar
