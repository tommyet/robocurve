# Tie an overhand knot

**Revision in development; not ready for submission.** The previous jig demo
and its evaluator pull do not validate this version. New robot trials are
required.

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
use metres: x away from the robot, y to its left, z up. The U has two 45 cm
straight legs and a 40 cm semicircular section. End-joint centres start at
(0.060,+0.1273751,0.753) and (0.060,−0.1273751,0.753); the straight legs end
at x=0.510. The far bend reaches x=0.6373751. `config.py` supplies all 105 joint
centres at exactly 12.5 mm spacing. Both arms start in the YAM ready pose.

## Run and score

Activate the competition's YAM / Isaac Lab-Arena `yam.env`. The retained
installation is pinned in [ENVIRONMENT.json](ENVIRONMENT.json). From this
folder, choose a fresh output directory for each run:

```bash
python run.py --policy loop --max-steps 700 --log-dir /tmp/rope-arch-001
python replay.py /tmp/rope-arch-001/trajectory.jsonl
python -m unittest discover -s . -p 'test_*.py'
```

`loop` is the available pickup/crossing/arch feasibility probe. The threading
and full-demo stages are explicitly blocked before simulator startup until
their paths are validated. A new demo and Dream recording are still missing.
Once implemented, both will use the same free cord, cameras, action limits
and scorer. The limit
is 2,400 actions at 20 Hz, including release and the final five seconds.
There are no additional evaluator actions after the robot episode.

Each run saves the exact source, configuration, package versions, executed
actions, measured rope poses and velocities, joint gaps, robot collision
geometry, setup images and a separate review-camera video. The review camera
is not a policy input. `score-summary.json` is authoritative; `replay.py`
recomputes the geometric result and checks clean finalization. Legacy v3
recordings continue to use their old scorer and recorded configuration.

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
the demonstration uses both arms to pull.

## Simulation limits and evidence

The cord is 104 rigid capsules with native D6 joints, bending resistance,
free axial twist and nonadjacent self-contact. Only the reset restores poses.
Grasps and threading use normal robot contacts; the controller neither moves
cord bodies directly nor attaches them to a gripper. Its measured-geometry
feedback is privileged demonstration assistance, not a Dream input.

Friction is 0.8. Bending stiffness is 0.000390625 N m/rad and damping is
0.0000390625 N m s/rad. These are engineering assumptions, not measured
polyester parameters. The current candidate uses 240 Hz physics, 64 position
and 16 velocity iterations, 0.5 mm contact offset and zero rest offset.
Fibres, stretch, wear and plastic deformation are not modelled.

The scorer checks each recorded 20 Hz frame for rope continuity, nonlocal
penetration, topology, span and release. It cannot establish physical fidelity
between samples. Topological ambiguity earns no credit. Synthetic test cases
verify the scorer, not robot feasibility.

`VALIDATION.json` retains explicitly labelled historical v3 evidence; none
establishes this revision's success. The previous jig demo also had an
unresolved native-velocity spike during handover. The new controller avoids
that handover, but requires fresh physics and visual review before any
success claim. Raw trials remain outside Git. No media has been uploaded and
no upstream pull request has been opened for this task.

## Review lessons

Accepted tasks [#8](https://github.com/robocurve/benchmark-tasks/pull/8),
[#10](https://github.com/robocurve/benchmark-tasks/pull/10) and
[#42](https://github.com/robocurve/benchmark-tasks/pull/42) informed the visible
judging, partial credit and disclosed approximations. Their acceptance does
not establish this task's feasibility, novelty or acceptance.
