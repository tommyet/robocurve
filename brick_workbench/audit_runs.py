"""Audit a finished trial offline and optionally export anonymous numeric evidence.

Example:
  python brick_workbench/audit_runs.py artifacts/RUN --task-dir tasks/TASK \
      --output artifacts/RUN/audit.json --anonymous-trace tasks/TASK/evidence/demo.jsonl.gz

Final runs record their own action limits. Older runs can use --yam-source PATH
to derive limits from a local YAM checkout; that fallback and its source hashes
are explicitly reported. This script never uploads data. Reports omit local
paths, user/run/session identifiers, request bodies and operator text. A failed
or unavailable required check prevents an overall pass; a zero task score does
not by itself mean the run audit failed.
"""

from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

import numpy as np


BRICK_CORE = ('config.py', 'task.py', 'scoring.py', 'geometry.py', 'hand_geometry.py',
              'run.py', 'demo_policy.py', 'telemetry.py', 'visuals.py')
DIE_CORE = ('task.py', 'scoring.py', 'run.py', 'demo_policy.py', 'visuals.py')
ROBOT_LINKS = {'base', 'gripper', 'tip_left', 'tip_right', 'link1', 'link2', 'link3', 'link4', 'link5'}
TASK_FAILURE_REASONS = {'a brick left the permitted table bounds'}
TOL = 1e-9


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path):
    with Path(path).open() as stream:
        return json.load(stream)


def load_rows(path):
    opener = gzip.open if Path(path).suffix == '.gz' else open
    with opener(path, 'rt') as stream:
        return [json.loads(line) for line in stream if line.strip()]


def literal_config(path):
    """Read generated CONFIG without executing arbitrary configuration code."""
    tree = ast.parse(Path(path).read_text())
    for statement in tree.body:
        if isinstance(statement, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'CONFIG' for t in statement.targets):
            value = ast.literal_eval(statement.value)
            if isinstance(value, dict):
                return value
    raise ValueError('generated CONFIG literal was not found')


