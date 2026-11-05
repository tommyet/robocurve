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
            context='Joining construction pieces supports assistance with hands-on play and model building. ' + task_distinction(c),
            setup=setup(c), scoring=rubric(c), run_limit='1,200 actions (60 seconds at 20 Hz)',
            reset_notes='Separate the bricks and return them upright to the fixed positions. Replace damaged printed parts.',
            fidelity='Custom printable press-fit bricks at Duplo scale, not official LEGO parts. Rigid hollow shapes use compliant contact and friction at socket rings; no attachment joint. Contact overlap approximates local compliance: plastic bending, fracture and print tolerances are not simulated. Fit, insertion force and pull-out force have not been calibrated to physical prints.',
            scores=previous.get('scores', 'Unvalidated development task; demo and Dream runs pending.'),
            media=previous.get('media', ''))
        details.write_text(json.dumps(fields, ensure_ascii=False, indent=2) + '\n')

def setup(c):
    def brick(role):
        shape = c[role + '_shape']
        size = ' × '.join(f'{16*n-.2:g}' for n in shape)
        x, y = c[role + '_xy']
        colour = 'blue' if role == 'lower' else 'red'
        return f'{colour} {shape[0]}×{shape[1]} brick: {size} mm footprint, 19.2 mm body plus 4.8 mm studs, {c[role+"_mass"]*1000:g} g model mass, body centre ({x:g}, {y:g}, 0.7571) m'
    return ('Two custom press-fit bricks with solid printed PLA as the material target: ' + brick('lower') + '; ' + brick('upper') +
            '. Studs face up; edges align with world X/Y. Stud pitch 16 mm; diameter 9.6 mm. '
            'Oak-coloured 1.10 × 1.30 m tabletop, centre X=0.36 m/Y=0, top Z=0.7475 m. '
            'Two YAM arms start in the station ready pose. No layout jitter. Printable CAD and exact socket dimensions are included.')

def rubric(c):
    n = c['required_studs']
    yaw = ' Edge alignment must also be within 3° for the red 2×2 brick.' if c['upper_shape'] == (2, 2) else ''
    return (f'0: no qualifying pickup. 0.25: hold red’s lowest point at least 20 mm above the table for 0.20 s. '
            f'0.5: after pickup, seat exactly {n} stud(s), centre error ≤1 mm, gap ≤0.75 mm and tilt ≤3°, for 0.20 s. '
            '1: also hold blue’s lowest point ≥20 mm above the table for 1 s while holding red only, then release the pair for 1 s: '
            'blue bottom within 3 mm of table, upright within 3°, both arms ≥5 mm clear, both bricks stable within 2 mm/5°. '
            'During lift, all robot surfaces must be ≥2 mm from blue.' + yaw + ' Use final score; separation removes connection credit. '
            'Score 0 if any brick part exits X[−0.17,0.89] m/Y[−0.63,0.63] m (20 mm inside table edges) or falls >15 mm below the tabletop.')

def task_distinction(c):
    if c['required_studs'] == 4:
        return 'The target requires simultaneous seating and retention at four stud/socket locations on equal-size pieces.'
    if c['required_studs'] == 2:
        return 'The target requires a 16 mm offset and two-stud retention with an overhanging upper piece; full overlap is excluded.'
    if c['lower_shape'] == (1, 1):
        return 'The target requires gripping two small pieces and retaining their single stud/socket connection.'
    return 'The small upper piece must retain the larger base through one chosen stud; any corner is valid.'

