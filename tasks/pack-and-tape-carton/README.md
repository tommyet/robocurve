# Pack a carton and seal it using an ordinary tape roll

Engineering draft. Twenty local material/contact/scorer checks pass. **There
is no functioning native peel/adhesion runtime, robot demonstration, model
score or video.** The finite tape ledger is accounting, not a tape simulator.

Pack two objects into an open carton, fold its four top flaps in the correct
order, find and peel the end of an ordinary roll of packing tape, pull out a
strip, press it across the seam and down both end faces, cut it with the
guarded cutter and park the roll/tool. Leave a sealed carton after releasing
both hands. No pre-laid strips or tool-path-triggered deposition.

## Ordinary tape form factor

Provisional design is a **loose roll**, 48 mm wide, 50 µm film-plus-adhesive,
100 mm outside diameter and 76.2 mm cardboard core diameter. The core is open,
so a robot can potentially grasp its rim rather than needing an invented
handle. Starting end is flush on the outer wrap: **no prepared pull tab or
protruding leader**. Extracting that edge with the YAM fingertips is a major
unproven physical challenge, not a step we assume succeeds automatically.

`model.py` tracks finite natural-length payout, shrinking roll radius and
verified blade severing. The dimensions imply about 65.9 m of tape; the
native implementation need only represent the active wound layer/ribbon
while conserving that supply. A 220 mm seam and two 40 mm wraps need at least
300 mm of connected material. Maximum permitted strain is 5%.

`adhesion.py` is a candidate local contact/cohesion law: only the adhesive
face can bond, within 0.5 mm of a surface under at least 0.5 N compression for
100 ms. Each 5 × 48 mm material cell has a provisional 2,000 N/m cohesive
spring and 2 N break load; these are **uncalibrated design values**. An adapter
must apply equal/opposite forces at physics substeps, preserve material
identity, model contact/slip and peel, and derive adhesion from actual ribbon
contact. It must not hold flaps shut by changing their poses or snapping
closed merely because a roller/finger passed over the seam.

The requested realism is therefore a required mechanics development step,
not a claim that this first draft already achieves it. If the fingertips
cannot peel a flush tape edge, we must report that and choose a justified
ordinary tool with the user rather than secretly adding a convenient tab.

## Carton and contents

Provisional carton: 220 × 180 × 100 mm, 3 mm corrugated board, ordinary four
top flaps; bottom factory-sealed. Objects are two rigid products, 80 × 50 ×
30 mm and 60 × 40 × 30 mm, initially outside the box. Native masses, materials,
starting positions, flap interactions and safe guarded cutter integration
remain to be frozen after reach/contact checks. No artificial handles.

## Proposed end-state scoring

- 0.25: both products wholly inside, at least 3 mm clear of walls and below
  the top flaps, product speeds below 20 mm/s. Full bounding boxes are checked.
- 0.50: above, all four top flaps closed within 5 degrees, short flaps beneath
  long flaps.
- 0.75: above, one severed connected tape strip bonds at least 80% of its
  width across **every** 5 mm seam cell, with at least 35 mm bonded on both
  40 mm end wraps. It is detached from the roll.
- 1.00: above, both hands clear, roll/cutter parked, carton speed below
  10 mm/s, held for two seconds after release. Native flap restoring forces
  remain active; adhesive forces must hold the seal without the robot.

Invalid material accounting, over 5% strain, carton joints separated by over
4 mm, dropped objects, nonfinite state or missing samples invalidates the
trial. Restoring forces and measured bond forces must be recorded for the
release hold. No external opening-test fixture is part of the task. Cosmetic
tape patches and tool paths do not establish a bond.

Proposed allowance is 4,800 controls (four minutes at 20 Hz), subject to a real
full-score demonstration. This task is harder than the tape-gun-only #1893 in
both product/flap preparation and actual tape sourcing/adhesion; this does not
guarantee novelty acceptance. Recheck the board before eventual submission.

```sh
python3 -m unittest discover -s tasks/pack-and-tape-carton -p 'test_*.py' -v
```

Next: hollow-roll/native ribbon representation, flush-edge peel probe with real
gripper geometry, winding/payout mechanics, force-coupled adhesion/peel,
scissor/cutter interaction, native packed-carton flap scene, then a robot
controller and complete validation. There is currently no `run.py`; do not
describe synthetic scoring states as a physically feasible robot trajectory.