def scoring_module(path):
    name = '_offline_audit_scoring_'+sha256(path)[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def rescore(rows, source):
    module = scoring_module(source/'scoring.py')
    if hasattr(module, 'BrickScorer'):
        tracker = module.BrickScorer(literal_config(source/'config.py'))
        result = tracker.result
    elif hasattr(module, 'RollTracker'):
        tracker = module.RollTracker()
        result = tracker.summary
    else:
        raise ValueError('unsupported scorer interface')
    first_full = None
    for sample in anonymous_rows(rows):
        tracker.update(sample)
        state = result()
        if state['score'] == 1. and first_full is None:
            first_full = float(sample['time'])
    return {'result': result(), 'first_full_score_seconds': first_full}


def check(report, name, passed, **details):
    report['checks'][name] = {'passed': bool(passed), **details}


def source_audit(run, task, runtime, report):
    core = BRICK_CORE if (task/'config.py').exists() else DIE_CORE
    recorded = runtime.get('source_sha256', {})
    details = {}
    for filename in core:
        archived, current = run/'task-source'/filename, task/filename
        item = {'recorded': recorded.get(filename),
                'archived': sha256(archived) if archived.is_file() else None,
                'current': sha256(current) if current.is_file() else None}
        item['matches'] = item['recorded'] is not None and item['recorded'] == item['archived'] == item['current']
        details[filename] = item
    check(report, 'core_source_provenance', all(v['matches'] for v in details.values()), files=details)
    if 'config.py' in core and (run/'task-source/config.py').is_file() and 'task_config' in runtime:
        normalize = lambda value: json.dumps(value, sort_keys=True)
        check(report, 'runtime_config_matches_snapshot',
              normalize(runtime['task_config']) == normalize(literal_config(run/'task-source/config.py')))


def trajectory_audit(rows, run, task, runtime, report):
    hz = float(runtime.get('control_hz', 20))
    times = np.array([s['time'] for s in rows], dtype=float)
    valid_time = len(times) > 0 and np.isfinite(times).all() and hz > 0 and math.isfinite(hz)
    gaps = np.diff(times) if valid_time else np.array([])
    timing_ok = valid_time and abs(float(times[0])) <= TOL and np.all(gaps > 0) and np.all(np.abs(gaps-1/hz) <= 1e-7)
    report['trajectory'] = {'observations': len(rows), 'actions_expected': max(0, len(rows)-1),
                            'control_hz': hz, 'first_time': float(times[0]) if valid_time else None,
                            'simulation_seconds': float(times[-1]) if valid_time else None,
                            'maximum_step_gap_seconds': float(gaps.max()) if len(gaps) else None}
    check(report, 'trajectory_timing', timing_ok)
    check(report, 'run_limit', len(rows)-1 <= int(runtime.get('max_steps', 1200)),
          max_steps=int(runtime.get('max_steps', 1200)))
    for label, source in (('archived', run/'task-source'), ('current', task)):
        try:
            report[label+'_rescore'] = rescore(rows, source)
            state = report[label+'_rescore']['result']
            invalid = state.get('invalid_reason', state.get('invalid'))
            # A valid recording of a task failure is still valid evidence.
            # Only this exact scorer-defined outcome is allowed; malformed
            # evidence and unfamiliar invalidation reasons remain failures.
            task_failure = invalid in TASK_FAILURE_REASONS and state.get('score') == 0
            check(report, label+'_scoring_evidence_valid', invalid is None or task_failure,
                  task_failure_reason=invalid if task_failure else None)
            if label == 'current' and task_failure:
                report['task_failure_reason'] = invalid
        except Exception as exc:
            check(report, label+'_scoring_evidence_valid', False, error_type=type(exc).__name__)
    if 'archived_rescore' in report and 'current_rescore' in report:
        check(report, 'archived_and_current_score_agree',
              report['archived_rescore']['result']['score'] == report['current_rescore']['result']['score'])
    summary = run/'score-summary.json'
    if summary.is_file() and 'current_rescore' in report:
        stored = load_json(summary)
        check(report, 'stored_final_score_agrees',
              stored.get('score') == report['current_rescore']['result']['score'],
              stored_score=stored.get('score'))
    else:
        check(report, 'stored_final_score_agrees', False, reason='summary or rescore unavailable')


def action_limits(runtime, yam_source=None):
    if 'action_limits' in runtime:
        limits = runtime['action_limits']
        return {key: np.asarray(limits[key], dtype=float) for key in ('low', 'high', 'max_step')}, {
            'source': 'recorded_by_audited_embodiment'}
    if yam_source is None:
        raise ValueError('no recorded limits; supply a verified local YAM source checkout')
    sys.path.insert(0, str(yam_source))
    try:
        from yam_arena import ik, YAM_URDF, constants
        hz = float(runtime.get('control_hz', 20))
        single_low, single_high = np.r_[ik.LOWER, 0.], np.r_[ik.UPPER, 1.]
        step = ([constants.SHOULDER['velocity']/hz]*3
                +[constants.WRIST['velocity']/hz]*3
                +[constants.GRIPPER['velocity']/abs(constants.FINGER_OPEN)/hz])
        return {'low': np.tile(single_low, 2), 'high': np.tile(single_high, 2),
                'max_step': np.array(step*2)}, {
                    'source': 'derived_from_supplied_local_YAM_checkout_not_recorded_during_trial',
                    'urdf_sha256': sha256(YAM_URDF), 'constants_sha256': sha256(constants.__file__)}
    finally:
        sys.path.pop(0)


def audit_actions(run, runtime, report, yam_source=None):
    paths = sorted((run/'actions').rglob('*.jsonl')) if (run/'actions').is_dir() else []
    if len(paths) != 1:
        check(report, 'executed_actions', False, reason='expected exactly one action log', log_count=len(paths))
        return
    try:
        records = load_rows(paths[0])
        headers = [r for r in records if r.get('kind') == 'header']
        actions = [r for r in records if 'action' in r]
        array = np.asarray([r['action'] for r in actions], dtype=float)
        limits, provenance = action_limits(runtime, yam_source)
        if (len(headers) != 1 or array.ndim != 2 or array.shape[1] != 14
                or headers[0].get('action_dim') != 14
                or any(v.shape != (14,) or not np.isfinite(v).all() for v in limits.values())
                or np.any(limits['low'] > limits['high']) or np.any(limits['max_step'] <= 0)):
            raise ValueError('invalid action/limit dimensions')
        finite = np.isfinite(array).all(axis=1)
        bad_range = (~finite) | np.any((array < limits['low']-TOL) | (array > limits['high']+TOL), axis=1)
        deltas = np.abs(np.diff(array, axis=0))
        bad_delta = (~np.isfinite(deltas).all(axis=1)) | np.any(deltas > limits['max_step']+TOL, axis=1)
        indices = [r.get('t') for r in actions]
        continuous = indices == list(range(len(actions)))
        count_match = len(actions) == report['trajectory']['actions_expected']
        details = {'source_action_log_sha256': sha256(paths[0]), 'executed_actions': len(actions),
                   'range_violation_rows': int(bad_range.sum()), 'delta_violation_rows': int(bad_delta.sum()),
                   'continuous_step_indices': continuous, 'matches_trajectory_actions': count_match,
                   'numeric_tolerance': TOL, 'limit_provenance': provenance,
                   'low': limits['low'].tolist(), 'high': limits['high'].tolist(),
                   'maximum_step': limits['max_step'].tolist(),
                   'observed_maximum_adjacent_step': np.max(deltas, axis=0).tolist() if len(deltas) else None,
                   'note': 'Approved executed actions only. First action has no previous-action comparison; prediction clipping counts are separate.'}
        check(report, 'executed_actions', not bad_range.any() and not bad_delta.any() and continuous and count_match, **details)
    except Exception as exc:
        check(report, 'executed_actions', False, error_type=type(exc).__name__,
              reason='action log or limit provenance unavailable/invalid')


def evaluation_audit(run, report):
    candidates = list(run.glob('adhoc_*.json'))
    if len(candidates) != 1:
        check(report, 'evaluation_log', False, reason='expected exactly one Inspect evaluation log', count=len(candidates))
        return
    evaluation = load_json(candidates[0])
    samples = evaluation.get('samples', [])
    status = evaluation.get('status')
    reasons = [reason for s in samples for reason in s.get('termination_reasons', [])]
    safe_reasons = {'success', 'max_steps', 'max_seconds', 'policy_stop', 'request_stop', 'error', 'cancelled'}
    total_steps = evaluation.get('stats', {}).get('total_steps')
    result = {'status': status if status in ('success', 'error', 'cancelled') else 'other',
              'termination_reasons': [r if r in safe_reasons else 'other' for r in reasons],
              'total_steps': total_steps, 'errored_trials': evaluation.get('results', {}).get('errored_trials')}
    scores = [epoch.get('task_score') for s in samples for epoch in s.get('epochs', [])]
    result['task_scores'] = scores
    check(report, 'evaluation_log', status == 'success' and evaluation.get('error') is None
          and evaluation.get('results', {}).get('errored_trials') == 0
          and all(s.get('error') is None for s in samples)
          and total_steps == report['trajectory']['actions_expected'] and len(scores) == 1,
          **result)
    if len(scores) == 1 and 'current_rescore' in report:
        check(report, 'evaluation_score_agrees', scores[0] == report['current_rescore']['result']['score'])
    transcripts = [t for s in samples for t in s.get('policy_transcripts', []) if isinstance(t, dict)]
    requests = [r for t in transcripts for r in t.get('requests', [])]
    if report['policy'] == 'dream':
        attempts = [r.get('attempts') for r in requests]
        known_attempts = all(isinstance(v, int) and not isinstance(v, bool) and v >= 1 for v in attempts)
        sessions = {r['session_id'] for r in requests if r.get('session_id')}
        session_missing = sum(not r.get('session_id') for r in requests)
        attempts_total = sum(attempts) if known_attempts else None
        total = lambda key: sum(r[key] for r in requests) if all(isinstance(r.get(key), (int, float)) for r in requests) else None
        models = {t.get('model') for t in transcripts if t.get('model')}
        report['dream'] = {
            'model': next(iter(models)) if len(models) == 1 and next(iter(models)).startswith('dreamlabs/') else 'unreported_or_multiple',
            'transport': 'direct', 'requests': len(requests), 'attempts': attempts_total,
            'retries': attempts_total-len(requests) if attempts_total is not None else None,
            'recovered_requests': sum(v > 1 for v in attempts) if known_attempts else None,
            'sessions': len(sessions) if session_missing == 0 else None,
            'requests_missing_session_evidence': session_missing,
            'reported_model_inference_ms': total('infer_ms'),
            'returned_prediction_rows': total('rows'),
            'returned_prediction_rows_beyond_limits': total('rows_beyond_limits'),
            'note': 'Aggregates only; session IDs and request content are omitted. Returned rows can include unused chunk rows. Inference time is not a billing total.',
        }
        check(report, 'dream_request_evidence', len(requests) > 0 and known_attempts and session_missing == 0
              and all(t.get('dry_run') is False for t in transcripts))


def fast_start(path):
    atoms = []
    size = Path(path).stat().st_size
    with Path(path).open('rb') as stream:
        offset = 0
        while offset+8 <= size:
            stream.seek(offset)
            length, tag = struct.unpack('>I4s', stream.read(8))
            header = 8
            if length == 1:
                length = struct.unpack('>Q', stream.read(8))[0]
                header = 16
            if length == 0:
                length = size-offset
            if length < header or offset+length > size:
                return False
            atoms.append(tag)
            offset += length
    return b'moov' in atoms and b'mdat' in atoms and atoms.index(b'moov') < atoms.index(b'mdat')


def decode_video(path, ffmpeg):
    decoded = subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'info', '-i', str(path),
                              '-map', '0:v:0', '-an', '-f', 'null', '-', '-progress', 'pipe:1', '-nostats'],
                             capture_output=True, text=True)
    counts = re.findall(r'^frame=(\d+)$', decoded.stdout, flags=re.M)
    stream_lines = [line for line in decoded.stderr.splitlines() if 'Video:' in line]
    stream = stream_lines[0] if stream_lines else ''
    codec = re.search(r'Video:\s*([A-Za-z0-9_]+)', stream)
    dimensions = re.search(r'\b(\d{2,5})x(\d{2,5})\b', stream)
    fps = re.search(r'([0-9.]+) fps', stream)
    return {'fully_decoded': decoded.returncode == 0 and bool(counts),
            'frames': int(counts[-1]) if counts else None,
            'codec': codec.group(1) if codec else None,
            'pixel_format': 'yuv420p' if re.search(r'\byuv420p\b', stream) else 'other_or_unknown',
            'width': int(dimensions.group(1)) if dimensions else None,
            'height': int(dimensions.group(2)) if dimensions else None,
            'fps': float(fps.group(1)) if fps else None,
            'fast_start': fast_start(path), 'bytes': Path(path).stat().st_size,
            'sha256': sha256(path)}


