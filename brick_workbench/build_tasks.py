"""Package four independent task folders from the maintained common sources.

Each folder is self-contained for a future one-task PR. Media and validated
scores are filled only after real trials; this builder never invents results.
"""
from pathlib import Path
import json
import math
import pprint
import shutil
from variants import VARIANTS, config
from geometry import DEFAULT_STIFFNESS, DEFAULT_DAMPING

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FILES = ('run.py', 'demo_policy.py', 'scoring.py', 'test_scoring.py', 'geometry.py',
         'hand_geometry.py', 'visuals.py', 'render_review.py', 'replay.py', 'telemetry.py')

def build():
    for name in VARIANTS:
        c = config(name)
        target = ROOT / 'tasks' / name
        target.mkdir(parents=True, exist_ok=True)
        validation = load_validation(target / 'VALIDATION.json')
        for filename in FILES:
            source = HERE / filename
            if source.exists():
                shutil.copy2(source, target / filename)
        shutil.copy2(HERE / 'task_template.py', target / 'task.py')
        (target / 'config.py').write_text('"""Fixed task scene and geometry; metres, kilograms, seconds."""\nCONFIG = ' + pprint.pformat(c, sort_dicts=True) + '\n')
        if (HERE / 'cad').exists():
            (target / 'cad').mkdir(exist_ok=True)
            for source in (HERE / 'cad').iterdir():
                if source.is_file() and source.name != 'render_targets.py':
                    shutil.copy2(source, target / 'cad' / source.name)
            # The illustration renderer compares all four tasks and belongs
            # in the workbench, not in a standalone submission.
            (target / 'cad' / 'render_targets.py').unlink(missing_ok=True)
        (target / 'README.md').write_text(readme(c, validation))
        (target / 'JUDGING.md').write_text(judging(c))
        details = target / 'task.json'
        previous = json.loads(details.read_text()) if details.exists() else {}
        fields = dict(title=c['title'], category='Societal relevance', keywords=['assembly', 'construction play', 'press fit'],
            instruction=c['instruction'],
            context='Joining toy bricks is a step in assisted play and model building. ' + task_distinction(c),
            setup=setup(c), scoring=rubric(c), run_limit='1,200 actions (60 seconds at 20 Hz)',
            reset_notes='Separate the bricks and return them upright to the fixed positions. Replace damaged printed parts.',
            fidelity='Custom PLA designs at Duplo scale, not official LEGO. Hollow rigid bodies and compliant socket contacts approximate a frictional press fit; no attachment joint. Plastic bending, fracture and print tolerances are not simulated. Fit, insertion force and pull-out force are uncalibrated against physical prints.',
            scores=previous.get('scores', 'Unvalidated development task; demo and Dream runs pending.'),
            media=previous.get('media', ''))
        details.write_text(json.dumps(fields, ensure_ascii=False, indent=2) + '\n')

def setup(c):
    def brick(role):
        shape = c[role + '_shape']
        size = ' × '.join(f'{16*n-.2:g}' for n in shape)
        x, y = c[role + '_xy']
        colour = 'blue' if role == 'lower' else 'red'
        return f'{colour} {shape[0]}×{shape[1]}, {size} mm footprint, {c[role+"_mass"]*1000:g} g model mass, body centre ({x:g}, {y:g}, 0.7571) m'
    return ('Two custom press-fit bricks, designed for solid printed PLA: ' + brick('lower') + '; ' + brick('upper') +
            '. Both have 19.2 mm bodies and 4.8 mm-high studs, 9.6 mm in diameter on a 16 mm grid. '
            'Studs face up; edges align with X/Y. Oak-coloured 1.10 × 1.30 m tabletop, '
            'centre X=0.36 m/Y=0, top Z=0.7475 m. Two YAM arms start in the station ready pose. '
            'Fixed layout, seed 0, no jitter. Printable CAD includes socket dimensions.')

def rubric(c):
    n = c['required_studs']
    studs = f'{n} '+('stud' if n == 1 else 'studs')
    yaw = ' Red 2×2 edges must align within 3°; quarter-turns are allowed.' if c['upper_shape'] == (2, 2) else ''
    return ('0.25: hold red’s lowest point ≥20 mm above the table for 0.20 s. '
            f'0.5: after pickup, seat exactly {studs} for 0.20 s: each stud/socket centre within 1 mm laterally '
            'and 0.75 mm of full insertion, relative tilt ≤3°.' + yaw +
            ' 1: also lift blue’s lowest point ≥20 mm for 1 s, holding red only, with all robot surfaces ≥2 mm from blue; '
            'then release for 1 s with blue’s bottom within 3 mm of the table, upright within 3°, both arms ≥5 mm clear '
            'of both bricks, and each brick stable within 2 mm/5°. '
            'Use the final score; separation or wrong alignment removes connection credit. '
            '0: no qualifying pickup, or any brick part leaves X[−0.17,0.89] m/Y[−0.63,0.63] m '
            '(20 mm inside the table edges) or falls >15 mm below the tabletop.')

