# Tie an overhand stopper knot

**Development task. There is no validated knot demo, Dream run or submission yet.**

Tie one overhand knot in a cord, leave at least 4 cm at each end and let go.
Stable end knots are a basic step in finishing drawcords. This task checks the
knot and whether it stays tied under a gentle pull; it does not test an eyelet.

## Setup

The YAM station holds one blue, round cord: 96 cm between end-joint centres,
8 mm diameter and 37.5 g. The rounded caps extend 4 mm beyond each end. Yellow
and red end markings make the two ends easy to follow. The intended physical
object is braided polyester cord; its material response is not yet calibrated.

The cord starts untied in a U on the table. Coordinates use metres, with x away
from the robot, y to its left and z up. The yellow end starts at (−0.02, 0), and the red end at
(−0.02, −0.17835). The two straight legs are each 34 cm long; a semicircle
with 28 cm of centreline joins them at the far end. `config.py` specifies every initial joint centre.
A fixed clamp holds the first 10 mm link at the yellow end. Its visible top
jaw is 30 × 40 × 8 mm, centred at (−0.015, 0, 0.7615); two 30 × 6 × 10 mm
side jaws sit at y=±0.017 m. The jaws are rigid grey blocks. The ideal fixed
joint is an explicit approximation to a firmly tightened bench clamp.
The arms start in the station's ready pose. There is no pre-existing crossing,
knot or attachment to either gripper.

## Run

Use the competition's updated YAM / Isaac Lab-Arena installation and activate
its `yam.env`. Run from this directory, choosing a fresh output directory:

```bash
python run.py --policy idle --max-steps 110 --log-dir /tmp/rope-idle-001
python run.py --policy grasp --max-steps 450 --log-dir /tmp/rope-grasp-001
python run.py --policy loop --max-steps 750 --log-dir /tmp/rope-loop-001
python run.py --policy thread --max-steps 1600 --log-dir /tmp/rope-thread-001
python run.py --policy idle --development-jig three-peg --max-steps 110 --log-dir /tmp/rope-jig-idle-001
```

These are development probes, not successful task demonstrations. The completed
task will use a 2,400-action limit: two minutes at 20 Hz. Runtime must be measured
on the final task. Each run saves complete rope geometry, individual segment
poses and velocities, joint gaps, measured grippers, actions, source snapshots,
versions and an additional review-camera video.

The default physics rate is 240 Hz. A 960 Hz comparison did not resolve the
unassisted threading probe's contact failures and was substantially slower.

Replay uses the saved dimensions and measured geometry, ignoring recorded
score claims:

```bash
python replay.py /tmp/rope-jig-idle-001/trajectory.jsonl
python -m unittest discover -s . -p 'test_*.py'
```

`score-summary.json` is the final audit result. Inspect's episode result covers
the robot actions only: a qualifying knot is load-tested after that episode.
The complete review video and trajectory include those assessor steps.

## Intended judging

The [draft judging protocol](JUDGING.md) gives 0.5 for a released overhand knot
with both tails at least 4 cm, and 1.0 if it survives a 2-second seating ramp
and 5 seconds at 0.981 N. A loop, ordinary crossing, tangle or damaged cord does
not qualify. The evaluator cannot create or repair a knot. A knot that comes
undone during the pull retains its pre-test 0.5; invalid physics scores zero.

`topology.py` checks actual crossing order using several views and exterior
closures. It reports ambiguity rather than treating every tangle as a knot.
Its crossing envelope is a conservative geometric diagnostic, not a substitute
for visible judging or a material-strength measurement.

## Development jig

The optional jig holds a single-crossed, untied loop on three rounded pegs.
It uses a 118 cm / 46.09375 g cord of the same diameter and linear density.
The current 16 mm-diameter pegs have 140 mm straight sections along y=−0.060 to +0.080 m,
at (x,z)=(0.225,0.920), (0.375,0.920), and (0.300,0.780) m. Their static posts
are fixed to the table at y=+0.096 m, behind the loop from the approaching
right hand. The first version's near-side upright caught the working tail.
`jig_layout.py` gives their dimensions and all rope
nodes. The standing clamp moves to the first link, centred at (0.105,−0.122,0.752).

No rope is attached to a peg. Before credit, the entire cord must be at least
1 cm clear of every peg and support, as well as 3 cm clear of the robot.
The first 5-second idle check remained untied without invalid rope contact.
A successful robot sequence is still required.

## Simulation limits

`rope.py` uses 96 rigid capsules and physical joints with bending resistance,
free twist and contact between nonadjacent links. Robot grasps use ordinary
finger contact. The controller never writes rope poses, attaches it to a hand
or changes collision rules during a trial. Only reset restores its layout.

This approximates an inextensible cord. It does not model braided fibres,
stretch, plasticity, wear or a certified load rating. Friction and damping are
explicit engineering assumptions. Stable knotting, retention and repeatability
must be demonstrated before this task is submission-ready.

## Design references

Accepted tasks [#8](https://github.com/robocurve/benchmark-tasks/pull/8) and
[#10](https://github.com/robocurve/benchmark-tasks/pull/10) demonstrate useful
cable objectives with physical milestones, visible judging and disclosed
segmented-cable approximations. They support the integration approach; their
acceptance does not establish that this knot task is feasible or novel.