def media_audit(run, report, ffmpeg, submission_video=None):
    review = run/'review-video.json'
    if review.is_file():
        metadata = load_json(review)
        t = report['trajectory']
        metadata_ok = (metadata.get('frames') == t['observations']
                       and abs(float(metadata.get('fps', 0))-t['control_hz']) <= TOL
                       and abs(float(metadata.get('first_time', -1))-t['first_time']) <= 1e-7
                       and abs(float(metadata.get('last_time', -1))-t['simulation_seconds']) <= 1e-7
                       and metadata.get('sent_to_dream') is False)
        check(report, 'review_metadata_timing', metadata_ok,
              frames=metadata.get('frames'), fps=metadata.get('fps'),
              first_time=metadata.get('first_time'), last_time=metadata.get('last_time'),
              sent_to_dream=metadata.get('sent_to_dream'))
    else:
        check(report, 'review_metadata_timing', False, reason='review-video.json missing')
    videos = {'review': run/'review.mp4'}
    for camera in ('top_cam', 'left_cam', 'right_cam'):
        candidates = list((run/'media').glob('*_'+camera+'.mp4'))
        if len(candidates) == 1:
            videos[camera] = candidates[0]
        else:
            check(report, 'video_'+camera, False, reason='expected exactly one exported policy video', count=len(candidates))
    for label, path in videos.items():
        if not path.is_file() or ffmpeg is None:
            check(report, 'video_'+label, False, reason='video or decoder unavailable')
            continue
        details = decode_video(path, ffmpeg)
        passed = (details['fully_decoded'] and details['frames'] == report['trajectory']['observations']
                  and details['codec'] == 'h264' and details['pixel_format'] == 'yuv420p'
                  and details['fps'] == report['trajectory']['control_hz'])
        check(report, 'video_'+label, passed, **details)
    if submission_video is not None:
        if submission_video.is_file() and ffmpeg is not None:
            details = decode_video(submission_video, ffmpeg)
            passed = (details['fully_decoded'] and details['frames'] == report['trajectory']['observations']
                      and details['codec'] == 'h264' and details['pixel_format'] == 'yuv420p'
                      and details['fps'] == report['trajectory']['control_hz'] and details['fast_start']
                      and details['bytes'] <= 50_000_000)
            check(report, 'submission_video_format', passed, **details)
        else:
            check(report, 'submission_video_format', False, reason='submission video or decoder unavailable')
    setup = run/'setup.png'
    if setup.is_file():
        signature = setup.read_bytes()[:24]
        is_png = signature[:8] == b'\x89PNG\r\n\x1a\n'
        width, height = struct.unpack('>II', signature[16:24]) if is_png and len(signature) >= 24 else (0, 0)
        check(report, 'setup_image', is_png and width > 0 and height > 0 and setup.stat().st_size <= 10_000_000,
              bytes=setup.stat().st_size, width=width, height=height, sha256=sha256(setup),
              note='Dimensions/signature/size only; visual correspondence still requires human review.')
    else:
        check(report, 'setup_image', False, reason='setup.png missing')


