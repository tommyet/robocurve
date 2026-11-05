"""A failed task can be valid evidence; malformed records cannot."""

import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

try:
    from . import audit_runs, finalize_batch
except ImportError:
    import audit_runs, finalize_batch


class ScoringEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.task = self.root/'task'
        self.run = self.root/'run'
        self.task.mkdir()
        (self.run/'task-source').mkdir(parents=True)
        source = Path(__file__).parent/'scoring.py'
        config = {'lower_shape': (1, 1), 'upper_shape': (1, 1), 'required_studs': 1}
        for target in (self.task, self.run/'task-source'):
            shutil.copyfile(source, target/'scoring.py')
            (target/'config.py').write_text('CONFIG = '+repr(config)+'\n')
        (self.run/'score-summary.json').write_text(json.dumps({'score': 0.}))
        body = {'pos': [.25, .1, .7571], 'quat_xyzw': [0., 0., 0., 1.]}
        self.rows = [{'time': t, 'upper': copy.deepcopy(body), 'lower': copy.deepcopy(body),
                      'hands': [{'tcp': [0., 0., 1.], 'opening': 1.},
                                {'tcp': [0., -.5, 1.], 'opening': 1.}]}
                     for t in (0., .05)]
        self.runtime = {'control_hz': 20, 'max_steps': 1200}

    def audit(self):
        report = {'checks': {}}
        audit_runs.trajectory_audit(self.rows, self.run, self.task, self.runtime, report)
        return report

    def test_brick_leaving_table_is_valid_zero_score_evidence(self):
        self.rows[1]['upper']['pos'][0] = 1.
        report = self.audit()
        self.assertTrue(all(c['passed'] for c in report['checks'].values()))
        self.assertEqual(report['current_rescore']['result']['score'], 0.)
        self.assertEqual(report['task_failure_reason'], 'a brick left the permitted table bounds')
        self.assertEqual(report['checks']['archived_scoring_evidence_valid']['task_failure_reason'],
                         report['task_failure_reason'])

    def test_invalid_quaternion_is_invalid_evidence(self):
        self.rows[0]['upper']['quat_xyzw'] = [0., 0., 0., 0.]
        report = self.audit()
        self.assertFalse(report['checks']['current_scoring_evidence_valid']['passed'])
        self.assertNotIn('task_failure_reason', report)

    def test_bad_time_is_invalid_evidence(self):
        self.rows[1]['time'] = 0.
        report = self.audit()
        self.assertFalse(report['checks']['trajectory_timing']['passed'])
        self.assertFalse(report['checks']['current_scoring_evidence_valid']['passed'])

    def test_malformed_observation_after_task_failure_still_fails_audit(self):
        self.rows[0]['upper']['pos'][0] = 1.
        baseline = copy.deepcopy(self.rows)
        for kind in ('quaternion', 'opening', 'rotation', 'half_size'):
            self.rows = copy.deepcopy(baseline)
            if kind == 'quaternion':
                self.rows[1]['upper']['quat_xyzw'] = [0., 0., 0., 0.]
            elif kind == 'opening':
                self.rows[1]['hands'][0]['opening'] = 2.
            else:
                envelope = {'link': 'gripper', 'center': [0., 0., 1.],
                            'rotation': [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]],
                            'half_size': [.01, .01, .01]}
                if kind == 'rotation':
                    envelope['rotation'][0][0] = 0.
                else:
                    envelope['half_size'][0] = 0.
                self.rows[1]['hands'][0]['finger_boxes'] = [envelope]
            with self.subTest(kind=kind):
                report = self.audit()
                self.assertFalse(report['checks']['current_scoring_evidence_valid']['passed'])

    def test_unknown_reason_or_nonzero_failure_is_not_whitelisted(self):
        for reason, score in (('unknown task failure', 0.),
                              ('a brick left the permitted table bounds', .25)):
            with self.subTest(reason=reason, score=score):
                value = {'result': {'score': score, 'invalid_reason': reason}}
                with patch.object(audit_runs, 'rescore', return_value=value):
                    report = self.audit()
                self.assertFalse(report['checks']['current_scoring_evidence_valid']['passed'])
                self.assertNotIn('task_failure_reason', report)


class DreamRecoveryTests(unittest.TestCase):
    def test_multiple_retry_attempts_are_not_multiple_recovered_requests(self):
        with tempfile.TemporaryDirectory() as temp:
            run = Path(temp)
            requests = [{'attempts': n, 'session_id': 'private-session-'+str(i)}
                        for i, n in enumerate((1, 2, 3))]
            evaluation = {'status': 'success', 'stats': {'total_steps': 3},
                          'results': {'errored_trials': 0},
                          'samples': [{'epochs': [{'task_score': 0}], 'policy_transcripts': [
                              {'model': 'dreamlabs/dream-1', 'dry_run': False, 'requests': requests}]}]}
            (run/'adhoc_test.json').write_text(json.dumps(evaluation))
            report = {'policy': 'dream', 'trajectory': {'actions_expected': 3}, 'checks': {}}
            audit_runs.evaluation_audit(run, report)
            self.assertEqual(report['dream']['retries'], 3)
            self.assertEqual(report['dream']['recovered_requests'], 2)
            self.assertNotIn('private-session', json.dumps(report))

    def test_public_scores_disclose_recovery_counts_without_diagnosing_cause(self):
        counts = {'requests': 25, 'attempts': 29, 'retries': 4, 'sessions': 5, 'recovered_requests': 4}
        runs = {'demo': {'score': 1.}, 'dream': {'score': 0., 'measured_metadata': {'dream_requests': counts}}}
        text = finalize_batch.scores_text(runs)
        self.assertLess(len(text), 300)
        self.assertIn('25 requests, 29 attempts, 4 retries across 5 sessions', text)
        self.assertIn('4 recovered requests', text)
        self.assertIn('effects are unknown', text)
        self.assertNotIn('session-expiry', text)
        self.assertNotIn('clean', text)
        counts.update(attempts=25, retries=0, sessions=1, recovered_requests=0)
        self.assertIn('0 retries across 1 session.', finalize_batch.scores_text(runs))

    def test_inconsistent_recovery_counts_fail_closed(self):
        counts = {'requests': 25, 'attempts': 29, 'retries': 4, 'sessions': 5, 'recovered_requests': 0}
        runs = {'demo': {'score': 1.}, 'dream': {'score': 0., 'measured_metadata': {'dream_requests': counts}}}
        with self.assertRaises(finalize_batch.FinalizationError):
            finalize_batch.scores_text(runs)


if __name__ == '__main__':
    unittest.main()
