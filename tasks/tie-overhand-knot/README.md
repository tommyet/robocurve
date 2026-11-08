# Tie an overhand knot

**The first full demo scores 1.0 in independent replay.** Trial 020 completes
the task in 138.30 seconds. The matching Dream run is in progress; submission
is still pending.

Tie one overhand knot in the blue cord. Pull its ends at least 117 cm apart
for one second with the whole cord at least 1 cm above the table. Let go and
leave the knot intact for five seconds. This is a basic cord-fastening task;
it does not test load capacity or whether the knot stops a particular eyelet.

## Setup

One blue, round polyester cord lies flat in an uncrossed U. There are no pegs,
clamps or attachments. Its diameter is 10 mm, nominal centreline length is
130 cm, outside length including rounded end caps is 131 cm, and mass is
97.11 g. The terminal 12.5 mm links are yellow and red. Mass uses the nominal
74.7 g/m in the manufacturer's [10 mm Doublebraid specification](https://shop.marlowropes.com/content/files/datasheets/2026/marlow-doublebraid-datasheet-0326.pdf).
This reference does not calibrate the simulated bending or friction.

The wooden tabletop is 110×130×6 cm, with its top at z=0.7475 m. Coordinates
use metres: x away from the robot, y to its left, z up. The U has two 30 cm
straight legs and a 70 cm semicircular section. End-joint centres start at
(0.060,+0.0428461,0.753) and (0.060,−0.4028461,0.753); the straight legs end
at x=0.360. The far bend reaches x=0.5828461. `config.py` supplies all 105 joint
centres at exactly 12.5 mm spacing. Both arms start in the YAM ready pose.
A render-only 28 cm tabletop ruler and 20 cm height guide have 5 mm ticks.
They provide review cues and have no collision geometry.

## Run and score

Activate the competition's YAM / Isaac Lab-Arena `yam.env`. The retained
installation is pinned in [ENVIRONMENT.json](ENVIRONMENT.json). From this
folder, choose a fresh output directory for each run. The current candidate
starts with `--physics-hz 240`, also the runner default. Its fixed schedule
switches to 960 Hz after 1,560 ordinary control actions (78 seconds), for
both the demo and Dream:

```bash
python run.py --policy loop --physics-hz 240 --max-steps 1000 --log-dir /tmp/rope-arch-001
python run.py --policy thread --physics-hz 240 --max-steps 2000 --log-dir /tmp/rope-feed-001
python run.py --policy demo --physics-hz 240 --max-steps 3000 --log-dir /tmp/rope-demo-001
python replay.py /tmp/rope-arch-001/trajectory.jsonl
python -m unittest discover -s . -p 'test_*.py'
```

`table_policy.py` lays a crossing, raises a local arch, and carries the red
terminal under it. The feeding hand releases the tip inside and withdraws;
the support hand lowers the arch, opens and lifts clear. The arms then pick
up both ends, lift and separate together while gradually closing the grippers,
turn outward, pull in the same control ticks, and release. Trial 020 demonstrates
this complete sequence from the uncrossed U.

`loop` stops after the arch; `thread` stops after red-tip regrasp; `demo`
attempts the whole sequence. The default seed is 0 and the starting layout is
fixed. The current sequence takes 137–140 simulated seconds, depending on how far
the final pull must extend, plus the final recording tick. The limit is 3,000
actions at 20 Hz (150 seconds). The successful demo stops when full score is
reached at 138.30 seconds; the simulator runner reports 29.3 wall-clock minutes.
A matching Dream run must use the same final source, seed, scene, cameras,
action limit and scorer. There are no evaluator actions after the episode.