def numbers(value, shape):
    array = np.asarray(value, dtype=float)
    if array.shape != shape or not np.isfinite(array).all():
        raise ValueError('unexpected or nonfinite numeric evidence')
    return array.tolist()


def rotation_numbers(value):
    result = numbers(value, (3, 3))
    matrix = np.asarray(result)
    if not np.allclose(matrix.T@matrix, np.eye(3), atol=1e-5) or abs(np.linalg.det(matrix)-1) > 1e-5:
        raise ValueError('invalid rotation evidence')
    return result


def anonymous_rows(rows):
    """Explicit allowlist; never forward arbitrary metrics, events or free text."""
    sanitized = []
    for source in rows:
        now = float(source['time'])
        if not math.isfinite(now):
            raise ValueError('nonfinite time')
        target = {'time': now}
        bodies = ('upper', 'lower') if 'upper' in source else (None,)
        for role in bodies:
            body = source[role] if role else source
            out = {'pos': numbers(body['pos'], (3,)), 'quat_xyzw': numbers(body['quat_xyzw'], (4,))}
            # Validate every record even after a permanent task failure makes
            # the stateful scorer stop examining subsequent observations.
            quaternion_norm = float(np.linalg.norm(out['quat_xyzw']))
            if not math.isfinite(quaternion_norm) or quaternion_norm < 1e-12:
                raise ValueError('invalid quaternion evidence')
            for key in ('lin_vel', 'ang_vel', 'low', 'high'):
                if key in body:
                    out[key] = numbers(body[key], (3,))
            if role:
                target[role] = out
            else:
                target.update(out)
        target['hands'] = []
        if len(source['hands']) != 2:
            raise ValueError('expected two arms')
        for hand in source['hands']:
            opening = float(hand['opening'])
            if not math.isfinite(opening) or not 0 <= opening <= 1:
                raise ValueError('invalid normalized opening')
            out = {'tcp': numbers(hand['tcp'], (3,)), 'opening': opening}
            for key, shape in (('joints', (6,)), ('tcp_rotation', (3, 3)), ('closing_axis', (3,))):
                if key in hand:
                    out[key] = rotation_numbers(hand[key]) if key == 'tcp_rotation' else numbers(hand[key], shape)
            if 'finger_boxes' in hand:
                out['finger_boxes'] = []
                for i, box in enumerate(hand['finger_boxes']):
                    link = box.get('link')
                    half_size = numbers(box['half_size'], (3,))
                    if any(v <= 0 for v in half_size):
                        raise ValueError('invalid collision envelope dimensions')
                    out['finger_boxes'].append({
                        'link': link if link in ROBOT_LINKS else 'extra_envelope_'+str(i),
                        'center': numbers(box['center'], (3,)), 'rotation': rotation_numbers(box['rotation']),
                        'half_size': half_size})
            target['hands'].append(out)
        sanitized.append(target)
    return sanitized