def target_pose(c):
    if c['required_studs'] == 2:
        return ('At full seating, the horizontal body-centre offset is 16 mm along either axis and zero along the other. '
                'Either sign is allowed: one adjacent row or column overlaps and two lower studs remain exposed.')
    if c['lower_shape'] != c['upper_shape']:
        return ('At full seating, the upper body centre is 8 mm from the lower centre along each horizontal axis. '
                'Either sign on each axis is allowed: one corner stud is covered and three remain exposed.')
    return 'At full seating, the horizontal body centres coincide and every lower stud is covered.'

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
        return '''**Development status:** local code and printable geometry are prepared. Physical
simulation, full-score demonstration and fresh Dream results are still pending.
This folder is for review; it is not ready to submit. `task.json` deliberately
has no media ID or claimed trial scores.'''
    runs = record['runs']
    status = (f'**Simulation results complete:** the final demo score is {runs["demo"]["score"]:g}; '
              f'the final Dream score is {runs["dream"]["score"]:g}. '
              'The recorded evidence is in [VALIDATION.json](VALIDATION.json). '
              'User review, media upload and submission are still pending.')
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
             'These are the final recorded trials, not runtime estimates. Wall time includes',
             'the runner\'s measured startup and execution interval.', '',
             '| Measurement | Demo | Dream |', '|---|---|---|']
    for label, key in fields:
        lines.append(f'| {label} | {cell(record["runs"]["demo"].get(key))} | {cell(record["runs"]["dream"].get(key))} |')
    if any('not per-run' in r.get('physics_configuration', {}).get('basis', '') for r in record['runs'].values()):
        lines.extend(['', 'Physics frequency is verified from the installed adapter source configuration;',
                      'it was not separately timed during each run.'])
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
                'A recovered request retries an observation window before the next executed action.',
                'Session recovery can reset client action smoothing; server continuity and the effect',
                'on performance are uncertain. These counts do not identify the cause of each recovery.'])
    lines.extend(['', f'Scorer version: {cell(record.get("scorer_version"))}.', '',
                  'Recorded environment and source revisions:', '',
                  '| Component | Demo | Dream |', '|---|---|---|'])
    environments = {}
    for policy in ('demo', 'dream'):
        environment = dict(record.get('environment') or {})
        overrides = record['runs'][policy].get('environment') or {}
        environment.update({k: v for k, v in overrides.items() if k not in ('packages', 'revisions')})
        for group in ('packages', 'revisions'):
            environment[group] = {**environment.get(group, {}), **overrides.get(group, {})}
        environments[policy] = environment
    for label, key in (('Python', 'python'), ('Platform', 'platform'), ('GPU', 'gpu')):
        lines.append(f'| {label} | {cell(environments["demo"].get(key))} | {cell(environments["dream"].get(key))} |')
    for group, label in (('packages', 'Package'), ('revisions', 'Source revision')):
        names = sorted(set(environments['demo'][group]) | set(environments['dream'][group]))
        for name in names:
            lines.append(f'| {label}: {cell(name)} | {cell(environments["demo"][group].get(name))} | {cell(environments["dream"][group].get(name))} |')
    lines.extend(['', 'Use these recorded versions and revisions when reproducing the final evidence.',
                  '“Not recorded” marks missing metadata; it is not a claimed version or measurement.', ''])
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

Category: **Societal relevance**. Joining construction pieces is a basic step in
assisting someone with hands-on play and model building.

{task_distinction(c)}
{target_pose(c)} In every case, the upper body centre is 19.2 mm above the lower
body centre at full seating; the studs enter the sockets rather than adding
another 4.8 mm between bodies. These are nominal target relations; the scoring
tolerances below determine acceptance.

{validation_status(validation)}

## Setup

{setup(c)}

World X points away from the arm bases, Y left and Z up. Origins refer to the
centre of each brick's rectangular body, excluding its studs. Red is the upper
piece and blue the lower piece. All starts use seed 0 and the station ready pose.
See `config.py` for the fixed values and `cad/` for printable geometry.
The table is fixed and rendered with a wood-like finish. Robot mounts, cameras,
camera stand and lighting use the calibrated YAM station in the installed
adapter. The added review rulers are visual references with no collision or
support effect; their exact dimensions and placement are in `visuals.py`.

These are custom parts at Duplo scale, including the single-stud design. They
are not official LEGO parts. The material target is solid printed PLA (density assumption 1.24 g/cm³); the socket
fit, friction and compliance require physical calibration before claiming
matched real-world performance. Model masses are rounded CAD-volume estimates: 3.907 g for 1×1 and 12.110 g for 2×2, not measured prints.

## Scoring

{rubric(c)}

The detailed manual procedure is in [JUDGING.md](JUDGING.md). Correct seating
alone earns partial credit. Full credit requires visible retention while the
lower brick has no external support. The scorer uses measured poses and
conservative collision envelopes for every link of both arms. It does not use
an attachment flag. Later separation removes the seating credit and lift proof;
an ordinary retry can still succeed within the time limit. Report the final
score, never the highest score seen earlier.

## Reproduce a trial

Use the competition's Brev launchable and retained YAM/Isaac environment. Keep
Dream credentials outside Git. Run from the repository root:

```bash
source ~/IsaacLab-Arena/yam.env
python -m unittest discover -s tasks/{name} -p 'test_*.py' -v
python tasks/{name}/demo_policy.py --check
python tasks/{name}/run.py --policy demo --seed 0 --max-steps 1200 --log-dir artifacts/{name}-demo-001
python tasks/{name}/run.py --policy dream --seed 0 --max-steps 1200 --log-dir artifacts/{name}-dream-001
python tasks/{name}/replay.py artifacts/{name}-demo-001/trajectory.jsonl
```

The included evidence can also be rescored locally with Python and NumPy;
no GPU or API key is needed:

```bash
python tasks/{name}/replay.py tasks/{name}/evidence/demo.jsonl.gz
python tasks/{name}/replay.py tasks/{name}/evidence/dream.jsonl.gz
```

Use a fresh output directory for each attempt. The task requires `run.py`:
it replaces the task file's placeholder boxes with compound hollow bricks
before the simulator starts. Running the task through the stock adapter alone
does not create the intended contact geometry or required robot telemetry.

