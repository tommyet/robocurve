"""Recompute geometry and certify full credit against the recorded native audit.

The certificate is recorded evidence, not cryptographic proof. A geometry-only
replay cannot establish that the native assessor or recording completed. Legacy
diagnostic traces remain useful for analysis and always receive task score zero.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np

from scoring import replay_file


def _near(actual, expected, tolerance=1e-8):
    return math.isfinite(float(actual)) and math.isclose(float(actual), float(expected), rel_tol=0, abs_tol=tolerance)


def _validate_transition(result, config, certificate):
    """Reject missing/inconsistent certification, including a failed final step."""
    if not isinstance(certificate, dict):
        raise ValueError('native transition certificate is missing')
    if certificate.get('status') != 'validated_intervals' or certificate.get('error'):
        raise ValueError('native transition did not validate every interval')
    for field, value in (('diagnostic_only', False), ('state_writes', False),
                         ('counter_writes', False), ('callback_removed', True)):
        if certificate.get(field) is not value:
            raise ValueError('native certificate has incorrect ' + field)
    hz = config['assay_physics_hz']
    if hz not in (480, 960) or config.get('physics_hz') != 240:
        raise ValueError('recorded task lacks the supported policy/assessor physics rates')
    substeps = hz // 20
    if certificate.get('control_hz') != 20 or certificate.get('target_physics_hz') != hz or certificate.get('requested_substeps') != substeps:
        raise ValueError('native certificate disagrees with recorded task rates')
    if not _near(certificate['old_physics_hz'], 240) or not _near(certificate['native_physics_dt_s'], 1/hz, 1e-9):
        raise ValueError('native certificate has incorrect physics timestep')
    if not certificate.get('state_sha256_before') or certificate['state_sha256_before'] != certificate.get('state_sha256_after'):
        raise ValueError('native transition did not preserve measured state')
    if not certificate.get('counters_before') or certificate['counters_before'] != certificate.get('counters_after'):
        raise ValueError('native transition did not preserve counters')
    policy_end = result['policy_end']
    if not policy_end or policy_end.get('qualified') is not True:
        raise ValueError('no independently qualifying policy-end knot')
    start = float(policy_end['time'])
    duration = float(result['seating']['required_seconds']) + float(config['proof_seconds'])
    count = round(duration * 20)
    if count <= 0 or not _near(count / 20, duration):
        raise ValueError('assessor duration does not contain whole control intervals')
    if not _near(certificate['switch_capture_time_s'], start) or not _near(result['time'], start + duration):
        raise ValueError('native certificate does not cover this trajectory assay')
    rows = certificate.get('intervals')
    if not isinstance(rows, list) or len(rows) != count or certificate.get('validated_control_intervals') != count:
        raise ValueError('native certificate has missing or extra assay intervals')
    for index, row in enumerate(rows):
        if row.get('validated') is not True or row.get('native_substeps') != substeps or not _near(row['capture_time_s'], start + (index + 1) / 20):
            raise ValueError('native interval is unvalidated or out of order')
        dts = np.asarray(row['native_callback_dt_s'], dtype=float)
        if dts.shape != (substeps,) or not np.isfinite(dts).all() or not np.allclose(dts, 1/hz, rtol=0, atol=1e-9):
            raise ValueError('native callback count or timestep is incorrect')
        if row.get('counter_deltas') != {'native': substeps, 'environment': substeps}:
            raise ValueError('native counters do not match the audited substeps')
        cameras = row.get('cameras', {})
        if 'review_cam' not in cameras or 'top_cam' not in cameras:
            raise ValueError('native interval lacks the recorded observation cameras')
        for camera in cameras.values():
            frame = np.asarray(camera['frame_delta'])
            stamp = np.asarray(camera['timestamp_s'], dtype=float)
            updated = np.asarray(camera['last_update_s'], dtype=float)
            expected = np.asarray(camera['float32_predicted_timestamp_s'], dtype=np.float32)
            tolerance = np.maximum(np.spacing(np.abs(expected)) * 2, 1e-7)
            if (frame.shape != (1,) or np.any(frame != 1) or stamp.shape != (1,)
                    or updated.shape != stamp.shape or expected.shape != stamp.shape
                    or not np.isfinite(stamp).all() or not np.isfinite(expected).all()
                    or np.any(updated != stamp) or np.any(np.abs(stamp - expected) > tolerance)):
                raise ValueError('native interval lacks one fresh camera frame')


def certify_result(result, config, certificate=None, *, finalization_complete=None, evidence_errors=()):
    """Keep geometry diagnostics, but only complete native evidence earns 1.0."""
    result = dict(result)
    result['geometric_score'] = result['score']
    diagnostic = bool(result.get('diagnostic_only') or config.get('diagnostic_only'))
    required = not diagnostic and (certificate is not None or result['score'] > .5 or result.get('policy_end') is not None)
    audit = {'required': required, 'status': 'not_required', 'errors': []}
    if diagnostic:
        result['score'] = 0.
        audit['status'] = 'diagnostic_only'
    elif required:
        audit['errors'].extend(evidence_errors)
        if finalization_complete is not True:
            audit['errors'].append('trial finalization is not certified complete')
        try:
            _validate_transition(result, config, certificate)
        except (KeyError, ValueError, TypeError, ArithmeticError, IndexError, AttributeError) as exc:
            audit['errors'].append(str(exc))
        audit['status'] = 'complete' if not audit['errors'] else 'incomplete'
        if audit['errors'] and result['score'] > .5:
            policy = result.get('policy_end') or {}
            result['score'] = .5 if policy.get('qualified') is True and result.get('invalid') is None else 0.
            result['status'] = 'policy-end knot; full assay evidence is not certified'
    result['assay_certification'] = audit
    result['score_scope'] = 'Geometry with native assessor and finalization certification for full credit'
    return result


def replay_trial(trajectory, runtime=None):
    """Load immutable trial artifacts; never trust their previously reported score."""
    trajectory = Path(trajectory)
    runtime = Path(runtime) if runtime else trajectory.parent / 'runtime.json'
    metadata = json.loads(runtime.read_text())
    config = metadata['task_config']
    if not all(name in config for name in ('length', 'mass', 'radius', 'segment')):
        raise ValueError('runtime.json lacks the recorded physical configuration')
    if metadata.get('score_version') == 'overhand-bimanual-v4':
        from bimanual_scoring import replay_file as replay_bimanual, certify_result as certify_bimanual
        result = replay_bimanual(trajectory, config)
        try:
            saved = json.loads((trajectory.parent / 'score-summary.json').read_text())
            finalization = saved.get('finalization') or {}
            completed = (metadata.get('finalization_complete') is True
                         and finalization.get('complete') is True
                         and not finalization.get('errors') and not finalization.get('interrupted_by'))
        except (OSError, ValueError, AttributeError):
            completed = False
        return certify_bimanual(result, finalization_complete=completed)
    result = replay_file(trajectory, config)
    evidence, errors = {}, []
    # Legacy diagnostic traces need no production certificate and stay zero.
    if not result.get('diagnostic_only') and not config.get('diagnostic_only'):
        for name in ('assay-physics-transition.json', 'score-summary.json'):
            path = trajectory.parent / name
            try:
                value = json.loads(path.read_text())
                if not isinstance(value, dict):
                    raise ValueError('evidence must be a JSON object')
                evidence[name] = value
            except (OSError, ValueError) as exc:
                errors.append(f'{name}: {type(exc).__name__}')
    saved_summary = evidence.get('score-summary.json') or {}
    finalization = saved_summary.get('finalization') or {}
    completed = (metadata.get('finalization_complete') is True
                 and finalization.get('complete') is True
                 and not finalization.get('errors') and not finalization.get('interrupted_by'))
    return certify_result(result, config, evidence.get('assay-physics-transition.json'),
                          finalization_complete=completed, evidence_errors=errors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trajectory', type=Path)
    parser.add_argument('--runtime', type=Path,
                        help='Saved runtime.json; defaults to the trajectory directory')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = replay_trial(args.trajectory, args.runtime)
    text = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(text)
    print(text, end='')


if __name__ == '__main__':
    main()
