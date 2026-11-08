# Tie an overhand knot using a jig

**Development task. There is no validated knot demo, Dream run or submission yet.**

Finish the overhand knot in the blue cord, remove it from the pegs and let go.
The knot is then tested with a gentle pull. The jig holds an untied loop for a
repeatable cord-finishing step used in drawstrings and bag handles. Forming the
initial loop and assembling or strength-testing a finished product are outside
this task.

## Setup

The YAM station holds one blue, round cord: 118 cm between end-joint centres,
8 mm diameter and 46.09375 g. Rounded caps extend 4 mm beyond each end. The
outside length is 118.8 cm including the terminal caps. The first and last
1 cm links are yellow and red. The intended physical object is
braided polyester cord; its material response is not calibrated.

The cord starts with one untied crossing arranged on three rounded pegs.
Nothing attaches it to the pegs or robot. `jig_layout.py` gives every initial
joint centre and fixture dimension. Coordinates use metres, with x away from
the robot, y to its left and z up. The wooden tabletop is 110×130×6 cm, with its top at z=0.7475 m.
The red end starts at (0.430,−0.25206,0.752); its straight working tail
runs along x=0.430 m. The crossing lies below the keeper peg.

The grey, steel-like pegs are 16 mm in diameter, with 140 mm straight sections
along y=−0.060 to +0.080 m and hemispherical ends. Their (x,z) centres are
(0.225,0.920), (0.375,0.920), and (0.300,0.780) m. Static posts are centred at
y=+0.096 m. The two tall posts are 22×16×192.5 mm; the short post is
22×16×32.5 mm. Their bottoms meet the table.

A fixed clamp holds the first 10 mm cord link, centred at
(0.105,−0.122,0.752). Its visible top jaw is 30×40×8 mm; two side jaws are
30×6×10 mm, offset by ±17 mm in y from the clamped link. The top jaw
is centred at (0.105,−0.122,0.7615); side-jaw centres are z=0.7525 m.
The posts and clamp are intended as rigid metal parts, shown in grey. An ideal
fixed joint approximates
a firmly tightened bench clamp. The arms start in the station's ready pose.

The current fixture is `far-supports-v3`. The earlier near-side upright caught
the working strand; each recording saves its exact fixture geometry so older
trials can still be replayed correctly.

## Run

Use the competition's YAM / Isaac Lab-Arena installation and activate its
`yam.env`. [ENVIRONMENT.json](ENVIRONMENT.json) records the exact package and
repository versions, plus the public asset-root correction used for these
trials. Seed 0 is the default. Run from this directory with a fresh output path:

```bash
python run.py --policy idle --development-jig three-peg --max-steps 110 --log-dir /tmp/rope-jig-idle-001
python run.py --policy jig --development-jig three-peg --max-steps 2400 --log-dir /tmp/rope-jig-trial-001
```

These are development probes. `--policy demo` refuses to run until there is a
validated full sequence. The intended limit is 2,400 actions: two minutes at
20 Hz. Runtime must be measured on the final task. Each run saves full rope
geometry, segment poses and velocities, joint gaps, measured grippers, actions,
source snapshots, versions and an additional review-camera video.

The current contact-resolution trial uses 480 Hz physics, 128 position and
16 velocity solver iterations, 1 mm capsule contact offsets and zero rest
offset. Earlier 240 Hz / 64-iteration trials completed robot knotting but
failed during load seating. A 960 Hz comparison on a different unassisted
pinching failure did not fix that problem. These are separate observations.

Replay uses the saved dimensions and measured geometry, ignoring recorded
score claims:

```bash
python replay.py /tmp/rope-jig-trial-001/trajectory.jsonl
python -m unittest discover -s . -p 'test_*.py'
```

`score-summary.json` is the final audit result. Inspect's episode result covers
the robot actions only: a qualifying knot is load-tested after that episode.
The complete review video and trajectory include those assessor steps.

## Judging

The [draft protocol](JUDGING.md) gives 0.5 for a released overhand knot, with
the entire cord at least 1 cm from every peg and support and 3 cm from every
robot part. The declared standing-end clamp remains attached. Full credit requires the knot to survive
a 2-second seating ramp and 5 seconds under a 0.981 N free-end pull.

A loop, ordinary crossing, tangle or damaged cord does not qualify. The
evaluator cannot create or repair a knot. A knot that comes undone during the
pull retains its pre-test 0.5; invalid physics scores zero.

`topology.py` checks crossing order using several views and exterior closures.
Ambiguity earns no credit. Projected core size, tail lengths and apparent slip
are diagnostics only: they vary with viewpoint and do not replace a ruler.
The load record establishes applied external force, not internal knot tension.

## Simulation limits

The jig uses 118 rigid capsules joined with bending resistance, free twist and
contact between nonadjacent links. Robot grasps use ordinary finger contact.
The controller never writes rope poses, attaches it to a hand or changes
collision rules during a trial. Only reset restores the initial layout.

This approximates an inextensible cord. It does not model braided fibres,
stretch, plasticity, wear or a certified load rating. Friction and damping are
explicit engineering assumptions. Stable knotting, retention and repeatability
must be demonstrated before this task is submission-ready.

A separate diagnostic starts with a preformed knot. It always scores zero as a
task, even when it survives the pull. It tests physics, not robot feasibility.

## Earlier unassisted probes

Without `--development-jig three-peg`, the runner uses a 96 cm / 37.5 g cord in
an untied U: two 34 cm straight legs and a 28 cm semicircular section. The yellow
end starts at (−0.02,0), and the red end at (−0.02,−0.17835). This setup is
retained for `idle`, `grasp`, `loop` and `thread` diagnostics; it is not the jig
task described in `task.draft.json`. `config.py` gives its exact nodes.

## Review lessons

Accepted tasks [#8](https://github.com/robocurve/benchmark-tasks/pull/8) and
[#10](https://github.com/robocurve/benchmark-tasks/pull/10) demonstrate useful
cable objectives with visible judging and disclosed segmented-cable
approximations. [#42](https://github.com/robocurve/benchmark-tasks/pull/42) uses
physical milestones and meaningful partial credit. This task follows those
principles, but their acceptance does not establish this task's feasibility,
novelty or acceptance. It does not test whether a knot stops an eyelet.
