"""Independent certificate checks with synthetic telemetry, not physical success."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from config import CONFIG, POLICY_PHYSICS_SCHEDULE
from replay import _validate_policy_transition, replay_trial
from test_runner import FakeTransition


def certificate(actions):
    count = max(0, actions - 1560)
    native = None
    if count:
        switch = FakeTransition(None, 960, 78.)
        switch.start()
        for i in range(count):
            switch.before_step(78.+i/20, 1561+i)
            switch.after_step(78.+(i+1)/20, 1562+i)
        switch.close()
        native = switch.report
    return dict(schema='fixed-policy-physics-v1', schedule=POLICY_PHYSICS_SCHEDULE,
                status='complete' if count else 'not_reached', error=None,
                completed_actions=actions, pending_interval=False,
                final_capture_time_s=actions/20, expected_control_intervals=count,
                closed=True, native_transition=native, policy_actions_modified=False,
                external_force_path_called=False)


class PolicyReplayTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        self.path = self.folder / 'trajectory.jsonl'
        self.config = dict(CONFIG, physics_hz=240)

    def samples(self, actions):
        self.path.write_text(''.join(json.dumps(dict(time=i/20, phase='policy'))+'\n'
                                     for i in range(actions+1)))

    def test_early_boundary_and_complete_intervals(self):
        for actions in (0, 1559, 1560, 1562):
            self.samples(actions)
            _validate_policy_transition(self.path, self.config, certificate(actions))

    def test_failed_malformed_or_truncated_evidence_rejected(self):
        self.samples(1562)
        mutations = [
            lambda c: c.update(status='failed'),
            lambda c: c.update(error='caught native error'),
            lambda c: c.update(closed=False),
            lambda c: c.update(pending_interval=True),
            lambda c: c.update(completed_actions=1561),
            lambda c: c.update(final_capture_time_s=78.05),
            lambda c: c.update(policy_actions_modified=True),
            lambda c: c.update(external_force_path_called=True),
            lambda c: c['schedule'].update(target_physics_hz=480),
            lambda c: c['native_transition'].update(callback_removed=False),
            lambda c: c['native_transition'].update(state_sha256_after='different'),
            lambda c: c['native_transition']['intervals'].pop(),
            lambda c: c['native_transition']['intervals'][-1].update(capture_time_s=78.15),
            lambda c: c['native_transition']['intervals'][0].update(native_callback_dt_s=[1/240]*48),
            lambda c: c['native_transition']['intervals'][0]['cameras']['top_cam'].update(frame_delta=[0]),
        ]
        for mutate in mutations:
            c = deepcopy(certificate(1562))
            mutate(c)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                _validate_policy_transition(self.path, self.config, c)

    def test_trajectory_clock_is_independent_of_frozen_scorer_time(self):
        self.samples(1562)
        metadata = dict(task_config=self.config, score_version='overhand-bimanual-v4',
                        finalization_complete=True, audited_final_score=1.)
        (self.folder/'runtime.json').write_text(json.dumps(metadata))
        (self.folder/'score-summary.json').write_text(json.dumps(dict(
            score=1., finalization=dict(complete=True))))
        geometry = dict(score=0., time=78.05, invalid='rope contact', status='invalid')
        with patch('bimanual_scoring.replay_file', return_value=geometry):
            (self.folder/'policy-physics-transition.json').write_text(json.dumps(certificate(1562)))
            result = replay_trial(self.path)
            self.assertEqual(result['score'], 0.)
            self.assertEqual(result['policy_physics_certification']['status'], 'complete')

    def test_missing_certificate_blocks_any_score_and_old_v4_is_unchanged(self):
        self.samples(1562)
        metadata = dict(task_config=self.config, score_version='overhand-bimanual-v4',
                        finalization_complete=True, audited_final_score=0.)
        (self.folder/'runtime.json').write_text(json.dumps(metadata))
        (self.folder/'score-summary.json').write_text(json.dumps(dict(
            score=0., finalization=dict(complete=True))))
        geometry = dict(score=1., time=78.1, invalid=None, status='complete')
        with patch('bimanual_scoring.replay_file', return_value=geometry):
            result = replay_trial(self.path)
            self.assertEqual(result['score'], 0.)
            self.assertEqual(result['geometric_score'], 1.)
            (self.folder/'policy-physics-transition.json').write_text(json.dumps(certificate(1562)))
            self.assertEqual(replay_trial(self.path)['score'], 1.)
            del metadata['task_config']['policy_physics_schedule']
            (self.folder/'runtime.json').write_text(json.dumps(metadata))
            (self.folder/'policy-physics-transition.json').unlink()
            result = replay_trial(self.path)
            self.assertEqual(result['score'], 1.)
            self.assertEqual(result['policy_physics_certification']['status'], 'not_required')
            metadata['execution'] = dict(status='failed', errors=['PolicyError'])
            (self.folder/'runtime.json').write_text(json.dumps(metadata))
            self.assertEqual(replay_trial(self.path)['score'], 0.)

    def test_gaps_duplicate_samples_and_nonpolicy_frames_fail(self):
        for mutation in (dict(time=.10, phase='policy'), dict(time=0., phase='policy'),
                         dict(time=.05, phase='proof')):
            self.path.write_text(json.dumps(dict(time=0., phase='policy'))+'\n'+json.dumps(mutation)+'\n')
            with self.assertRaises(ValueError):
                _validate_policy_transition(self.path, self.config, certificate(1))

    def test_truncated_gzip_returns_incomplete_certification(self):
        compressed = self.folder/'trajectory.jsonl.gz'
        data = gzip.compress((json.dumps(dict(time=0., phase='policy'))+'\n').encode())
        compressed.write_bytes(data[:-4])
        (self.folder/'runtime.json').write_text(json.dumps(dict(
            task_config=self.config, score_version='overhand-bimanual-v4', finalization_complete=True)))
        (self.folder/'policy-physics-transition.json').write_text(json.dumps(certificate(0)))
        with patch('bimanual_scoring.replay_file', return_value=dict(score=0., invalid='truncated')):
            result = replay_trial(compressed)
        self.assertEqual(result['score'], 0.)
        self.assertEqual(result['policy_physics_certification']['status'], 'incomplete')


if __name__ == '__main__':
    unittest.main()
