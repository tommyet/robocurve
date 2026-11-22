# Weave a lattice top on a pie

Development prototype. No native full-score demonstration or model baseline is
claimed yet; do not submit this folder in its current state.

Weave three loose pastry strips across two strips already laid on a small pie.
Every crossing must alternate over and under. Leave all five strips intact,
spanning the crust, and release them. Cutting, filling, trimming and baking are
outside this task.

The two lengthwise strips start flat, with no crossings made and no ends fixed.
The work is lifting soft pastry, feeding a cross-strip underneath it, and
replacing it without undoing earlier crossings. Merely laying three strips on
top does not earn credit.

## Physical setup and reset

Use an ordinary 180 mm inside-diameter, 190 mm rim-diameter, 36 mm deep aluminium
pie/tart pan, a bottom pastry shell and a level layer of commercially canned
apple pie filling. The pan is loose on the worktop. Fill to 1–2 mm below its rim;
the whole prepared pie weighs approximately 550 g. Filling preparation is not
being tested. The simulator treats the pan, bottom shell and filling as one
rigid body; there is no claim to simulate filling damage or baking.

Use Pillsbury refrigerated pie-crust dough, from the same product and batch for
all trials. Temper sealed dough as its package directs, unroll on baking
parchment, roll between 2 mm thickness guides, and cut five 200 × 25 mm strips
with a ruler and pastry wheel. Keep prepared strips covered in a refrigerator
at 2–4 °C. Take one set out five minutes before the trial, at a room temperature
of 20–22 °C. Do not flour, glue or pre-crease the strips. Reject visibly cracked,
stuck or dry strips. Record the product, batch, temperature and preparation
intervals. Prepare several sets together; use fresh strips and a fresh top
surface for each attempt. This preparation protocol has not been physically
validated.

Lay two strips north–south on the pie, their centre lines 64 mm apart. Lay the
other three east–west, 50 mm apart, on a 180 × 180 × 42 mm chopping board to the
left, with 10 mm of natural strip overhang at each end for pickup. The board is level with the pie surface. None is attached, pre-threaded
or already overlapping another strip. The fixed layout is in `geometry.py`;
metres are relative to the robot station, with worktop height 747.5 mm. The pie
centre is (350, 25) mm and the board centre is (130, 25) mm in plan view.

Use removable, smooth stainless finger extensions with 40 × 6 × 1 mm working
leaves and 100 × 8 × 1 mm stems as specified in `pad_covers.py`. Round and deburr
the edges. The extensions are washable food-contact surfaces; cover the
underlying grippers/wrists with disposable food-safe sleeves and put a washable
catch mat beneath the work. Remove and wash the extensions and replace the
sleeves between trials. Do not eat evaluation food. Sleeves and catch mat are
physical-rig protection, not rendered task objects; they must not bridge the
jaws or obstruct the pastry. No real rig or material test is claimed here.

Before physical trials, manually check that a prepared strip can be lifted and
laid without sticking or cracking, and that the extensions can grip it without
cutting it. Record any rejected preparation. Do not quietly change the dough,
add supports or stiffen the strips to make the task work.

## Scoring

Judge after both grippers are open and at least 50 mm clear for three seconds.
Use an overhead and oblique photograph and a ruler. A tear separating any strip,
a strip lost off the work area, or a tipped pie earns zero. Each cross-strip
must reach the crust on both sides, lie on the pie rather than hang from a hand,
and pass above one lengthwise strip and below the other. The next row reverses
that order. Either checkerboard phase is equally valid.

Award one third for each complete correctly woven row in the better of those
two checkerboard phases. A row with both crossings on top or both underneath
gets zero. No starting-placement credit is awarded. Full score needs all three
rows, all five strips intact and spanning the crust, with the lattice resting
on the pie. Finishing with the opposite over/under phase or handling the loose
strips in a different order makes no difference.

The scorer uses native strip poses and the loose pan's frame. It sorts strips
by their final positions, checks each row's two crossing orders and rim reach,
and checks release and integrity. Submillimetre tolerances in that geometric
implementation are numerical guards for the disclosed 2 mm material model,
not measurements a real judge must take. The visible criterion is which intact
strip is above the other at each crossing.

## Approximation

Each strip is 24 contact-bearing rigid sectors joined by passive bend/twist
joints. Gravity, contact, friction and finite native grips move them. The joints
can break; there is no scripted fold, snap-to-weave, target trajectory for dough,
or body-position write after reset. The model omits pastry stretch, plastic
flow, tackiness and temperature dependence. Its stiffness, 2 N tear limit and
0.8 N grip limit are nominal, uncalibrated approximations. They are not measured
properties of the named dough. The important retained constraints are bending,
support, collision, possible tearing and genuine over/under passage.

`make_plan.py` authors joint commands offline; `demo_control.py` corrects for
observed poses but can only command the same robot joints as Dream. Both
policies use the same scene, cameras, finger hardware, force limits and scorer.

## Sources and novelty

The method follows [King Arthur's lattice technique](https://www.kingarthurbaking.com/blog/2021/07/01/how-to-make-a-lattice-pie-crust):
lift alternating strips, add a cross-strip, replace them and alternate the next
row. [Pillsbury](https://www.pillsbury.com/everyday-eats/desserts/pies-tarts/how-to-make-pie)
documents using its refrigerated crust for lattice tops.

A public all-state search of 3,572 Robocurve PRs on 22 November found no direct
pastry-lattice submission. BEHAVIOR's
[`make_pastry`](https://behavior.stanford.edu/knowledgebase/tasks/make_pastry-0.html)
combines ingredients in a food processor; it does not weave strips. These
searches do not guarantee novelty across every external benchmark. All meshes
are generated in this folder; no third-party geometry is used.

## Run and verify

Use the pinned Python 3.12 / Isaac Sim 6.1 / YAM environment in `ENVIRONMENT.json`.

```sh
python tasks/weave-a-pie-lattice/make_plan.py
OMNI_KIT_ACCEPT_EULA=YES ACCEPT_EULA=Y python tasks/weave-a-pie-lattice/run.py --mode demo --out /tmp/lattice-demo
OMNI_KIT_ACCEPT_EULA=YES ACCEPT_EULA=Y python tasks/weave-a-pie-lattice/run.py --mode dream --out /tmp/lattice-dream
python tasks/weave-a-pie-lattice/rescore.py /tmp/lattice-demo
python tasks/weave-a-pie-lattice/rescore.py /tmp/lattice-dream
```

Limit: 3,000 actions / 150 seconds at 20 Hz. Fixed layout, no reset jitter or
random seed. The deterministic IK authoring search uses seeds 17, 31 and 43.
Runtime saves every native frame, continuous body/action traces and frozen
source. CPU rescoring checks source hashes, action bounds, release and the
outcome; it is not a substitute for native simulation. Native wall times and
full video inspection must be recorded before submission.