def export_anonymous(rows, target, task, expected_result):
    if target.exists():
        raise FileExistsError('choose a fresh anonymous trace path')
    clean = anonymous_rows(rows)
    result = rescore(clean, task)['result']
    if result != expected_result:
        raise ValueError('anonymous trace changes the rescore result')
    raw = ''.join(json.dumps(row, separators=(',', ':'), allow_nan=False)+'\n' for row in clean).encode()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as sink:
        with gzip.GzipFile(filename='', mode='wb', fileobj=sink, mtime=0) as stream:
            stream.write(raw)
    return {'schema': 'allowlisted numeric measured states; public robot-link names only',
            'observations': len(clean), 'decoded_sha256': hashlib.sha256(raw).hexdigest(),
            'gzip_sha256': sha256(target), 'gzip_bytes': target.stat().st_size,
            'same_rescore_result': True, 'original_metrics_removed': True,
            'note': 'Curated numeric copy, not a byte-identical copy of the original trajectory.'}


def audit_run(run, task, *, ffmpeg=None, yam_source=None, anonymous_trace=None, submission_video=None):
    runtime = load_json(run/'runtime.json')
    trajectory = run/'trajectory.jsonl'
    if not trajectory.exists():
        trajectory = run/'trajectory.jsonl.gz'
    rows = load_rows(trajectory)
    report = {'audit_version': 'robot-trial-offline-v1', 'policy': runtime.get('policy') if runtime.get('policy') in ('demo', 'dream') else 'unknown',
              'seed': runtime.get('seed'), 'score_version': runtime.get('score_version'),
              'elapsed_wall_seconds': runtime.get('elapsed_wall_seconds'),
              'input_trajectory_sha256': sha256(trajectory), 'checks': {},
              'limits': ['An audit pass establishes internal evidence consistency, not physical calibration, statistical reliability or competition acceptance.',
                         'Visual review of the complete videos and setup is still required.']}
    source_audit(run, task, runtime, report)
    trajectory_audit(rows, run, task, runtime, report)
    audit_actions(run, runtime, report, yam_source)
    evaluation_audit(run, report)
    media_audit(run, report, ffmpeg, submission_video)
    if anonymous_trace is not None:
        try:
            report['anonymous_evidence'] = export_anonymous(rows, anonymous_trace, task, report['current_rescore']['result'])
            check(report, 'anonymous_evidence_preserves_result', True)
        except Exception as exc:
            check(report, 'anonymous_evidence_preserves_result', False, error_type=type(exc).__name__)
    files = report['checks']['core_source_provenance']['files']
    changed = [name for name, item in files.items()
               if not (task/name).is_file() or sha256(task/name) != item['current']]
    check(report, 'sources_unchanged_during_audit', not changed, changed_files=changed)
    report['passed'] = all(item['passed'] for item in report['checks'].values())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir', type=Path)
    parser.add_argument('--task-dir', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--anonymous-trace', type=Path)
    parser.add_argument('--submission-video', type=Path, help='also verify final upload encoding, size and fast start')
    parser.add_argument('--yam-source', type=Path)
    parser.add_argument('--ffmpeg', default='ffmpeg')
    args = parser.parse_args()
    decoder = shutil.which(args.ffmpeg)
    if decoder is None:
        try:
            import imageio_ffmpeg
            decoder = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            pass
    try:
        report = audit_run(args.run_dir, args.task_dir, ffmpeg=decoder,
                           yam_source=args.yam_source, anonymous_trace=args.anonymous_trace,
                           submission_video=args.submission_video)
    except Exception as exc:
        # Avoid echoing exception strings that can include private local paths.
        report = {'audit_version': 'robot-trial-offline-v1', 'passed': False,
                  'fatal_error_type': type(exc).__name__, 'reason': 'Required audit input is missing or malformed.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    failures = [name for name, item in report.get('checks', {}).items() if not item['passed']]
    print(json.dumps({'passed': report['passed'], 'failed_checks': failures,
                      'fatal_error_type': report.get('fatal_error_type'),
                      'final_score': report.get('current_rescore', {}).get('result', {}).get('score')}, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
