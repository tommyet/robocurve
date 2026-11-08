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
            args=SimpleNamespace(skip_assay=False, diagnostic_layout=None, log_dir=self.folder),
            CONFIG={"proof_seconds": 5., "proof_load_n": .981},
            telemetry=SimpleNamespace(demo_events=[]),
        )
        exec(compile(ast.Module(body=[cls], type_ignores=[]), str(source), "exec"), namespace)
        self.runner_class = namespace[cls.name]
        modules = patch.dict(sys.modules, {
            "proof_load": SimpleNamespace(EndpointLoad=FakeLoad),
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

    def embodiment(self):
        runner = self.runner_class.__new__(self.runner_class)
        runner._close_finished = False
        runner._base = SimpleNamespace(step_dt=.05)
        runner._t, runner.seen = 0., []
        runner.assay_attempted, runner.assay_phase = False, None
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
        self.assertEqual(self.report()["score"], 1.)
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


if __name__ == "__main__":
    unittest.main()
