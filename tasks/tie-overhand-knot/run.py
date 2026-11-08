"""Run one audited rope-knot trial using the guide's Inspect Robots workflow."""

from __future__ import annotations

import argparse
import atexit
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import platform
import os
import subprocess
import sys
import time
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np

from scoring import KnotScorer
from config import CONFIG
import telemetry
SCORE_VERSION = "overhand-retention-v3"

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy", choices=("demo", "dream", "idle", "grasp", "loop", "thread", "jig"), default="demo")
    parser.add_argument("--max-steps", type=int, default=2400)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--log-dir", type=Path, required=True)
    parser.add_argument("--headless", choices=("true", "false"), default="true")
    parser.add_argument("--physics-hz", type=int, choices=(240, 480, 960), default=240,
                        help="Physics substeps; control and recorded policy observations remain 20 Hz")
    parser.add_argument("--assay-physics-hz", type=int, choices=(480, 960), default=960,
                        help="Physics rate used only after a released knot qualifies for the assessor")
    parser.add_argument("--development-jig", choices=("three-peg",),
                        help="Development fixture; requires separate task and contact validation")
    parser.add_argument("--diagnostic-layout", choices=("straight", "preformed"),
                        help="Physics diagnostic only; cannot earn a task score")
    parser.add_argument("--proof-probe", action="store_true",
                        help="Apply assessor forces to a diagnostic layout, never a robot trial")
    parser.add_argument("--skip-assay", action="store_true",
                        help="Development only: record policy outcome without the post-policy load test")
    args = parser.parse_args()
    if args.policy in ('demo', 'dream', 'jig'):
        if args.diagnostic_layout or args.proof_probe:
            parser.error('demo, dream and jig use the ordinary task scene, not diagnostic layouts')
        args.development_jig = 'three-peg'
    if args.development_jig and (args.diagnostic_layout or args.proof_probe):
        parser.error('development-jig cannot be combined with diagnostic-layout or proof-probe')
    if args.diagnostic_layout and args.policy != 'idle':
        parser.error('diagnostic layouts require the idle policy')
    if args.proof_probe and not args.diagnostic_layout:
        parser.error('proof-probe requires a diagnostic layout')
    if not args.diagnostic_layout and not args.skip_assay and args.physics_hz != 240:
        parser.error('the audited assessor switch requires 240 Hz policy physics; other development rates require --skip-assay')
    if args.development_jig:
        import config
        import jig_layout
        nodes = jig_layout.initial_nodes()
        config.initial_nodes = lambda: nodes.copy()
        density = CONFIG['mass'] / CONFIG['length']
        length = float(np.linalg.norm(np.diff(nodes, axis=0), axis=1).sum())
        CONFIG.update(initial_nodes=nodes.tolist(), development_jig='three-peg',
                      instruction='Finish the overhand knot in the blue cord, remove it from the pegs and let go. The knot will be tested with a gentle pull.',
                      jig_geometry=jig_layout.geometry(),
                      length=length, mass=density*length, anchor_start=True)
    if args.diagnostic_layout:
        import config
        from diagnostic_layouts import diagnostic_nodes
        nodes = diagnostic_nodes(args.diagnostic_layout)
        config.initial_nodes = lambda: nodes.copy()
        CONFIG['diagnostic_only'] = True
        CONFIG['diagnostic_layout'] = args.diagnostic_layout
        CONFIG['initial_nodes'] = nodes.tolist()
        density = CONFIG['mass'] / CONFIG['length']
        CONFIG['length'] = float(np.linalg.norm(np.diff(nodes, axis=0), axis=1).sum())
        CONFIG['mass'] = density * CONFIG['length']
        CONFIG['proof_probe'] = args.proof_probe
    CONFIG['physics_hz'] = args.physics_hz
    CONFIG['assay_physics_hz'] = args.assay_physics_hz
    if not 1 <= args.max_steps <= 2400:
        parser.error("max-steps must be 1..2400 (120 seconds at 20 Hz)")
    args.log_dir.mkdir(parents=True, exist_ok=True)
    if (args.log_dir / "trajectory.jsonl").exists():
        parser.error("choose a fresh log directory; existing audit data will not be overwritten")

    from inspect_robots.cli import main as inspect_main
    from inspect_robots.registry import register
    from yam_arena import ik
    from yam_arena.constants import FINGER_OPEN, GRIPPER, SHOULDER, WRIST
    from yam_arena.inspect_embodiment import YamArenaEmbodiment

    instances = []

    class AuditedRopeEmbodiment(YamArenaEmbodiment):
        def __init__(self, **kwargs):
            self._close_finished = False
            self.audit = self.review_encoder = self.review_stderr = None
            self.endpoint_load = None
            self.physics_switch = None
            self.assay_transition_required = False
            self._transition_failure = None
            instances.append(self)
            super().__init__(**kwargs)
            if not self.info.is_simulated:
                raise RuntimeError("this task runner is for simulation only")
            hz = self.info.control_hz
            per_arm = (SHOULDER["velocity"] / hz,) * 3 + (WRIST["velocity"] / hz,) * 3 + (GRIPPER["velocity"] / abs(FINGER_OPEN) / hz,)
            semantics = replace(self.info.action_space.semantics, max_step=per_arm * 2)
            self.info = replace(self.info, action_space=replace(self.info.action_space, semantics=semantics))
            metadata['action_limits'] = {
                'low': self._low.tolist(), 'high': self._high.tolist(),
                'max_step': list(self.info.action_space.semantics.max_step),
                'source': 'Audited embodiment action bounds and control-step semantics',
            }

        def _ensure_sim(self, goal):
            # The adapter imports scene construction only after Kit starts. Start
            # its shared app identically, then add this task's passive review
            # camera before construction. No installed adapter files are changed.
            from yam_arena import inspect_embodiment as adapter
            if adapter._APP is None:
                os.environ.setdefault("OMNI_KIT_ACCEPT_EULA", "YES")
                from isaaclab.app import AppLauncher
                options = {"headless": self.headless, "device": self.device, "enable_cameras": True}
                if not self.headless:
                    options["visualizer"] = ["kit"]
                    os.environ["DISPLAY"] = adapter.window_display(os.environ)
                    if os.environ["DISPLAY"] == adapter.DESKTOP_DISPLAY:
                        options["window_width"], options["window_height"] = adapter.DESKTOP_SIZE
                adapter._APP = AppLauncher(**options).app
                atexit.register(adapter._close_app_at_exit)
            from yam_arena import scene as scene_module
            from visuals import add_review_camera, install_scene_visuals
            make_env = scene_module.make_env

            def make_review_env(embodiment, **kwargs):
                add_review_camera(embodiment)
                return make_env(embodiment, **kwargs)

            scene_module.make_env = make_review_env
            original_physics_dt = scene_module.PHYSICS_DT
            scene_module.PHYSICS_DT = 1. / args.physics_hz
            try:
                super()._ensure_sim(goal)
            finally:
                scene_module.make_env = make_env
                scene_module.PHYSICS_DT = original_physics_dt
            self.visual_metadata = install_scene_visuals(self._base)
            from isaaclab.sim.utils.stage import get_current_stage
            from pxr import UsdPhysics
            physics = {'physics_dt': float(self._base.physics_dt),
                       'control_dt': float(self._base.step_dt), 'scenes': [],
                       'rope_requested': {key: CONFIG[key] for key in ('contact_offset', 'solver_position_iterations', 'solver_velocity_iterations')},
                       'rope_rest_offset_m': 0.}
            for prim in get_current_stage().Traverse():
                if prim.IsA(UsdPhysics.Scene):
                    attrs = {}
                    for attr in prim.GetAttributes():
                        if any(word in attr.GetName().lower() for word in ('ccd', 'gpu', 'solver', 'stabil', 'iteration')):
                            attrs[attr.GetName()] = str(attr.Get())
                    physics['scenes'].append({'path': str(prim.GetPath()), 'attributes': attrs})
            (args.log_dir / 'physics.json').write_text(json.dumps(physics, indent=2) + '\n')


        def reset(self, scene, *, seed=None):
            self.endpoint_load = None
            self.physics_switch = None
            self.assay_transition_required = False
            self._transition_failure = None
            self.proof_record = None
            self.assay_phase = None
            self.assay_attempted = False
            self.last_policy_action = None
            self.policy_steps = 0
            telemetry.latest_sample = None
            telemetry.demo_events.clear()
            observation = super().reset(scene, seed=seed)
            import cv2

            # Save the actual settled initial scene, before any policy action.
            rgb = self._base.scene["top_cam"].data.output["rgb"]
            rgb = rgb.torch if hasattr(rgb, "torch") else rgb
            rgb = rgb[0, ..., :3].detach().cpu().numpy().astype(np.uint8)
            if not cv2.imwrite(str(args.log_dir / "setup.png"), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)):
                raise RuntimeError("could not save the initial scene image")
            self.task.module._tracker = KnotScorer(CONFIG)
            self.audit = (args.log_dir / "trajectory.jsonl").open("x")
            self.review_encoder = None
            self.review_frames = 0
            (args.log_dir / "visuals.json").write_text(json.dumps(self.visual_metadata, indent=2) + "\n")
            self._audit_sample()
            return observation

        def step(self, action):
            if args.proof_probe and self._t >= 1.-1e-9:
                from proof_load import EndpointLoad
                from rope import rope_state
                if self.endpoint_load is None:
                    self.endpoint_load = EndpointLoad(self._base, magnitude=CONFIG['proof_load_n'])
                seating_seconds = self.task.module._tracker.config['seating_seconds']
                phase = 'seating' if self._t < 1.+seating_seconds-1e-9 else 'proof'
                if phase != self.assay_phase:
                    self.assay_phase = phase
                    self.endpoint_load.elapsed = 0.
                state = rope_state(self._base, 'cord')
                # Seat the knot gradually; an instantaneous point-force step
                # on a sub-gram end link is an impact, not a hanging-weight test.
                fraction = min(1., max(0., (self._t - 1.) / seating_seconds))
                self.endpoint_load.magnitude = CONFIG['proof_load_n'] * fraction
                self.endpoint_load.apply(state.start_tip, state.end_tip)
            if self.assay_phase is None:
                # Policies may reuse/mutate their action object after step().
                self.last_policy_action = deepcopy(action)
                self.policy_steps += 1
            return super().step(action)

        def _run_assay(self):
            """Evaluate an already released knot after policy actions end."""
            if self.assay_attempted:
                return
            self.assay_attempted = True
            if args.skip_assay or args.diagnostic_layout or self.last_policy_action is None:
                return
            tracker = self.task.module._tracker
            policy_result = tracker.summary(final=True)
            (args.log_dir / 'policy-end-score.json').write_text(json.dumps(policy_result, indent=2)+'\n')
            metadata['inspect_policy_score'] = policy_result['score']
            if policy_result['score'] != .5 or policy_result['invalid'] is not None:
                return
            self.assay_transition_required = True
            from proof_load import EndpointLoad
            from rope import rope_state
            dt = float(self._base.step_dt)
            seating_seconds = tracker.config['seating_seconds']
            evidence = {'policy_steps': self.policy_steps, 'policy_end_time': float(self._t),
                        'robot_command': np.asarray(self.last_policy_action.data).reshape(-1).tolist(),
                        'assessor_only': True, 'policy_receives_no_observations_or_actions_during_assay': True,
                        'seating_seconds': seating_seconds, 'proof_seconds': CONFIG['proof_seconds'],
                        'target_endpoint_force_n': CONFIG['proof_load_n'], 'completed': False,
                        'policy_physics_hz': args.physics_hz, 'assay_physics_hz': args.assay_physics_hz,
                        'inspect_result_scope': 'Policy only; this assessor runs after Inspect finishes the episode.'}
            # Hold the policy's final joint command. The assessor adds only
            # endpoint forces, never body poses, new grasps or knot crossings.
            errors = []
            try:
                from assay_physics import AssayPhysicsSwitch
                self.physics_switch = AssayPhysicsSwitch(self._base, args.assay_physics_hz, self._t,
                                                        diagnostic_only=bool(CONFIG.get('diagnostic_only')))
                self.physics_switch.start()
                self._assay_expected_intervals = round((seating_seconds + CONFIG['proof_seconds']) / dt)
                self.endpoint_load = EndpointLoad(self._base, magnitude=0.)
                for phase, duration in (('seating', seating_seconds), ('proof', CONFIG['proof_seconds'])):
                    self.assay_phase = phase
                    self.endpoint_load.elapsed = 0.
                    count = round(duration/dt)
                    if count < 1 or not np.isclose(count*dt, duration, rtol=0, atol=1e-9):
                        raise ValueError('Assessor duration must contain a whole number of control intervals')
                    for index in range(count):
                        # Left endpoint of the integration interval: start at
                        # zero, then reach full force as the proof phase begins.
                        self.endpoint_load.magnitude = CONFIG['proof_load_n'] * (index/count if phase == 'seating' else 1.)
                        state = rope_state(self._base, 'cord')
                        self.endpoint_load.apply(state.start_tip, state.end_tip)
                        self.physics_switch.before_step(self._t, self.review_frames)
                        super().step(self.last_policy_action)
                        self.physics_switch.after_step(self._t, self.review_frames)
                        self.physics_switch.save(args.log_dir / 'assay-physics-transition.json')
                        if tracker.invalid is not None:
                            evidence['stopped_reason'] = tracker.invalid
                            return
                evidence['completed'] = True
            except BaseException as exc:
                self._transition_failure = exc
                if self.physics_switch is not None:
                    self.physics_switch.fail(exc)
                errors.append(exc)
            finally:
                if self.endpoint_load is not None:
                    try:
                        self.endpoint_load.clear()
                    except BaseException as exc:
                        errors.append(exc)
                if self.physics_switch is not None:
                    try:
                        self.physics_switch.close()
                        self.physics_switch.save(args.log_dir / 'assay-physics-transition.json')
                    except BaseException as exc:
                        self._transition_failure = exc
                        errors.append(exc)
                evidence['end_time'] = float(self._t)
                evidence['errors'] = [f'{type(exc).__name__}: {exc}' for exc in errors]
                try:
                    evidence['result'] = tracker.summary(final=True)
                    evidence['result_scope'] = 'Geometry and force telemetry only; authoritative score is in score-summary.json after native audit and finalization.'
                    (args.log_dir / 'assay.json').write_text(json.dumps(evidence, indent=2)+'\n')
                except BaseException as exc:
                    errors.append(exc)
                if errors:
                    raise BaseExceptionGroup('Post-policy assessor failed', errors)

        def _audit_sample(self):
            from hand_geometry import robot_collision_boxes
            def arr(value):
                value = value.torch if hasattr(value, 'torch') else value
                return value.detach().cpu().numpy().astype(float)
            origin = arr(self._base.scene.env_origins)[0]
            world = self._base.arena_world
            hands = []
            for side in ('left', 'right'):
                arm_name = side + '_robot'
                robot = self._base.scene[arm_name]
                arm_ids, finger_ids = self._ids[arm_name]
                q = arr(robot.data.joint_pos)[0]
                joints = q[arm_ids]
                tcp, tcp_rotation = ik.tcp_pose(joints, self.rig.bases[side])
                hands.append(dict(tcp=tcp.tolist(),
                    opening=float(np.clip(q[finger_ids].mean() / FINGER_OPEN, 0, 1)),
                    joints=joints.tolist(), tcp_rotation=tcp_rotation.tolist(),
                    finger_boxes=robot_collision_boxes(robot, origin=origin)))
            sample = {'time': float(self._t), 'hands': hands}
            from yam_arena.scene import object_states
            cord = object_states(self._env, ('cord',))['cord']
            sample['cord'] = cord.to_record()
            sample['diagnostic_only'] = bool(args.diagnostic_layout)
            if self.endpoint_load is not None and self.endpoint_load.active:
                sample['phase'] = self.assay_phase
                sample['proof'] = self.endpoint_load.record(self._base.step_dt)
            else:
                sample['phase'] = 'policy'
            self.task.module._tracker.update(sample)
            sample['metrics'] = self.task.module._tracker.summary()
            telemetry.latest_sample = sample
            self.audit.write(json.dumps(sample, allow_nan=False) + '\n')
            self.audit.flush()
            self._record_review_frame()

        def _record_review_frame(self):
            import cv2
            output = self._base.scene["review_cam"].data.output["rgb"]
            output = output.torch if hasattr(output, "torch") else output
            rgb = np.ascontiguousarray(output[0, ..., :3].detach().cpu().numpy(), dtype=np.uint8)
            if self.review_encoder is None:
                height, width = rgb.shape[:2]
                if not cv2.imwrite(str(args.log_dir / "setup-closeup.png"), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)):
                    raise RuntimeError("could not save the review setup image")
                self.review_stderr = (args.log_dir / "review-encoder.log").open("wb")
                self.review_encoder = subprocess.Popen([
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-n",
                    "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{width}x{height}",
                    "-framerate", "20", "-i", "pipe:0", "-an", "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", str(args.log_dir / "review.mp4"),
                ], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=self.review_stderr)
            self.review_encoder.stdin.write(rgb.tobytes())
            self.review_frames += 1

        def _task_step(self):
            self._audit_sample()
            return super()._task_step()

        def close(self):
            if self._close_finished:
                return
            # Never begin new simulation work while Inspect is unwinding an
            # error or interruption. Resource cleanup must still run in full.
            transition_failure = getattr(self, '_transition_failure', None)
            unwinding = sys.exception() or getattr(self, '_skip_assay_reason', None) or transition_failure
            errors = [transition_failure] if transition_failure is not None else []

            def attempt(operation):
                try:
                    return operation()
                except BaseException as exc:
                    errors.append(exc)
                    return None

            try:
                if self.audit is not None and not self.audit.closed and unwinding is None:
                    attempt(self._run_assay)
                if self.endpoint_load is not None:
                    attempt(self.endpoint_load.clear)
                if getattr(self, 'assay_transition_required', False):
                    transition = getattr(self, 'physics_switch', None)
                    if transition is not None:
                        attempt(transition.close)
                        attempt(lambda: transition.save(args.log_dir / 'assay-physics-transition.json'))
                    def require_complete_transition():
                        report = transition.report if transition is not None else {}
                        expected = getattr(self, '_assay_expected_intervals', None)
                        if report.get('status') != 'validated_intervals' or expected is None or report.get('validated_control_intervals') != expected or not report.get('callback_removed'):
                            raise RuntimeError('Required assay timestep transition did not complete: ' +
                                               str(report.get('error', report.get('status', 'not started'))))
                    attempt(require_complete_transition)
                attempt(lambda: (args.log_dir / 'demo-corrections.json').write_text(
                    json.dumps(telemetry.demo_events, indent=2)+'\n'))
                encoder = self.review_encoder
                if encoder is not None:
                    # Broken pipes, timeouts and nonzero exits must not skip
                    # audit finalization, stderr closure or base.close().
                    if encoder.stdin is not None:
                        attempt(encoder.stdin.close)
                    result = None
                    try:
                        result = encoder.wait(timeout=30)
                        if result:
                            raise RuntimeError('review video encoder failed; see review-encoder.log')
                    except BaseException as exc:
                        errors.append(exc)
                    finally:
                        if attempt(encoder.poll) is None:
                            attempt(encoder.kill)
                            attempt(lambda: encoder.wait(timeout=5))
                        self.review_encoder = None
                    if result == 0:
                        attempt(lambda: (args.log_dir / 'review-video.json').write_text(json.dumps({
                            'camera': 'review_cam', 'frames': self.review_frames, 'fps': 20,
                            'first_time': 0.0, 'last_time': (self.review_frames-1)/20,
                            'sent_to_dream': False,
                        }, indent=2)+'\n'))
                if self.review_stderr is not None:
                    attempt(self.review_stderr.close)
                if self.audit is not None and not self.audit.closed:
                    attempt(self.audit.close)
            finally:
                # The independent audit score is authoritative for the whole
                # recording. Inspect's existing episode log remains an honest
                # policy-only result; never rewrite it to invent assay steps.
                tracker = getattr(getattr(getattr(self, 'task', None), 'module', None), '_tracker', None)
                attempt(super().close)
                if tracker is not None:
                    def save_summary():
                        from replay import certify_result
                        summary = tracker.summary(final=True)
                        summary['score_scope'] = 'Policy plus recorded assessor phases, when present'
                        summary['inspect_result_scope'] = 'Policy episode only; post-policy assessor runs during close'
                        transition = getattr(self, 'physics_switch', None)
                        report = transition.report if transition is not None else {}
                        summary['assay_physics_transition'] = {
                            'required': bool(getattr(self, 'assay_transition_required', False)),
                            'status': report.get('status', 'not_required'),
                            'error': report.get('error'),
                            'validated_control_intervals': report.get('validated_control_intervals', 0),
                            'expected_control_intervals': getattr(self, '_assay_expected_intervals', None),
                            'callback_removed': report.get('callback_removed'),
                        }
                        summary['finalization'] = {
                            'complete': not errors and unwinding is None,
                            'errors': [f'{type(exc).__name__}: {exc}' for exc in errors],
                            'interrupted_by': f'{type(unwinding).__name__}: {unwinding}' if unwinding else None,
                        }
                        summary = certify_result(summary, CONFIG, report or None,
                            finalization_complete=summary['finalization']['complete'])
                        if summary['assay_certification']['required'] and summary['assay_certification']['status'] != 'complete' and not errors:
                            errors.append(RuntimeError('Full assessor evidence is not certified: ' +
                                          '; '.join(summary['assay_certification']['errors'])))
                            summary['finalization']['complete'] = False
                            summary['finalization']['errors'] = [f'{type(exc).__name__}: {exc}' for exc in errors]
                        (args.log_dir / 'score-summary.json').write_text(json.dumps(summary, indent=2)+'\n')
                        metadata['audited_final_score'] = summary['score']
                        metadata['geometric_score'] = summary['geometric_score']
                        metadata['assay_certification'] = summary['assay_certification']
                        metadata['authoritative_score_file'] = 'score-summary.json'
                        metadata['finalization_complete'] = summary['finalization']['complete']
                    attempt(save_summary)
                self._close_finished = True
            if errors:
                raise BaseExceptionGroup('Rope trial finalization failed', errors)

    register("embodiment", "audited_rope")(AuditedRopeEmbodiment)
    policy_name = "dream"
    if args.policy in ("demo", "idle", "grasp", "loop", "thread", "jig"):
        from demo_policy import register_policy
        policy_name = register_policy(mode=args.policy)
    cli_args = [
        "run", "--embodiment", "audited_rope", "--policy", policy_name,
        "-E", f"task={HERE / 'task.py'}", "-E", "object_jitter=0", "-E", "control_hz=20",
        "-E", "cam_width=320", "-E", "cam_height=176", "-E", f"headless={args.headless}",
        "--instruction", CONFIG["instruction"], "--scorer", "task_score", "--epochs", "1", "--seed", str(args.seed),
        "--max-steps", str(args.max_steps), "--store-frames", "--log-dir", str(args.log_dir),
        "--no-prompt", "--grader", "none",
    ]
    metadata = {"python": platform.python_version(), "policy": args.policy, "seed": args.seed, "max_steps": args.max_steps, "control_hz": 20, "score_version": SCORE_VERSION, "packages": {}}
    if args.policy == "dream":
        metadata["dream_transport"] = "direct"
    metadata["task_config"] = CONFIG
    snapshot = args.log_dir / "task-source"
    snapshot.mkdir(exist_ok=True)
    metadata["source_sha256"] = {}
    for source in sorted(HERE.glob("*.py")):
        if source.name.startswith("."):
            continue  # Exclude filesystem metadata such as macOS AppleDouble files.
        content = source.read_bytes()
        (snapshot / source.name).write_bytes(content)
        metadata["source_sha256"][source.name] = hashlib.sha256(content).hexdigest()
    for package in ("numpy", "yam-arena", "inspect-robots", "inspect-robots-yam", "inspect-robots-dream", "dreamlabs-client", "isaaclab", "isaacsim"):
        try:
            metadata["packages"][package] = version(package)
        except PackageNotFoundError:
            metadata["packages"][package] = "not registered"
    started = time.monotonic()
    errors = []
    result = None
    try:
        result = inspect_main(cli_args)
    except BaseException as exc:
        errors.append(exc)
    finally:
        # Also close instances if Inspect exits before its own close hook.
        for instance in instances:
            try:
                if errors:
                    instance._skip_assay_reason = errors[0]
                instance.close()
            except BaseException as exc:
                errors.append(exc)
        metadata["elapsed_wall_seconds"] = round(time.monotonic() - started, 3)
        try:
            (args.log_dir / "runtime.json").write_text(json.dumps(metadata, indent=2) + "\n")
        except BaseException as exc:
            errors.append(exc)
    if not errors and metadata.get('finalization_complete') is False:
        errors.append(RuntimeError('Trial finalization is incomplete; see score-summary.json'))
    if errors:
        raise BaseExceptionGroup('Rope trial failed', errors)
    if 'audited_final_score' in metadata:
        print(f"Final audited task score: {metadata['audited_final_score']}; "
              f"see {args.log_dir / 'score-summary.json'} (includes any post-policy assessor).")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
