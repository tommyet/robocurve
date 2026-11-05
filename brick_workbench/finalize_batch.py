r"""Audit and publish anonymous evidence for the four completed brick tasks.

Nothing is uploaded or submitted. All eight trials must pass the offline audit,
every demo must finish at 1.0, and each run must have a complete.mp4 composite.
Existing completed validation or an evidence directory is never overwritten.
Pending development VALIDATION.json files may be replaced after all gates pass.

Example (after the complete recordings and VM metadata have been downloaded):
  python brick_workbench/finalize_batch.py --repo . --artifact-root artifacts \
      --environment artifacts/environment-final.json \
      --probe-summary artifacts/brick-probe-005/summary.json --check-only

Omit --check-only to publish the checked results. --mapping accepts a JSON object
keyed by the four task names. Each value has demo and dream artifact directory
names, and optional demo_video/dream_video paths relative to --artifact-root.
Environment JSON accepts python/platform/gpu, packages/revisions maps, and
physics_configuration: {hz, constants_sha256, scene_sha256, adapter_revision}.
The latter records the actual VM adapter source configuration, not measured
physics-step telemetry. Runtime-recorded values take precedence; conflicts fail.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import tempfile

try:
    from . import audit_runs
except ImportError:
    import audit_runs


DEFAULT_RUNS = {
    'join-two-2x2-blocks': {'demo': 'brick-2x2-demo-004', 'dream': 'brick-2x2-dream-001'},
    'join-two-1x1-blocks': {'demo': 'brick-1x1-demo-002', 'dream': 'brick-1x1-dream-001'},
    'join-1x1-to-2x2': {'demo': 'brick-mixed-demo-002', 'dream': 'brick-mixed-dream-001'},
    'join-two-2x2-blocks-offset': {'demo': 'brick-offset-demo-002', 'dream': 'brick-offset-dream-001'},
}
SCHEMA = 'brick-batch-validation-v1'


class FinalizationError(ValueError):
    """An intentionally public, identifier-free diagnostic."""


def require(condition, message):
    if not condition:
        raise FinalizationError(message)


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def finite(value, *, positive=False):
    return (not isinstance(value, bool) and isinstance(value, (float, int))
            and math.isfinite(value) and (not positive or value > 0))


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def safe_label(value):
    # Environment metadata is an explicit allowlist, never a raw shell/log dump.
    require(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 ._()+:=\-]{0,199}', value),
            'Environment metadata contains an unsupported value; provide anonymous version labels only.')
    return value


def environment_values(source):
    require(isinstance(source, dict), 'Environment metadata must be a JSON object.')
    out = {}
    for key in ('python', 'platform', 'gpu'):
        if key in source:
            out[key] = safe_label(source[key])
    for group in ('packages', 'revisions'):
        if group not in source:
            continue
        require(isinstance(source[group], dict), 'Environment version groups must be objects.')
        out[group] = {}
        for name, value in source[group].items():
            safe_label(name)
            safe_label(value)
            if group == 'revisions':
                require(re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', value) is not None,
                        'Source revisions must be complete hexadecimal commit IDs.')
            out[group][name] = value
    return out


def merge_environment(runtime, supplemental):
    measured = environment_values(runtime)
    out = environment_values(supplemental)
    provenance = {key: 'supplemental VM environment export' for key in out}
    for key, value in measured.items():
        if key in ('packages', 'revisions'):
            previous = out.get(key, {})
            require(all(k not in previous or previous[k] == v for k, v in value.items()),
                    'Runtime and supplemental environment versions disagree.')
            out[key] = {**previous, **value}
        else:
            require(key not in out or out[key] == value,
                    'Runtime and supplemental environment metadata disagree.')
            out[key] = value
        provenance[key] = 'runtime.json; supplemental values only fill missing fields'
    require('python' in measured and measured.get('packages'),
            'Trial runtime must record Python and package versions.')
    return out, provenance


def physics_configuration(runtime, supplemental):
    if 'physics_hz' in runtime:
        require(finite(runtime['physics_hz']) and runtime['physics_hz'] == 240,
                'Unexpected runtime physics frequency.')
        return {'hz': 240, 'basis': 'Recorded in runtime.json.'}
    cfg = supplemental.get('physics_configuration')
    require(isinstance(cfg, dict),
            'Physics frequency was not recorded per run; supply actual VM adapter-source metadata in physics_configuration.')
    require(finite(cfg.get('hz')) and cfg['hz'] == 240,
            'Expected an adapter-source physics frequency of 240 Hz.')
    result = {'hz': 240}
    for key in ('constants_sha256', 'scene_sha256'):
        value = cfg.get(key)
        require(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None,
                'Physics configuration requires actual VM constants.py and scene.py SHA-256 hashes.')
        result[key] = value
    revision = cfg.get('adapter_revision')
    require(isinstance(revision, str) and re.fullmatch(r'[0-9a-f]{40}', revision) is not None,
            'Physics configuration requires the actual VM adapter commit.')
    require(supplemental.get('revisions', {}).get('yam-isaac-lab-arena') == revision,
            'Physics-source revision must match the supplemental VM adapter revision.')
    result.update(adapter_revision=revision,
                  source='yam_arena.constants.PHYSICS_DT applied by yam_arena.scene.env_cfg_callback',
                  basis='Adapter source configuration exported on the trial VM; not per-run physics-step telemetry.')
    return result


def resolve_inside(root, relative):
    require(isinstance(relative, str) and not Path(relative).is_absolute(),
            'Artifact mapping paths must be relative to the artifact root.')
    target = (root/relative).resolve()
    require(target.is_relative_to(root), 'Artifact mapping escapes the artifact root.')
    return target


def checked_mapping(mapping, artifact_root):
    require(isinstance(mapping, dict) and set(mapping) == set(DEFAULT_RUNS),
            'Mapping must contain exactly the four brick task names.')
    seen, out = set(), {}
    for task, item in mapping.items():
        require(isinstance(item, dict) and set(item) <= {'demo', 'dream', 'demo_video', 'dream_video'}
                and {'demo', 'dream'} <= set(item), 'Invalid run mapping fields.')
        out[task] = {}
        for policy in ('demo', 'dream'):
            run = resolve_inside(artifact_root, item[policy])
            require(re.fullmatch(r'brick-[a-z0-9-]+-(demo|dream)-\d{3}', run.name) is not None,
                    'Use anonymous descriptive brick run directory names.')
            require(run not in seen, 'Each final trial must have a distinct artifact directory.')
            seen.add(run)
            video = resolve_inside(artifact_root, item.get(policy+'_video', item[policy]+'/complete.mp4'))
            out[task][policy] = {'directory': run, 'video': video}
    return out


def read_existing(path):
    require(not path.is_symlink(), 'Publication destinations must not be symbolic links.')
    return path.read_bytes() if path.exists() else None


def preflight(repo, mapping):
    records = {}
    for name in mapping:
        task = repo/'tasks'/name
        require(task.is_dir() and not task.is_symlink(), 'A required task directory is missing or linked.')
        evidence = task/'evidence'
        require(not evidence.exists() and not evidence.is_symlink(),
                'An evidence directory already exists; final evidence is never overwritten.')
        task_raw = read_existing(task/'task.json')
        require(task_raw is not None, 'A required task.json is missing.')
        task_json = json.loads(task_raw)
        require(isinstance(task_json, dict), 'Task metadata must be a JSON object.')
        pending = read_existing(task/'VALIDATION.json')
        if pending is not None:
            prior = json.loads(pending)
            require(isinstance(prior, dict) and prior.get('validation_complete') is not True,
                    'Completed validation already exists and will not be overwritten.')
        core = {f: audit_runs.sha256(task/f) for f in audit_runs.BRICK_CORE}
        records[name] = {'task': task, 'task_raw': task_raw, 'task_json': task_json,
                         'pending': pending, 'core': core}
    return records


def curated_probe(source, name, task):
    summary = audit_runs.load_json(source)
    require(summary.get('not_a_task_demonstration') is True and summary.get('contact_processing_enabled') is True,
            'Material probe metadata must identify an instrumented standalone probe.')
    result = {'not_a_task_demonstration': True, 'calibrated_to_physical_bricks': False,
              'source_summary_sha256': audit_runs.sha256(source),
              'note': 'Controlled material-contact probe, not a robot task trial. Forces and penetration here are not measurements from the submitted robot demos.',
              'cases': {}}
    cases = summary.get('cases', [])
    for mode in ('aligned', 'misaligned_2mm', 'hover_2mm'):
        matches = [c for c in cases if c.get('case') == name+'__'+mode]
        require(len(matches) == 1, 'Material probe is missing a unique required control case.')
        case = matches[0]
        selected = {}
        for key in ('retained_with_correct_geometry_for_final_1s', 'airborne_for_final_1s',
                    'correct_geometry_for_final_1s', 'descent_limited',
                    'contact_reports_observed', 'brick_pair_contact_reports_observed'):
            require(isinstance(case.get(key), bool), 'Malformed material probe boolean.')
            selected[key] = case[key]
        selected['last_metrics'] = {}
        for key in ('lower_floor_clearance_m', 'seat_gap_m', 'target_xy_error_m', 'lower_tilt_deg'):
            value = case.get('last_metrics', {}).get(key)
            require(finite(value), 'Malformed material probe measurement.')
            selected['last_metrics'][key] = value
        selected['contact_diagnostics'] = {}
        for key in ('pair_normal_axis_force_N', 'hard_penetration_m', 'soft_penetration_m'):
            value = case.get('contact_diagnostics', {}).get(key)
            require(finite(value) or (key == 'pair_normal_axis_force_N' and value is None),
                    'Malformed material probe contact measurement.')
            selected['contact_diagnostics'][key] = value
        result['cases'][mode] = selected
    geometry = source.parent/'geometry.py'
    if geometry.is_file():
        result['probe_geometry_sha256'] = audit_runs.sha256(geometry)
        result['probe_geometry_matches_task'] = result['probe_geometry_sha256'] == audit_runs.sha256(task/'geometry.py')
    return result


def run_record(report, runtime, run_name, supplemental, supplemental_hash):
    require(report.get('passed') is True, 'A required offline run audit failed.')
    require(report['policy'] in ('demo', 'dream'), 'Unrecognized trial policy.')
    score = report['checks']['stored_final_score_agrees']['stored_score']
    replay = report['current_rescore']['result']['score']
    require(finite(score) and 0 <= score <= 1 and score == replay, 'Invalid or inconsistent final scores.')
    require(report['policy'] != 'demo' or score == 1., 'Every final demo must finish at full score.')
    require(runtime.get('control_hz') == 20 and report['trajectory']['control_hz'] == 20,
            'Final trials must record 20 Hz control.')
    require(finite(runtime.get('elapsed_wall_seconds'), positive=True), 'Measured runner wall time is missing.')
    require(isinstance(runtime.get('seed'), int) and not isinstance(runtime.get('seed'), bool), 'Trial seed is missing.')
    require(report['checks']['executed_actions']['limit_provenance']['source'] == 'recorded_by_audited_embodiment',
            'Final trials must record their own action limits.')
    environment, provenance = merge_environment(runtime, supplemental)
    physics = physics_configuration(runtime, supplemental)
    result = {
        'run_id': run_name, 'score': score, 'replay_score': replay, 'seed': runtime['seed'],
        'actions': report['checks']['executed_actions']['executed_actions'],
        'simulated_seconds': report['trajectory']['simulation_seconds'],
        'elapsed_wall_seconds': runtime['elapsed_wall_seconds'], 'control_hz': 20,
        'physics_hz': physics['hz'], 'physics_configuration': physics,
        'environment': environment, 'environment_provenance': provenance,
        'runtime_json_sha256': None,  # Filled from the actual input file by the caller.
        'supplemental_environment_sha256': supplemental_hash,
        'source_sha256': {k: v['current'] for k, v in report['checks']['core_source_provenance']['files'].items()},
        'evidence': {'trajectory': 'evidence/'+report['policy']+'.jsonl.gz',
                     'audit': 'evidence/'+report['policy']+'-audit.json',
                     **report['anonymous_evidence']},
        'measured_metadata': {'first_full_score_seconds': report['current_rescore']['first_full_score_seconds'],
                              'final_scorer_state': report['current_rescore']['result'],
                              'observations': report['trajectory']['observations'],
                              'maximum_sample_gap_seconds': report['trajectory']['maximum_step_gap_seconds'],
                              'submission_video': report['checks']['submission_video_format'],
                              'setup_image': report['checks']['setup_image']},
    }
    if 'dream' in report:
        result['measured_metadata']['dream_requests'] = report['dream']
    if 'task_failure_reason' in report:
        result['measured_metadata']['task_failure_reason'] = report['task_failure_reason']
    return result


def scores_text(runs):
    """Keep public scores short while disclosing measured Dream recoveries."""
    requests = runs['dream'].get('measured_metadata', {}).get('dream_requests', {})
    counts = {}
    for key in ('requests', 'attempts', 'retries', 'sessions', 'recovered_requests'):
        value = requests.get(key)
        require(isinstance(value, int) and not isinstance(value, bool) and value >= 0,
                'Final Dream scores require measured request and recovery counts.')
        counts[key] = value
    require(counts['requests'] > 0 and counts['attempts'] == counts['requests']+counts['retries']
            and 1 <= counts['sessions'] <= counts['requests']
            and 0 <= counts['recovered_requests'] <= min(counts['requests'], counts['retries'])
            and (counts['retries'] == 0) == (counts['recovered_requests'] == 0),
            'Inconsistent Dream request and recovery counts.')
    text = (f"Dream-1 run: {runs['dream']['score']:g}; demo: {runs['demo']['score']:g}. "
            f"Dream: {counts['requests']} requests, {counts['attempts']} attempts, "
            f"{counts['retries']} {'retry' if counts['retries'] == 1 else 'retries'} across {counts['sessions']} "
            f"{'session' if counts['sessions'] == 1 else 'sessions'}")
    if counts['recovered_requests']:
        text += (f" ({counts['recovered_requests']} recovered "
                 f"{'request' if counts['recovered_requests'] == 1 else 'requests'}); "
                 'recovery effects are unknown.')
    else:
        text += '.'
    require(len(text) < 300, 'Public score description exceeds the 300-character limit.')
    return text


def atomic_replace(path, content):
    with tempfile.NamedTemporaryFile(prefix='.finalize-', dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def verify_unchanged(records):
    """Recheck the whole batch, including for --check-only."""
    for name, record in records.items():
        task = record['task']
        require(not (task/'evidence').exists(), 'Evidence appeared while auditing; nothing will be overwritten.')
        require(read_existing(task/'task.json') == record['task_raw']
                and read_existing(task/'VALIDATION.json') == record['pending'],
                'Task metadata changed during the audit.')
        require(all(audit_runs.sha256(task/f) == h for f, h in record['core'].items()),
                'Task source changed during batch auditing.')


def publish(records, staged):
    # Also recheck each metadata file immediately before replacement, so
    # another agent's intervening edits survive.
    verify_unchanged(records)
    replaced, created = [], []
    try:
        for name, record in records.items():
            task, stage = record['task'], staged/name
            destination = task/'evidence'
            destination.mkdir()  # Exclusive creation; no existing evidence merges.
            created.append(destination)
            for source in (stage/'evidence').iterdir():
                with (destination/source.name).open('xb') as output:
                    output.write(source.read_bytes())
            for filename, before in (('VALIDATION.json', record['pending']), ('task.json', record['task_raw'])):
                path, after = task/filename, (stage/filename).read_bytes()
                require(read_existing(path) == before, 'Task metadata changed before publication.')
                atomic_replace(path, after)
                replaced.append((path, before, after))
    except BaseException:
        # Only undo files whose bytes are still exactly those we wrote.
        for path, before, after in reversed(replaced):
            if read_existing(path) == after:
                if before is None:
                    path.unlink()
                else:
                    atomic_replace(path, before)
        for destination in reversed(created):
            source_dir = staged/destination.parent.name/'evidence'
            for source in source_dir.iterdir():
                target = destination/source.name
                if target.is_file() and not target.is_symlink() and target.read_bytes() == source.read_bytes():
                    target.unlink()
            if not any(destination.iterdir()):
                destination.rmdir()
        raise


def finalize(repo, artifact_root, *, mapping=None, environment=None, probe_summary=None,
             ffmpeg=None, check_only=False):
    repo, artifact_root = Path(repo).resolve(), Path(artifact_root).resolve()
    mapping = checked_mapping(DEFAULT_RUNS if mapping is None else mapping, artifact_root)
    records = preflight(repo, mapping)
    supplemental = audit_runs.load_json(environment) if environment is not None else {}
    environment_values(supplemental)
    supplemental_hash = audit_runs.sha256(environment) if environment is not None else None
    decoder = shutil.which(ffmpeg or 'ffmpeg')
    if decoder is None:
        try:
            import imageio_ffmpeg
            decoder = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            pass
    require(decoder is not None, 'FFmpeg is required for complete video decoding.')
    outcomes, failures = {}, []
    with tempfile.TemporaryDirectory(prefix='.finalize-bricks-', dir=artifact_root) as temp:
        staged = Path(temp)
        for name, inputs in mapping.items():
            record, stage = records[name], staged/name
            (stage/'evidence').mkdir(parents=True)
            validation = {'schema': SCHEMA, 'validation_complete': False,
                          'generated_at_utc': datetime.now(timezone.utc).isoformat(),
                          'visual_review_complete': False, 'submission_ready': False,
                          'scope': 'Offline evidence consistency and a full-score simulated demonstration; user review and submission remain pending.',
                          'limitations': ['One fixed-seed trial per policy does not establish reliability.',
                                          'The contact model is not calibrated to physical printed bricks.',
                                          'Audit success does not guarantee competition acceptance.'], 'runs': {}}
            if record['pending'] is not None:
                validation['superseded_pending_validation_sha256'] = digest_bytes(record['pending'])
            outcomes[name] = {}
            versions = set()
            for policy in ('demo', 'dream'):
                run, video = inputs[policy]['directory'], inputs[policy]['video']
                try:
                    runtime_hash = audit_runs.sha256(run/'runtime.json')
                    runtime = audit_runs.load_json(run/'runtime.json')
                    require(runtime.get('policy') == policy, 'Artifact policy disagrees with final mapping.')
                    require(runtime.get('task_config', {}).get('name') == name, 'Artifact task disagrees with final mapping.')
                    report = audit_runs.audit_run(run, record['task'], ffmpeg=decoder,
                                                 anonymous_trace=stage/'evidence'/f'{policy}.jsonl.gz',
                                                 submission_video=video)
                    (stage/'evidence'/f'{policy}-audit.json').write_bytes(json_bytes(report))
                    failed = [k for k, v in report['checks'].items() if not v['passed']]
                    outcomes[name][policy] = {'audit_passed': report['passed'], 'failed_checks': failed,
                                              'score': report.get('current_rescore', {}).get('result', {}).get('score')}
                    data = run_record(report, runtime, run.name, supplemental, supplemental_hash)
                    require(audit_runs.sha256(run/'runtime.json') == runtime_hash,
                            'Runtime metadata changed during auditing.')
                    data['runtime_json_sha256'] = runtime_hash
                    data['evidence']['audit_sha256'] = audit_runs.sha256(stage/'evidence'/f'{policy}-audit.json')
                    validation['runs'][policy] = data
                    versions.add(safe_label(report['score_version']))
                except Exception as exc:
                    message = str(exc) if isinstance(exc, FinalizationError) else 'Required input missing or malformed ('+type(exc).__name__+').'
                    outcomes[name].setdefault(policy, {})['finalization_error'] = message
                    failures.append(name+'/'+policy)
            if len(validation['runs']) != 2:
                continue
            require(len(versions) == 1, 'Demo and Dream use different scorer versions.')
            validation['scorer_version'] = versions.pop()
            validation['validation_complete'] = True
            if probe_summary is not None:
                probe = curated_probe(probe_summary, name, record['task'])
                (stage/'evidence/material-probe.json').write_bytes(json_bytes(probe))
                validation['standalone_material_probe'] = {'file': 'evidence/material-probe.json',
                    'sha256': audit_runs.sha256(stage/'evidence/material-probe.json'), 'not_a_task_demonstration': True}
            updated = dict(record['task_json'])
            updated['scores'] = scores_text(validation['runs'])
            (stage/'task.json').write_bytes(json_bytes(updated))
            (stage/'VALIDATION.json').write_bytes(json_bytes(validation))
        if failures:
            return {'passed': False, 'published': False, 'failed_runs': failures, 'runs': outcomes}
        verify_unchanged(records)
        if environment is not None:
            require(audit_runs.sha256(environment) == supplemental_hash,
                    'Supplemental environment metadata changed during auditing.')
        if not check_only:
            publish(records, staged)
        return {'passed': True, 'published': not check_only, 'runs': outcomes,
                'note': 'Visual review, user review, media upload and submission remain separate steps.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--artifact-root', type=Path, required=True)
    parser.add_argument('--mapping', type=Path)
    parser.add_argument('--environment', type=Path)
    parser.add_argument('--probe-summary', type=Path)
    parser.add_argument('--ffmpeg')
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    lock = args.repo/'brick_workbench/.finalize-batch.lock'
    acquired = False
    try:
        lock.open('x').close()
        acquired = True
        result = finalize(args.repo, args.artifact_root,
                          mapping=audit_runs.load_json(args.mapping) if args.mapping else None,
                          environment=args.environment, probe_summary=args.probe_summary,
                          ffmpeg=args.ffmpeg, check_only=args.check_only)
    except Exception as exc:
        result = {'passed': False, 'published': False,
                  'reason': str(exc) if isinstance(exc, FinalizationError) else 'Input or publication failure ('+type(exc).__name__+'); existing evidence was not intentionally overwritten.'}
    finally:
        if acquired:
            lock.unlink(missing_ok=True)
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