def task_distinction(c):
    if c['required_studs'] == 4:
        return 'All four connections must hold the equal-sized bricks together.'
    if c['required_studs'] == 2:
        return 'A two-stud joint must support an overhanging brick; full overlap does not qualify.'
    if c['lower_shape'] == (1, 1):
        return 'The small bricks must stay joined by a single stud.'
    return 'One connection must support the larger base; any corner stud is allowed.'

def target_pose(c):
    if c['required_studs'] == 2:
        return ('Seated body centres are 16 mm apart along X or Y and aligned along the other axis. '
                'Either direction is allowed, leaving two blue studs exposed.')
    if c['lower_shape'] != c['upper_shape']:
        return ('Seated body centres differ by 8 mm along both X and Y, in either direction. '
                'One blue corner stud is covered and three remain exposed.')
    return 'Seated body centres line up horizontally, covering every blue stud.'

def load_validation(path):
    """Read final evidence, never infer completed trials from development notes.

    A final record has validation_complete=true and runs.demo/runs.dream,
    each with a numeric final score. Runtime fields are optional but are never
    filled from estimates. Malformed final records stop packaging rather than
    silently replacing previously recorded evidence with pending prose.
    """
    if not path.exists():
        return None
    record = json.loads(path.read_text())
    if not isinstance(record, dict) or record.get('validation_complete') is not True:
        return None
    runs = record.get('runs')
    for policy in ('demo', 'dream'):
        run = runs.get(policy) if isinstance(runs, dict) else None
        score = run.get('score') if isinstance(run, dict) else None
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError(f'{path}: completed validation requires runs.{policy}.score in [0, 1]')
    return record

def validation_status(record):
    if record is None:
        return '**Simulation status:** final trial evidence has not been recorded.'
    runs = record['runs']
    status = (f'**Verified simulation results:** demo {runs["demo"]["score"]:g}; '
              f'Dream-1 {runs["dream"]["score"]:g}. '
              'Replayed scores, source hashes and trial metadata are in [VALIDATION.json](VALIDATION.json). '
              'The task’s media record is listed in `task.json`.')
    if max(runs[p]['score'] for p in ('demo', 'dream')) < 1:
        status += ' A full-score feasibility demonstration is still required.'
    return status

def recorded_validation(record):
    """Render only measured runtime and explicitly recorded environment values.

    Environment schema: python/platform/gpu scalars plus packages/revisions maps.
    Each run may override those environment fields for its own recorded trial.
    No machine hostname, credentials, or absolute artifact paths are rendered.
    """
    if record is None:
        return ''
    def cell(value):
        if value is None:
            return 'Not recorded'
        if isinstance(value, float):
            return f'{value:.6g}'
        return str(value).replace('|', '\\|').replace('\n', ' ')
    fields = (('Run ID', 'run_id'), ('Final score', 'score'),
              ('Replay score', 'replay_score'), ('Seed', 'seed'),
              ('Executed actions', 'actions'), ('Simulated seconds', 'simulated_seconds'),
              ('Measured wall seconds', 'elapsed_wall_seconds'),
              ('Control Hz', 'control_hz'), ('Physics Hz', 'physics_hz'))
    lines = ['### Recorded simulation evidence', '',
             'Wall time includes simulator startup and trial execution.', '',
             '| Measurement | Demo | Dream |', '|---|---|---|']
    for label, key in fields:
        lines.append(f'| {label} | {cell(record["runs"]["demo"].get(key))} | {cell(record["runs"]["dream"].get(key))} |')
    if any('not per-run' in r.get('physics_configuration', {}).get('basis', '') for r in record['runs'].values()):
        lines.extend(['', 'Physics frequency comes from the installed adapter configuration, not per-run timing.'])
    requests = record['runs']['dream'].get('measured_metadata', {}).get('dream_requests', {})
    if requests:
        lines.extend(['',
            f'Dream request history: {cell(requests.get("requests"))} requests, '
            f'{cell(requests.get("attempts"))} attempts, {cell(requests.get("retries"))} '
            f'{"retry" if requests.get("retries") == 1 else "retries"}, '
            f'{cell(requests.get("sessions"))} {"session" if requests.get("sessions") == 1 else "sessions"}; '
            f'{cell(requests.get("recovered_requests"))} recovered '
            f'{"request" if requests.get("recovered_requests") == 1 else "requests"}.'])
        if isinstance(requests.get('retries'), int) and requests['retries'] > 0:
            lines.extend([
                'Retries reuse an observation window before the next action. Recovery can reset client',
                'action smoothing; server continuity and performance effects are uncertain.',
                'The counts alone do not identify each recovery’s cause.'])
    lines.extend(['', f'Scorer version: {cell(record.get("scorer_version"))}.', ''])
    environments = {}
    for policy in ('demo', 'dream'):
        environment = dict(record.get('environment') or {})
        overrides = record['runs'][policy].get('environment') or {}
        environment.update({k: v for k, v in overrides.items() if k not in ('packages', 'revisions')})
        for group in ('packages', 'revisions'):
            environment[group] = {**environment.get(group, {}), **overrides.get(group, {})}
        environments[policy] = environment
    common = environments['demo'] == environments['dream']
    lines.extend(['Both runs used the environment below.' if common else 'Recorded environments:', '',
                  '| Component | Version |' if common else '| Component | Demo | Dream |',
                  '|---|---|' if common else '|---|---|---|'])
    def environment_row(label, demo, dream):
        return f'| {label} | {cell(demo)} |' if common else f'| {label} | {cell(demo)} | {cell(dream)} |'
    for label, key in (('Python', 'python'), ('Platform', 'platform'), ('GPU', 'gpu')):
        lines.append(environment_row(label, environments['demo'].get(key), environments['dream'].get(key)))
    for group, label in (('packages', 'Package'), ('revisions', 'Source revision')):
        names = sorted(set(environments['demo'][group]) | set(environments['dream'][group]))
        for name in names:
            lines.append(environment_row(f'{label}: {cell(name)}', environments['demo'][group].get(name), environments['dream'][group].get(name)))
    lines.extend(['', '“Not recorded” means the metadata was unavailable.', ''])
    return '\n'.join(lines) + '\n'

