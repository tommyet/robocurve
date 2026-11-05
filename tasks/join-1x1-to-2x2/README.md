# Join a 1×1 block to a 2×2 block

Press the red block onto the blue block, connecting one stud. Lift the pair by the red block alone so the blue block is at least 2 cm above the table for one second. Set the joined pair down upright and let go for one second. Any of the blue block's four studs is allowed.

Category: **Societal relevance**. Joining construction pieces is a basic step in
assisting someone with hands-on play and model building.

The small upper piece must retain the larger base through one chosen stud; any corner is valid.
At full seating, the upper body centre is 8 mm from the lower centre along each horizontal axis. Either sign on each axis is allowed: one corner stud is covered and three remain exposed. In every case, the upper body centre is 19.2 mm above the lower
body centre at full seating; the studs enter the sockets rather than adding
another 4.8 mm between bodies. These are nominal target relations; the scoring
tolerances below determine acceptance.

**Simulation results complete:** the final demo score is 1; the final Dream score is 0. The recorded evidence is in [VALIDATION.json](VALIDATION.json). User review, media upload and submission are still pending.

## Setup

Two custom press-fit bricks with solid printed PLA as the material target: blue 2×2 brick: 31.8 × 31.8 mm footprint, 19.2 mm body plus 4.8 mm studs, 12.11 g model mass, body centre (0.26, 0.1, 0.7571) m; red 1×1 brick: 15.8 × 15.8 mm footprint, 19.2 mm body plus 4.8 mm studs, 3.907 g model mass, body centre (0.2, 0.2, 0.7571) m. Studs face up; edges align with world X/Y. Stud pitch 16 mm; diameter 9.6 mm. Oak-coloured 1.10 × 1.30 m tabletop, centre X=0.36 m/Y=0, top Z=0.7475 m. Two YAM arms start in the station ready pose. No layout jitter. Printable CAD and exact socket dimensions are included.

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

0: no qualifying pickup. 0.25: hold red’s lowest point at least 20 mm above the table for 0.20 s. 0.5: after pickup, seat exactly 1 stud(s), centre error ≤1 mm, gap ≤0.75 mm and tilt ≤3°, for 0.20 s. 1: also hold blue’s lowest point ≥20 mm above the table for 1 s while holding red only, then release the pair for 1 s: blue bottom within 3 mm of table, upright within 3°, both arms ≥5 mm clear, both bricks stable within 2 mm/5°. During lift, all robot surfaces must be ≥2 mm from blue. Use final score; separation removes connection credit. Score 0 if any brick part exits X[−0.17,0.89] m/Y[−0.63,0.63] m (20 mm inside table edges) or falls >15 mm below the tabletop.

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
python -m unittest discover -s tasks/join-1x1-to-2x2 -p 'test_*.py' -v
python tasks/join-1x1-to-2x2/demo_policy.py --check
python tasks/join-1x1-to-2x2/run.py --policy demo --seed 0 --max-steps 1200 --log-dir artifacts/join-1x1-to-2x2-demo-001
python tasks/join-1x1-to-2x2/run.py --policy dream --seed 0 --max-steps 1200 --log-dir artifacts/join-1x1-to-2x2-dream-001
python tasks/join-1x1-to-2x2/replay.py artifacts/join-1x1-to-2x2-demo-001/trajectory.jsonl
```

The included evidence can also be rescored locally with Python and NumPy;
no GPU or API key is needed:

```bash
python tasks/join-1x1-to-2x2/replay.py tasks/join-1x1-to-2x2/evidence/demo.jsonl.gz
python tasks/join-1x1-to-2x2/replay.py tasks/join-1x1-to-2x2/evidence/dream.jsonl.gz
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

### Recorded simulation evidence

These are the final recorded trials, not runtime estimates. Wall time includes
the runner's measured startup and execution interval.

| Measurement | Demo | Dream |
|---|---|---|
| Run ID | brick-mixed-demo-002 | brick-mixed-dream-001 |
| Final score | 1 | 0 |
| Replay score | 1 | 0 |
| Seed | 0 | 0 |
| Executed actions | 400 | 1200 |
| Simulated seconds | 20 | 60 |
| Measured wall seconds | 107.38 | 264.635 |
| Control Hz | 20 | 20 |
| Physics Hz | 240 | 240 |

Physics frequency is verified from the installed adapter source configuration;
it was not separately timed during each run.

Dream request history: 25 requests, 26 attempts, 1 retry, 2 sessions; 1 recovered request.
A recovered request retries an observation window before the next executed action.
Session recovery can reset client action smoothing; server continuity and the effect
on performance are uncertain. These counts do not identify the cause of each recovery.

Scorer version: brick-join-v1.

Recorded environment and source revisions:

| Component | Demo | Dream |
|---|---|---|
| Python | 3.12.16 | 3.12.16 |
| Platform | Linux-6.8.0-1066-aws-x86_64-with-glibc2.35 | Linux-6.8.0-1066-aws-x86_64-with-glibc2.35 |
| GPU | NVIDIA L40S | NVIDIA L40S |
| Package: dreamlabs-client | 1.0.14 | 1.0.14 |
| Package: inspect-robots | 0.60.0 | 0.60.0 |
| Package: inspect-robots-dream | 0.1.0 | 0.1.0 |
| Package: inspect-robots-yam | 0.37.0 | 0.37.0 |
| Package: isaaclab | 17.0.2 | 17.0.2 |
| Package: isaacsim | 6.1.0.0 | 6.1.0.0 |
| Package: numpy | 2.3.1 | 2.3.1 |
| Package: yam-arena | 0.1.0 | 0.1.0 |
| Source revision: IsaacLab | 37ddf626871758333d6ed89cf64ad702aef127d0 | 37ddf626871758333d6ed89cf64ad702aef127d0 |
| Source revision: IsaacLab-Arena | c7edf3a9d5d8276565208f72422f8f8a0806d6cf | c7edf3a9d5d8276565208f72422f8f8a0806d6cf |
| Source revision: yam-isaac-lab-arena | 0059d02a1a91bc6834c1d0846022891df0c78730 | 0059d02a1a91bc6834c1d0846022891df0c78730 |

Use these recorded versions and revisions when reproducing the final evidence.
“Not recorded” marks missing metadata; it is not a claimed version or measurement.

## Model and evidence

Hard collision shapes form the hollow body, roof and studs. Segmented socket
rings retain inserted studs using compliant contact and friction. The default
radial interference is 0.1 mm, contact stiffness 500 N/m, damping 1 N·s/m,
static friction 0.6 and dynamic friction 0.5. These are trial engineering
parameters, not measured Duplo material properties. No automatic glue,
proximity latch or fixed attachment joint is used. These parameters were used in the recorded robot trials. The separate [material probe](evidence/material-probe.json) checked aligned insertion, 2 mm misalignment and non-contact hover controls. Physical fit and force calibration remain unproven.

Each run saves measured brick roots, both arms' measured link envelopes, joints
and timestamps in `trajectory.jsonl`; the final score in `score-summary.json`;
source snapshots/hashes and measured runtime in `runtime.json`; setup images;
and complete review footage. The three 320×176 policy cameras remain unchanged.
A separate 1600×1280 close-up and passive metric guides aid review and are not
additional Dream observations. The guides have no collision geometry.

For final media, export the three recorded policy views with
`inspect-robots video EVAL.json --out RUN/media --fps 20`, then run
`python tasks/join-1x1-to-2x2/render_review.py RUN --output RUN/complete.mp4`.
The exporter preserves every recorded frame and verifies the frame count.
Upload media and open a single-task PR only after user review and authorization.
