# Weave a lattice top on a pie

Development prototype, not submission-ready. The complete 3,000-control Dream
baseline scores 0.0, but no full-score scripted demonstration has succeeded.
Do not submit this folder in its current state.

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
all trials. Temper the sealed refrigerated dough for 15 minutes at room temperature, as
[Pillsbury directs](https://www.pillsbury.com/products/pie-crust/refrigerated-pie-crust), then unroll on baking
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
Use an overhead and oblique photograph and a ruler. Ends may overhang the crust;
trimming and exact row angles are not scored. A tear separating any strip,
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
searches do not guarantee novelty across every external benchmark. Related
[pending task #2296](https://github.com/robocurve/benchmark-tasks/pull/2296)
braids three hair sections anchored at a head. This task weaves five loose
strips into an orthogonal lattice on a pie; it requires under-passage and
replacement without a shared anchored end. The broader skill of interlacing
is not claimed to be new to robotics. The pie, board, pastry and finger extensions are generated in this folder.
The robot assets are listed below.

## Run and verify

Use the pinned Python 3.12 / Isaac Sim 6.1 / YAM environment in `ENVIRONMENT.json`.

```sh
python tasks/weave-a-pie-lattice/make_plan.py
OMNI_KIT_ACCEPT_EULA=YES ACCEPT_EULA=Y python tasks/weave-a-pie-lattice/run.py --mode demo --out /tmp/lattice-demo
OMNI_KIT_ACCEPT_EULA=YES ACCEPT_EULA=Y python tasks/weave-a-pie-lattice/run.py --mode dream --out /tmp/lattice-dream
python tasks/weave-a-pie-lattice/rescore_current.py /tmp/lattice-demo
python tasks/weave-a-pie-lattice/rescore_current.py /tmp/lattice-dream
```

Limit: 3,000 actions / 150 seconds at 20 Hz. Fixed layout, no reset jitter or
random seed. The deterministic IK authoring search uses seeds 17, 31 and 43.
Runtime saves every native frame, continuous body/action traces and frozen
source. CPU rescoring checks source hashes, action bounds, release and the
outcome; it is not a substitute for native simulation. Native wall times and
full video inspection must be recorded before submission.

### Tail-alignment scoring correction

The Dream baseline and earlier diagnostics use the original scorer; the final
demo candidate uses the corrected scorer. The original extra lateral bound on
loose tails rejected a valid diagonal row, although its six crossings, rim reach
and supported portions were correct. `rescore_current.py` verifies the frozen
source and original audit, proves that removing this single condition is the
only model-code change, then scores the complete trace. Both original and
corrected scores are retained. Physics, policy, damage and release checks are
unchanged. Tail overhang is allowed because trimming is outside the task.

## Asset attribution

Task props and finger extensions are procedural boxes, cylinders and rings
from `geometry.py` and `pad_covers.py`, under this folder's MIT licence.
No downloaded food, kitchen or fabric model is used.

The external pinned YAM runtime supplies the following I2RT robot assets,
under its [MIT asset licence](https://github.com/kairosiann/yam-isaac-lab-arena/blob/0059d02a1a91bc6834c1d0846022891df0c78730/yam_arena/assets/yam/LICENSE.i2rt):

- `assets/base.stl`, `gripper.stl`, `link1.stl` through `link5.stl`,
  `tip_left.stl` and `tip_right.stl`, plus their convex decomposition files
  in the corresponding `collision/<link>/` directories.
- Dream-style split visuals `dream/link2_black.stl`, `link2_white.stl`,
  `link3_black.stl` and `link3_white.stl`. The pinned runtime's
  [station module](https://github.com/kairosiann/yam-isaac-lab-arena/blob/0059d02a1a91bc6834c1d0846022891df0c78730/yam_arena/station.py)
  attributes these parts to Dream's station and identifies the same MIT terms.

The robot USD is converted from those assets. The table, floor, camera bodies
and mast are primitive geometry in the external runtime. Robot meshes and
runtime source are not redistributed in this task folder. `inspect-robots-yam`
0.38.0 separately carries an MIT package licence and its MIT I2RT
`assets/MENAGERIE_LICENSE`; all runtime versions are pinned in `ENVIRONMENT.json`.

## Validation status — 22 November 2026

The full native Dream baseline completed 3,000 controls and independently
rescores 0.0. Its trace, measured contacts and complete native videos are
archived. Twelve diagnostic demonstrations have not produced a full weave.
Demo011 retained the support grip but missed the second cross-strip pickup
at control1,140. Lower demo-only tracking gains did not fix that pickup.

Demo012 completes and releases each row before starting the next. Its plan
fits in2,920controls with maximum joint-speed ratio0.845. The first cross-strip
spans the pie intact, but replacing the lifted lengthwise strip leaves it
folded back on itself rather than spanning the crust. Both the native scorer
and the inspected camera frame correctly show no completed woven row. The
operator stopped at control1,016 because this sequence could not finish
successfully. No score condition or material property was weakened.

The unresolved action is unfolding and laying the lengthwise strip flat while
preserving the crossing. The model/policy and physical setup remain unchanged;
the current controller changes affect only the scripted demo. No full-score
demo, physical dough calibration or physical preparation trial is claimed.
All run archives are backed up and the rented GPU was deleted, confirmed404.
Do not submit until a genuine full-score demonstration passes.