def readme(c, validation=None):
    name = c['name']
    contact_evidence = 'Validate changed contact parameters in simulation before recording final evidence.'
    if validation is not None:
        contact_evidence = 'These parameters were used in the recorded robot trials.'
        if validation.get('standalone_material_probe'):
            contact_evidence += (' The separate [material probe](evidence/material-probe.json) checked '
                                 'aligned insertion, 2 mm misalignment and non-contact hover controls.')
        contact_evidence += ' Physical fit and force calibration remain unproven.'
    return f'''# {c['title']}

{c['instruction']}

Category: **Societal relevance**. Joining toy bricks is a step in assisted play
and model building.

{task_distinction(c)}
{target_pose(c)} At full insertion, red's body centre is 19.2 mm above blue's.
The studs sit inside the sockets, adding no gap between the bodies.

{validation_status(validation)}

## Setup

{setup(c)}

World X points away from the arm bases, Y left and Z up. Brick positions refer
to rectangular body centres, excluding studs. Red is uppermost when joined.
`config.py` fixes the layout; `cad/` contains printable geometry. Mounts,
cameras, camera stand and lighting use the installed YAM station. Review rulers
in `visuals.py` are visual only and cannot support objects.

These custom Duplo-scale parts are not official LEGO. Model masses come from
CAD volume at an assumed PLA density of 1.24 g/cm³: 3.907 g for 1×1 and 12.110 g
for 2×2. They are not measured prints. Fit, friction and compliance still need
physical calibration.

## Scoring

{rubric(c)}

See [JUDGING.md](JUDGING.md) for manual checks. Full credit requires unsupported
retention, followed by release. The scorer checks measured poses and collision
bounds for every link of both arms. Separation cancels connection credit and
the lift proof; a retry can still succeed. Report the final score.

## Reproduce a trial

Use the competition's Brev launchable with the YAM/Isaac environment and versions
listed below. Keep Dream credentials outside Git. From the repository root:

```bash
source ~/IsaacLab-Arena/yam.env
python -m unittest discover -s tasks/{name} -p 'test_*.py' -v
python tasks/{name}/demo_policy.py --check
python tasks/{name}/run.py --policy demo --seed 0 --max-steps 1200 --log-dir artifacts/{name}-demo-001
python tasks/{name}/run.py --policy dream --seed 0 --max-steps 1200 --log-dir artifacts/{name}-dream-001
python tasks/{name}/replay.py artifacts/{name}-demo-001/trajectory.jsonl
```

Rescore the included evidence with Python and NumPy; no GPU or API key is needed:

```bash
python tasks/{name}/replay.py tasks/{name}/evidence/demo.jsonl.gz
python tasks/{name}/replay.py tasks/{name}/evidence/dream.jsonl.gz
```

Use a new output directory each time and run through `run.py`. It builds the
hollow contact geometry and records robot state; the stock adapter alone
does not perform these steps.

Both policies share the recorded instruction, fixed scene, scorer and action
limits: 20 Hz control, 240 Hz physics, at most 1,200 actions (60 simulated seconds).
The scripted demo commands only joints and grippers. Once after pickup, it uses
measured brick and tool poses to correct placement for grasp offset, recorded
in `demo-corrections.json`. This is privileged demo feedback; Dream receives
only standard camera and robot observations. The demo cannot move bricks
directly or create attachments. Startup, rendering and API calls add wall time.

{recorded_validation(validation)}\
## Model and evidence

Rigid shapes form the hollow bodies, roofs and studs. Compliant socket rings
hold inserted studs by friction: radial interference 0.1 mm, stiffness
{DEFAULT_STIFFNESS:g} N/m, damping {DEFAULT_DAMPING:g} N·s/m, static friction 0.6 and dynamic friction 0.5.
These are simulation assumptions. There is no glue, proximity latch or attachment
joint. {contact_evidence}

Runs save measured brick and robot state in `trajectory.jsonl`, the final score
in `score-summary.json`, and source snapshots and runtime in `runtime.json`,
alongside setup images and footage. The three policy views are 320×176.
The separate 1600×1280 review view and visual rulers are not Dream inputs.

For final media, export the three recorded policy views with
`inspect-robots video EVAL.json --out RUN/media --fps 20`, then run
`python tasks/{name}/render_review.py RUN --output RUN/complete.mp4`.
The exporter preserves every recorded frame and verifies the frame count.
'''

