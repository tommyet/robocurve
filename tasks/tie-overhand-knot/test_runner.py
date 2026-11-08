"""Local assessor/finalization checks; no simulator, encoder, or GPU required.

Compile the actual runner class from its AST because importing run.py requires
the simulator stack. Only its base embodiment, endpoint load, and video process
are replaced. The real scorer consumes synthetic telemetry from test_scoring;
topology positives are injected. These tests verify orchestration and cleanup,
not physical knot retention, scene startup, or the complete Inspect CLI.

Run: python -m unittest discover -s tasks/tie-overhand-knot -p test_runner.py -v
"""
import ast
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from scoring import KnotScorer
from test_scoring import candidate, proof_sample, straight_sample


class FakeEmbodiment:
    def step(self, action):
        self._t += self._base.step_dt
        self.endpoint_load.elapsed += self._base.step_dt
        elapsed, force = self.endpoint_load.elapsed, self.endpoint_load.magnitude
        self.task.module._tracker.update(proof_sample(self._t, elapsed, force, self.assay_phase))
        self.review_frames += 1
        self.seen.append((self.assay_phase, elapsed, force))

    def close(self):
        self.base_closed = True
        if getattr(self, "base_close_error", False):
            raise RuntimeError("base close failure")


class FakeLoad:
    fail_at = None

    def __init__(self, base, magnitude):
        self.magnitude, self.elapsed = magnitude, 0.
        self.active, self.calls = False, 0

    def apply(self, start, end):
        self.calls += 1
        self.active = True
        if self.calls == self.fail_at:
            raise RuntimeError("force apply failure")

    def clear(self):
        self.active = False


class FakeTransition:
    """Require one audit bracket for each control step without a native backend."""
    fail_start = False
    fail_after = None
    constructed = 0

    def __init__(self, base, target_hz, capture_time_s, *, diagnostic_only=False):
        type(self).constructed += 1
        self.target_hz = target_hz
        self.report = {'status': 'not_started', 'diagnostic_only': diagnostic_only,
                       'validated_control_intervals': 0, 'callback_removed': False,
                       'control_hz': 20, 'target_physics_hz': target_hz,
                       'requested_substeps': target_hz // 20, 'old_physics_hz': 240.,
                       'native_physics_dt_s': 1/target_hz, 'state_writes': False,
                       'counter_writes': False, 'state_sha256_before': 'test-only',
                       'state_sha256_after': 'test-only', 'counters_before': {'native': 1},
                       'counters_after': {'native': 1}, 'switch_capture_time_s': capture_time_s,
                       'intervals': []}
        self.pending = None

    def start(self):
        if self.fail_start:
            raise ValueError('transition guard failed')
        self.report['status'] = 'awaiting_intervals'

    def before_step(self, time, frames):
        if self.pending is not None:
            raise ValueError('unclosed interval')
        self.pending = (time, frames)

    def after_step(self, time, frames):
        previous, previous_frames = self.pending
        if not np.isclose(time - previous, .05) or frames != previous_frames + 1:
            raise ValueError('incorrect capture interval')
        if self.report['validated_control_intervals'] + 1 == self.fail_after:
            raise ValueError('native callback mismatch')
        self.pending = None
        substeps = self.target_hz // 20
        camera = dict(frame_delta=[1], timestamp_s=[time], last_update_s=[time],
                      float32_predicted_timestamp_s=[time])
        self.report['intervals'].append(dict(
            validated=True, capture_time_s=time, native_substeps=substeps,
            native_callback_dt_s=[1/self.target_hz]*substeps,
            counter_deltas={'native': substeps, 'environment': substeps},
            cameras={'review_cam': camera, 'top_cam': camera}))
        self.report['validated_control_intervals'] += 1
        self.report['status'] = 'validated_intervals'

    def fail(self, error):
        self.report.update(status='failed', error=str(error))

    def close(self):
        if self.pending is not None:
            self.fail(ValueError('unfinished interval'))
        self.report['callback_removed'] = True

    def save(self, path):
        path.write_text(json.dumps(self.report))


class FakeEncoder:
    def __init__(self, timeout=False):
        self.stdin = io.BytesIO()
        self.timeout, self.killed, self.code = timeout, False, None

    def wait(self, timeout):
        if self.timeout and not self.killed:
            raise subprocess.TimeoutExpired("ffmpeg", timeout)
        self.code = -9 if self.killed else 0
        return self.code

    def poll(self):
        return self.code

    def kill(self):
        self.killed = True