Both policies use the same instruction, fixed scene, scorer, 20 Hz control,
240 Hz physics and standard action limits. The demonstration only commands
robot joints and grippers. After pickup it uses measured simulator brick/TCP
poses once to correct the remaining placement targets for grasp offset. This
privileged scripted feedback is recorded in `demo-corrections.json`; Dream
receives only its standard camera and robot observations. The demonstration
cannot set brick poses or create attachments.
The limit is 1,200 actions, or 60 simulated seconds. Record actual wall time;
simulation startup, rendering and Dream requests add time beyond this limit.

{recorded_validation(validation)}\
## Model and evidence

Hard collision shapes form the hollow body, roof and studs. Segmented socket
rings retain inserted studs using compliant contact and friction. The default
radial interference is 0.1 mm, contact stiffness {DEFAULT_STIFFNESS:g} N/m, damping {DEFAULT_DAMPING:g} N·s/m,
static friction 0.6 and dynamic friction 0.5. These are trial engineering
parameters, not measured Duplo material properties. No automatic glue,
proximity latch or fixed attachment joint is used. {contact_evidence}

Each run saves measured brick roots, both arms' measured link envelopes, joints
and timestamps in `trajectory.jsonl`; the final score in `score-summary.json`;
source snapshots/hashes and measured runtime in `runtime.json`; setup images;
and complete review footage. The three 320×176 policy cameras remain unchanged.
A separate 1600×1280 close-up and passive metric guides aid review and are not
additional Dream observations. The guides have no collision geometry.

For final media, export the three recorded policy views with
`inspect-robots video EVAL.json --out RUN/media --fps 20`, then run
`python tasks/{name}/render_review.py RUN --output RUN/complete.mp4`.
The exporter preserves every recorded frame and verifies the frame count.
Upload media and open a single-task PR only after user review and authorization.
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
    return f'''# Judging: {c['title']}

Use the complete trial video, a ruler or calipers, a protractor, and paused frames. Follow
the same physical brick through the trial. Red must finish above blue.
{allowed}

{target_pose(c)}

{overlap_note}

| Score | Observable requirement |
|---|---|
| 0 | No qualifying pickup, or either brick leaves the permitted table area. |
| 0.25 | The robot holds red with its lowest point at least 20 mm above the table for 0.20 s. |
| 0.5 | After pickup, red is seated on blue in the required configuration for 0.20 s. |
| 1 | After seating, hold red only with blue's lowest point at least 20 mm above the table for 1 s; then leave the joined pair upright and released on the table for 1 s. |

Seated means the required {count} stud/socket centre matches are within 1 mm
laterally and 0.75 mm vertically of full insertion. The undersides of red's body
and the top of blue's body meet at full insertion; stud height does not add an
extra gap between the bodies. Their upward axes differ by at most 3°. Two 2×2
pieces also align their edges within 3°, allowing quarter-turn symmetry. A
single round stud permits arbitrary yaw where the physical bodies fit.

For a manual check, infer the stud centres from the supplied part drawings and
the visible body edges; the socket interiors need not be visible. Measure the
two horizontal offsets in a top view and the body-to-body gap in a side view.
The combined lateral mismatch of each required pair must be at most 1 mm,
not 1 mm independently on each axis. Use elapsed video timestamps for each
hold, and views where the table, both bricks and both grippers remain visible.
An oblique image alone cannot resolve hidden gaps or submillimetre seating.

During the lift proof, every part of both arms must be at least 2 mm clear of
blue. Blue must retain the required pose relative to red for the whole second.
Supporting blue directly, gripping both bricks, or balancing a loose stack does
not establish retention. The robot must actually hold red: the automated check
requires both named finger envelopes to lie within 1 mm of red's body, with the
holding TCP within 35 mm. Robot-link envelopes are conservative bounds derived
from all collision meshes, not point estimates at the fingertips.

At the finish, blue's bottom is within 3 mm of the table and its up axis within
3° of vertical. Both arms are at least 5 mm clear of both bricks. Each brick's
position remains within 2 mm and full orientation within 5° of its pose at the
start of a continuous one-second rest interval. Drifting outside these limits
restarts the interval. Small harmless movement inside the limits is allowed.

The permitted region contains the entire brick, including studs: X from
−0.17 to 0.89 m, Y from −0.63 to 0.63 m. A brick's lowest point more than 15 mm
below the table also invalidates the trial. Falling off or leaving these bounds
makes the final score zero. The rigid-body simulation has no destructible parts.

Judge the state at the end. A failed attempt may be retried within 1,200 actions.
Pickup credit survives a normal failed joining attempt. Separation or the wrong
final configuration removes connection credit and resets the lift proof. Correct
seating without the proof earns 0.5. A valid lift without a released stable finish
also earns 0.5. No historical maximum is substituted for the final score.

The audit samples every 50 ms. Durations use timestamps, not frame counts alone.
Missing intervals longer than 75 ms reset active timing windows; malformed,
nonfinite or non-increasing evidence invalidates the automated score. For replay,
use the source archived with the trial. The passive rulers help interpretation;
perspective is not a universal millimetre scale away from their planes.
'''

if __name__ == '__main__':
    build()
