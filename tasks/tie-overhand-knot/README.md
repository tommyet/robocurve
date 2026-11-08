# Tie an overhand knot

**Implemented, but not yet validated or ready for submission.** The complete
table method is in code. Sixteen table pilots have scored zero. Trial 016
passed the measured support-placement guard and fixed physics checks, then
stopped on invalid rope contact during support-hand withdrawal. Trial 017
will lift the open support hand vertically before parking. Recovery, pulling
and final retention remain unproven.

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

`table_policy.py` implements the sequence. The right hand grips segment 101
and lays one crossing from the uncrossed U. It then grips standing segment 23
and raises a local arch by 15 cm. The left hand grasps the actual red terminal,
segment 103, and carries it under the arch. It releases the red tip inside
the loop and withdraws empty. The right hand lowers the arch toward the table,
releases it, lifts the open hand 3 cm before parking, then picks up the red
terminal from above. The left approaches yellow segment 2 from the
north with a 24 mm jaw opening and descends to grasp it. With both ends held,
the right lifts the red terminal 6.5 cm, moves outward to clear the other arm,
then moves south. Both arms stage the pull, move outward in the same control
ticks and release the cord. The full sequence remains unvalidated.

`loop` stops after the arch; `thread` stops after right-hand red-tip regrasp;
`demo` attempts the whole sequence. Available commands do not establish
feasibility. [Sixteen table pilots](evidence/table-pilots.json) all scored zero.
Trials 004/005 stopped on invalid rope contact; 006 formed the right-arm arch.
In 007 the terminal entered the loop, but the palm still supported the raised
strand. Diagonal staging returned the topology to unknot, and a pickup-region
guard stopped the run before pulling. Trial 008 produced an independently
certified geometric overhand candidate during the deeper feed and retained it
through the lift. The cord remained held, with no span or release attempt, so
it still scored zero. In 009, the crossing migrated to the free yellow end
and disappeared during staging. A pickup-region guard stopped the run before
pulling. Trial 010 formed a candidate during red-tip release, but the tip
recoiled into the far loop strand and violated the contact tolerance at
68.15 seconds. Trial 011 used 480 Hz and failed on contact between the two
ends during arch lifting, before reaching the new motions. Trial 012 returns
to 240 Hz and kept the released terminal inside, with a 3.61 mm surface gap
to the nearest strand. Its 15 mm planning margin stopped the run. Trial 013
passed the 12 mm whole-axis guard and empty-hand withdrawal, then stopped
on invalid contact after releasing the raised arch. It never reached the
planned regrasp or pull. Trial 014 added a controlled 14 cm lowering, but the
cord remained 12.66 mm above the table when opening began. It also failed
during withdrawal, after the right hand was clear of the rope. The cause is
not yet established. Trial 015 validated the 78-second physics switch through
60 subsequent control intervals, but stopped on a policy exception at
81 seconds. Its clean recording and zero CLI exit did not mean the policy
succeeded. Trial 016 passed the measured support-placement guard and all
154 post-switch native intervals, but capsule pair 28/90 crossed the unchanged
contact threshold at 85.65 seconds. The controlled stop and recording
finalized cleanly; no recovery or pull was reached. Trial 017 adds a 3 cm
vertical withdrawal before fully opening and parking the support hand. Its
result is pending. The full 132-test CPU suite passes; 17 focused checks also
pass after the withdrawal change. They check scoring, recording and guards, not
whether the robot can complete this task. A check of all 1,342 recorded native robot
poses from trial 012 found no inter-arm or tabletop intersections; minimum
separation bounds were 23.93 mm between arms and 0.72 mm above the table. This
does not certify the later, unreached recovery and pull.

[Five earlier high-lift pilots](evidence/bimanual-pilots.json), also score zero,
use the previous layout and controller. They are separate historical evidence.
The table pilots took about 3.6–11.0 wall-clock minutes each in the recorded
environment; full-task runtime is not yet measured. The current sequence totals
143 simulated seconds before the final recording tick. The prospective limit
is now 3,000 actions at 20 Hz (150 seconds), allowing time for careful clearance
and regrasping, including release and the final five seconds. Recorded trials
retain their original limits; trial 008 uses its frozen 2,400-action scene and
1,800-action thread probe. A matching Dream trial must use the same final scene, cameras, action limits and scorer.
There are no evaluator actions after the robot episode.

Each run saves the exact source, configuration, package versions, executed
actions, measured rope poses and velocities, joint gaps, robot collision
geometry, setup images and a separate review-camera video. The review camera
is not a policy input. `score-summary.json` is authoritative; `replay.py`
recomputes the geometric result and checks clean finalization. Scheduled runs
also save `policy-physics-transition.json`. Replay requires unchanged state
at the switch, every native physics interval, fresh camera frames and clean
cleanup through the last recorded sample, even if geometry became invalid.
Legacy v3
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
the implemented demonstration commands both arms to pull together.

## Simulation limits and evidence

The cord is 104 rigid capsules with native D6 joints, bending resistance,
free axial twist and nonadjacent self-contact. Only the reset restores poses.
Grasps and threading use normal robot contacts. The controller neither moves
cord bodies directly nor attaches them to a gripper. Its measured-geometry
feedback is privileged demonstration assistance, not a Dream input.

Friction is 0.8. Bending stiffness is 0.000390625 N m/rad and damping is
0.0000390625 N m s/rad. These are engineering assumptions, not measured
polyester parameters. The current candidate uses 240 Hz physics through
78 seconds and 960 Hz afterward, with 20 Hz robot control throughout. The
switch is fixed in time and applies equally to demo and Dream; it neither
adds robot actions nor applies external forces. Trial 016 validated unchanged
state, counters and 48 native substeps per action for 154 actions after the
switch. That validates the transition through 85.70 seconds, not task completion. Solver settings remain 64 position and 16 velocity
iterations, 0.5 mm contact offset and zero rest offset. Earlier trials keep
their recorded rates: 011 used 480 Hz; trials 001–014 otherwise used 240 Hz. The 5% diameter
penetration tolerance is unchanged.
Fibres, stretch, wear and plastic deformation are not modelled.

The scorer checks each recorded 20 Hz frame for rope continuity, nonlocal
penetration, topology, span and release. It cannot establish physical fidelity
between samples. Topological ambiguity earns no credit. Synthetic test cases
verify the scorer, not robot feasibility.

[VALIDATION.json](VALIDATION.json) separates current table pilots, older
high-lift pilots and historical v3 jig evidence. The old jig demo had an
unresolved native-velocity spike during handover. Current success requires a
fresh complete trial, independent replay and visual review. Raw trials remain
outside Git. No media has been uploaded and no upstream pull request has been
opened for this task.

## Review lessons

Accepted tasks [#8](https://github.com/robocurve/benchmark-tasks/pull/8),
[#10](https://github.com/robocurve/benchmark-tasks/pull/10) and
[#42](https://github.com/robocurve/benchmark-tasks/pull/42) informed the visible
judging, partial credit and disclosed approximations. Their acceptance does
not establish this task's feasibility, novelty or acceptance.