class RunnerTests(unittest.TestCase):
    def test_unready_controller_is_rejected_before_simulator_import_or_output_creation(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'must-not-be-created'
            for policy in ('demo', 'thread'):
                with self.subTest(policy=policy):
                    result = subprocess.run([sys.executable, str(Path(__file__).with_name('run.py')),
                        '--policy', policy, '--log-dir', str(output)], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 2)
                    self.assertIn('full bimanual controller is not ready', result.stderr)
                    self.assertNotIn('ModuleNotFoundError', result.stderr)
                    self.assertFalse(output.exists())

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        source = Path(__file__).with_name("run.py")
        main = next(node for node in ast.parse(source.read_text()).body
                    if isinstance(node, ast.FunctionDef) and node.name == "main")
        cls = next(node for node in main.body
                   if isinstance(node, ast.ClassDef) and node.name == "AuditedRopeEmbodiment")
        self.metadata = {}
        namespace = dict(
            YamArenaEmbodiment=FakeEmbodiment, np=np, json=json, sys=sys,
            subprocess=subprocess, metadata=self.metadata,
            args=SimpleNamespace(skip_assay=False, diagnostic_layout=None, log_dir=self.folder,
                                 physics_hz=240, assay_physics_hz=960),
            CONFIG={"proof_seconds": 5., "proof_load_n": .981,
                    'physics_hz': 240, 'assay_physics_hz': 960},
            telemetry=SimpleNamespace(demo_events=[]),
        )
        exec(compile(ast.Module(body=[cls], type_ignores=[]), str(source), "exec"), namespace)
        self.runner_class = namespace[cls.name]
        modules = patch.dict(sys.modules, {
            "proof_load": SimpleNamespace(EndpointLoad=FakeLoad),
            "assay_physics": SimpleNamespace(AssayPhysicsSwitch=FakeTransition),
            "rope": SimpleNamespace(rope_state=lambda *args: SimpleNamespace(
                start_tip=np.zeros(3), end_tip=np.array([.64, 0., 0.]))),
        })
        modules.start()
        self.addCleanup(modules.stop)
        topology = patch("scoring.analyze_open_rope", return_value=candidate())
        topology.start()
        self.addCleanup(topology.stop)
        failure = patch.object(FakeLoad, "fail_at", None)
        failure.start()
        self.addCleanup(failure.stop)
        for name, value in (('fail_start', False), ('fail_after', None), ('constructed', 0)):
            context = patch.object(FakeTransition, name, value)
            context.start()
            self.addCleanup(context.stop)

    def embodiment(self):
        runner = self.runner_class.__new__(self.runner_class)
        runner._close_finished = False
        runner._base = SimpleNamespace(step_dt=.05)
        runner._t, runner.seen = 0., []
        runner.assay_attempted, runner.assay_phase = False, None
        runner.physics_switch, runner.assay_transition_required = None, False
        runner._transition_failure = None
        runner.last_policy_action = SimpleNamespace(data=np.zeros(14))
        runner.policy_steps = 1
        scorer = KnotScorer()
        scorer.update(straight_sample())
        runner.task = SimpleNamespace(module=SimpleNamespace(_tracker=scorer))
        runner.audit = io.StringIO()
        runner.review_encoder, runner.review_stderr = FakeEncoder(), io.BytesIO()
        runner.review_frames, runner.endpoint_load = 1, None
        return runner

    def report(self, name="score-summary.json"):
        return json.loads((self.folder / name).read_text())

    def test_assay_phases_final_score_and_idempotent_close(self):
        runner = self.embodiment()
        runner.close()
        result = self.report()
        self.assertEqual(result["score"], 1.)
        self.assertEqual(self.metadata["inspect_policy_score"], .5)
        self.assertEqual(self.metadata["audited_final_score"], 1.)
        self.assertTrue(result["finalization"]["complete"])
        self.assertTrue(result['assay_physics_transition']['required'])
        self.assertEqual(result['assay_physics_transition']['validated_control_intervals'], 140)
        self.assertFalse(runner.physics_switch.report['diagnostic_only'])
        self.assertEqual(len(runner.seen), 140)
        self.assertEqual(runner.seen[0], ("seating", .05, 0.))
        self.assertEqual(runner.seen[40], ("proof", .05, .981))
        self.assertFalse(runner.endpoint_load.active)
        self.assertTrue(runner.audit.closed)
        self.assertTrue(runner.base_closed)
        runner.close()
        self.assertEqual(len(runner.seen), 140)

    def test_assay_failure_cleans_up_and_preserves_partial_score(self):
        FakeLoad.fail_at = 5
        runner = self.embodiment()
        encoder = runner.review_encoder
        with self.assertRaises(BaseExceptionGroup):
            runner.close()
        self.assertFalse(runner.endpoint_load.active)
        self.assertTrue(runner.audit.closed)
        self.assertTrue(encoder.stdin.closed)
        self.assertTrue(runner.review_stderr.closed)
        self.assertTrue(runner.base_closed)
        self.assertEqual(self.report()["score"], .5)
        self.assertFalse(self.report()["finalization"]["complete"])
        self.assertFalse(self.report("assay.json")["completed"])
        self.assertTrue(self.report("assay.json")["errors"])
        runner.close()  # Failure cleanup must also be idempotent.

    def test_encoder_timeout_kills_process_and_preserves_score(self):
        runner = self.embodiment()
        encoder = runner.review_encoder = FakeEncoder(timeout=True)
        with self.assertRaises(BaseExceptionGroup):
            runner.close()
        self.assertTrue(encoder.killed)
        self.assertTrue(runner.audit.closed)
        self.assertTrue(runner.base_closed)
        self.assertFalse(runner.endpoint_load.active)
        self.assertEqual(self.report()["score"], .5)
        self.assertEqual(self.report()['geometric_score'], 1.)
        self.assertFalse(self.report()["finalization"]["complete"])

    def test_existing_runner_failure_does_not_start_assay(self):
        runner = self.embodiment()
        try:
            raise RuntimeError("policy failed")
        except RuntimeError:
            runner.close()
        self.assertEqual(runner.seen, [])
        self.assertTrue(runner.base_closed)
        result = self.report()
        self.assertEqual(result["score"], .5)
        self.assertFalse(result["finalization"]["complete"])
        self.assertIn("policy failed", result["finalization"]["interrupted_by"])

    def test_base_close_failure_is_reported_in_preserved_summary(self):
        runner = self.embodiment()
        runner.base_close_error = True
        with self.assertRaises(BaseExceptionGroup):
            runner.close()
        finalization = self.report()["finalization"]
        self.assertFalse(finalization["complete"])
        self.assertIn("base close failure", " ".join(finalization["errors"]))

    def test_zero_policy_result_finishes_without_assessor_or_transition(self):
        runner = self.embodiment()
        runner.task.module._tracker = KnotScorer()
        with patch('scoring.analyze_open_rope', return_value={
                'status': 'unknot', 'is_overhand': False, 'reason': 'test-only negative'}):
            runner.task.module._tracker.update(straight_sample())
            runner.close()
        result = self.report()
        self.assertEqual(result['score'], 0.)
        self.assertTrue(result['finalization']['complete'])
        self.assertFalse(result['assay_physics_transition']['required'])
        self.assertEqual(result['assay_physics_transition']['status'], 'not_required')
        self.assertIsNone(runner.physics_switch)
        self.assertEqual(FakeTransition.constructed, 0)
        self.assertEqual(runner.seen, [])

    def test_required_switch_failure_cannot_be_swallowed_by_inspect(self):
        runner = self.embodiment()
        FakeTransition.fail_start = True
        with self.assertRaises(BaseExceptionGroup):
            runner._run_assay()
        # Inspect may catch this error before invoking close. The stored failure
        # must still prohibit a complete final result when sys.exception is None.
        with self.assertRaises(BaseExceptionGroup):
            runner.close()
        result = self.report()
        self.assertEqual(result['score'], .5)
        self.assertFalse(result['finalization']['complete'])
        self.assertEqual(result['assay_physics_transition']['status'], 'failed')
        self.assertTrue(result['assay_physics_transition']['callback_removed'])
        self.assertTrue(runner.base_closed)
        self.assertTrue(runner.audit.closed)
        self.assertEqual(runner.seen, [])

    def test_failed_last_native_interval_cannot_report_full_authoritative_credit(self):
        runner = self.embodiment()
        FakeTransition.fail_after = 140
        with self.assertRaises(BaseExceptionGroup):
            runner.close()
        result = self.report()
        self.assertEqual(result['geometric_score'], 1.)
        self.assertEqual(result['candidate_score'], 1.)
        self.assertEqual(result['score'], .5)
        self.assertEqual(self.metadata['audited_final_score'], .5)
        self.assertEqual(self.metadata['geometric_score'], 1.)
        self.assertEqual(result['assay_certification']['status'], 'incomplete')
        self.assertFalse(result['finalization']['complete'])
        self.assertEqual(result['assay_physics_transition']['validated_control_intervals'], 139)
        self.assertFalse(runner.endpoint_load.active)
        self.assertTrue(runner.base_closed)

    def bimanual_embodiment(self):
        runner = self.embodiment()
        self.runner_class.close.__globals__['CONFIG']['score_version'] = 'overhand-bimanual-v4'
        # This isolates runner finalization; scorer geometry/timing is exercised
        # independently in test_bimanual_scoring, not invented by this stub.
        runner.task.module._tracker = SimpleNamespace(summary=lambda final=False: dict(
            score=1., candidate_score=1., invalid=None, diagnostic_only=False,
            release_elapsed_s=5., release_required_s=5., status='qualified'))
        return runner

    def test_bimanual_close_never_adds_external_pull_or_simulation_steps(self):
        runner = self.bimanual_embodiment()
        runner.close()
        result = self.report()
        self.assertEqual(result['score'], 1.)
        self.assertTrue(result['finalization']['complete'])
        self.assertFalse(result['assay_certification']['required'])
        self.assertEqual(FakeTransition.constructed, 0)
        self.assertIsNone(runner.endpoint_load)
        self.assertEqual(runner.seen, [])
        self.assertTrue(runner.audit.closed)
        self.assertTrue(runner.base_closed)

    def test_bimanual_incomplete_recording_cannot_claim_full_credit(self):
        runner = self.bimanual_embodiment()
        runner.base_close_error = True
        with self.assertRaises(BaseExceptionGroup):
            runner.close()
        result = self.report()
        self.assertEqual(result['score'], .5)
        self.assertFalse(result['finalization']['complete'])
        self.assertFalse(result['finalization_certification']['complete'])
        self.assertEqual(FakeTransition.constructed, 0)
        self.assertEqual(runner.seen, [])


if __name__ == "__main__":
    unittest.main()