Each run saves its exact source, configuration, package versions, actions,
measured cord and robot geometry, setup images and review video. The review
camera is not a policy input. `score-summary.json` records the result;
`replay.py` independently recomputes it and checks execution and finalization.
Scheduled runs also save `policy-physics-transition.json`: replay checks state
preservation, all native intervals, fresh cameras and cleanup through the last
sample, including samples after a geometry failure. A clean recording alone
does not mean that the robot completed the task. New version-2 certificates
also require final native counter/callback checks and a successful Inspect
execution record. Replay enforces both the task and trial action budgets.
Version-1 recordings remain readable, with any missing shutdown or execution
audit reported explicitly; their frozen source and results are preserved.

The optional factual time/phase overlay preserves all original frames:

```bash
python render_review.py /tmp/rope-arch-001 --output /tmp/rope-arch-001/review-labelled.mp4
```

## Judging

[JUDGING.md](JUDGING.md) defines the ruler-and-timer check. Half credit requires
one intact overhand to remain released for the final five seconds, with every
cord surface at least 3 cm from every robot part. Full credit also requires
the same knot to have met the suspended 117 cm end-span target for one second.
All other outcomes score zero. Either handedness is valid. A loop, crossing,
slipknot, tangle, broken cord or invalid physics earns no credit.

The span target limits whole-cord slack. It does not measure tension or prove
a maximally tight or strong knot. Its 14-diameter allowance is a declared task
target, not a material standard. Projected knot size and inferred tail lengths
are not scoring conditions. No particular grasp or arm sequence is required;
the implemented demonstration commands both arms to pull together.

## Simulation limits and evidence

The cord is 104 rigid capsules with native D6 joints, bending resistance,
free axial twist and nonadjacent self-contact. Only the reset restores poses.
Grasps and threading use normal robot contacts. The controller neither moves
cord bodies directly nor attaches them to a gripper. Its measured-geometry
feedback is privileged demonstration assistance, not a Dream input.

Friction is 0.8. Bending stiffness is 0.000390625 N m/rad and damping is
0.0000390625 N m s/rad. These are engineering assumptions, not measured
polyester parameters. Fibres, stretch, wear and plastic deformation are not
modelled. The solver uses 64 position and 16 velocity iterations, a 0.5 mm
contact offset and zero rest offset; allowed penetration is 5% of the diameter.

The fixed 240→960 Hz physics schedule applies equally to demo and Dream,
with 20 Hz control throughout. It adds no actions or external forces. Trial 020
validated unchanged state/counters, 48 native substeps per action across 1,206
post-switch intervals, and version-2 final callback/counter closure through
138.30 seconds. Historical trials
retain their recorded settings and scorer.

The scorer checks each recorded 20 Hz frame for rope continuity, nonlocal
penetration, topology, span and release. It cannot establish physical fidelity
between samples. Topological ambiguity earns no credit. Synthetic test cases
verify the scorer, not robot feasibility.

[The table-pilot evidence](evidence/table-pilots.json) preserves nineteen failed
pilots and the successful trial 020. Its suspended span qualifies from
130.75–131.75 seconds; released-knot retention runs from 133.30–138.30 seconds.
Both grasps remain held until intentional opening. All 2,767 recorded robot
poses pass the arm/table mesh audit, and twelve key frames were visually
reviewed. A separate audit of nonadjacent parts within each arm also finds no
intersections. The closest recorded rope-axis separation is 9.509743 mm against the
9.5 mm limit, a narrow margin. One fixed-seed success does not establish
repeatability. The full 142-test CPU suite also passes.

[VALIDATION.json](VALIDATION.json) separates current evidence from the five
older high-lift pilots and historical v3 jig trials. The old jig demo's native
velocity spike remains unresolved. Submission still needs the matching Dream
result, independent replay and review of that run, and final submission checks. Raw trials
remain outside Git. No media upload or upstream PR has been made for this task.

## Review lessons

Accepted tasks [#8](https://github.com/robocurve/benchmark-tasks/pull/8),
[#10](https://github.com/robocurve/benchmark-tasks/pull/10) and
[#42](https://github.com/robocurve/benchmark-tasks/pull/42) informed the visible
judging, partial credit and disclosed approximations. Their acceptance does
not establish this task's feasibility, novelty or acceptance.
