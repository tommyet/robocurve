# Relocated first-quarter diagnostic

This candidate has no native success claim. It addresses122's actual approach
overshoot and wrist reach limit. The default task layout remains unchanged.

The explicit `--relocated-fixture-diagnostic` moves the wheel10mm forward and
50mm toward the right arm, and lowers its axle10mm. The stand upright is10mm
shorter (227.5mm); its base stays on the tabletop. Wheel, spoke, nipple and
wrench dimensions/materials are unchanged. The axle becomes(0.360,−0.050,0.995)m.
The pointer, judging cameras and measured momentum origin follow this layout.
No runtime scene movement is involved.

The652-action/32.6-second route preserves the original right-hand pickup and
replans the left rim approach. It settles at22mm mouth lead, moves the final8mm
to a14mm lead over3 seconds, then inserts over3 seconds. It turns90° over4
seconds, withdraws16mm over3 seconds and settles before moving across the wheel
plane. Measured nipple alignment blends smoothly during the clear-front
transition only. Contact/turn targets receive full feedback and retain the same
IK, mouth-clearance, material and collision checks. All outputs are ordinary
bounded robot targets; no object state or effort limit changes.

Two alternatives were rejected locally. The 30 mm right / 10 mm lower layout reaches
a wrist limit under the measured122 nipple orientation. Lowering 25 mm resolves
that endpoint but puts the handle through the table during the turn/withdrawal.
The retained 10 mm forward / 50 mm right / 10 mm lower route passes its nominal and
measured-state screens. A screen cannot predict actual grasp slip, tracking,
contact penetration or wheel settling.

## Reproduce local screening

Use the pinned YAM adapter and a recorded122 trace, with a new output file:

```sh
python tasks/true-a-bicycle-wheel/relocated_plan.py REFERENCE_PLAN.json \
  --measured-trace TRACE.jsonl.gz --relocated-fixture-diagnostic --out PLAN.json
python tasks/true-a-bicycle-wheel/audit_robot_plan.py PLAN.json --out NOMINAL_AUDIT.json
python tasks/true-a-bicycle-wheel/screen_relocated_plan.py PLAN.json \
  --measured-trace TRACE.jsonl.gz --out MEASURED_AUDIT.json
```

The measured screen uses fixture/grasp snapshots 148/84 and 174/174, and checks
all 570 post-pickup commands in each case. The native planar wheel geometry is
translated to the candidate location; the stand is explicitly shortened. The
actual rim/jaw convex meshes and robot hulls are used, with conservative boxes
for circular shafts. Intended jaw and finger contacts still need physical
magnitude review in a native recording.

## Prepared native gates; not executed

First verify passive settling under the existing supported physics:

```sh
python tasks/true-a-bicycle-wheel/scene_probe.py --out PASSIVE_OUTPUT \
  --seconds .5 --dt .0001 --solver-type PGS --solver-position-iterations 128 \
  --solver-velocity-iterations 4 --reset-profile two-defect-candidate \
  --wheel-clocking-deg 55 --nipple-flat-phase-deg 45 \
  --central-spring-candidate --distance-tolerance-compensation-m .025 \
  --relocated-fixture-diagnostic --batch-sdf-notices
```

Then check the matching YAM scene and reset before the full 652-action attempt:

```sh
python tasks/true-a-bicycle-wheel/preview_yam.py --out YAM_OUTPUT --steps 2 \
  --physics-hz 10000 --device cpu --solver-type PGS --solver-position-iterations 128 \
  --central-spring-candidate --distance-tolerance-compensation-m .025 \
  --relocated-fixture-diagnostic --plan PLAN.json --joint-tracking-diagnostic \
  --tool-pose-servo-diagnostic --nipple-target-servo-diagnostic \
  --judging-views --batch-sdf-notices
```

Only after those gates pass, replace `--steps 2` with `--steps 652` and use another
new output directory. Based on the reference-layout runtime, allow about 40
minutes and a 3000-second wall cap. This is one quarter cycle, not the full repair,
released revolution, Dream baseline or submission demo. No new paid run has
been launched for this candidate.