def judging(c):
    count = c['required_studs']
    allowed = ('All four lower studs must be inserted.' if count == 4 else
               'Exactly one adjacent row or column of two lower studs must be inserted. Either axis and either direction are allowed. A full four-stud connection does not meet this target.' if count == 2 else
               'The single lower stud must be inserted.' if c['lower_shape'] == (1,1) else
               'Any one of the four lower studs may be inserted into the upper single-stud brick.')
    overlap_note = ('For the two-stud target, the known 2×2 grid and a one-pitch '
                    '(16 mm) shift imply one overlapping row. A hidden unused '
                    'stud can be inferred from the part geometry and visible '
                    'body edges; it need not be directly visible in every view.'
                    if count == 2 else '')
    alignment = ('Red’s edges must align with blue’s within 3°; quarter-turns are allowed.'
                 if c['upper_shape'] == (2, 2) else
                 'The single round connection allows any yaw where the bodies fit.')
    target_notes = '\n\n'.join(part for part in (target_pose(c), overlap_note) if part)
    return f'''# Judging: {c['title']}

Use the complete video, paused frames, a ruler or calipers, and a protractor.
Follow each brick throughout the trial. Red must finish above blue.
{allowed}

{target_notes}

| Score | Observable requirement |
|---|---|
| 0 | No qualifying pickup, or either brick leaves the permitted table area. |
| 0.25 | The robot holds red with its lowest point at least 20 mm above the table for 0.20 s. |
| 0.5 | After pickup, red is seated on blue in the required configuration for 0.20 s. |
| 1 | After seating, hold red only with blue's lowest point at least 20 mm above the table for 1 s; then leave the joined pair upright and released on the table for 1 s. |

**Seating:** each required stud/socket centre is within 1 mm laterally and
0.75 mm vertically of full insertion. Red's underside meets blue's body top;
stud height adds no gap. The bricks' upward axes differ by at most 3°.
{alignment}

Infer stud centres from the part drawings and visible body edges. Measure both
horizontal offsets in a top view and the body gap in a side view. The combined
lateral error must be ≤1 mm, not 1 mm per axis. Use timestamps for each hold
and views showing the table, bricks and both grippers. An oblique image alone
cannot establish hidden gaps or submillimetre seating.

**Lift:** every part of both arms stays ≥2 mm from blue, and the required
connection holds for the whole second. Gripping blue, supporting it directly or
balancing a loose stack does not qualify. The automated grasp check requires
both finger collision bounds within 1 mm of red's body and the tool centre
within 35 mm. Bounds cover all collision meshes of both arms.

**Finish:** blue's bottom is within 3 mm of the table and its upward axis within
3° of vertical. Both arms are ≥5 mm from both bricks. Each brick stays within
2 mm and 5° of its pose at the start of a continuous one-second rest. Exceeding
either limit restarts that interval.

**Bounds:** every part of each brick, including studs, stays within X[−0.17,0.89] m
and Y[−0.63,0.63] m. A lowest point >15 mm below the table, or leaving these
bounds, makes the final score zero. The simulation has no destructible parts.

Use the final state. Retries are allowed within 1,200 actions. Pickup credit
survives a normal failed join. Separation or wrong alignment removes connection
credit and the lift proof. Correct seating earns 0.5 without a completed lift
and released finish; earlier higher scores do not persist.

Samples are 50 ms apart; durations use timestamps. Gaps >75 ms reset active
timing windows. Malformed, nonfinite or non-increasing evidence invalidates the
automated score. Replay with the archived source. Visual rulers are useful only
in their own planes; perspective changes the scale elsewhere.
'''

if __name__ == '__main__':
    build()
