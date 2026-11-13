# Peg a T-shirt onto a clothesline

**Development only; not ready to submit.** Native cloth pickup/carry and physical peg pickup/opening work. Fastening the
shirt to the line and leaving it hanging remain unproven. No
full-score demo, Dream run, final score or uploaded media exists.

Hang a small T-shirt using two spring pegs, then let go. The shirt has two sewn
fabric layers and open neck, cuffs and hem. Each peg has two dynamic wooden
jaws, a hinge and a constant closing spring. Squeezing the handles must open
the jaws through physical contact. There are no cloth attachments, proximity
grasps, animated object paths or runtime changes to spring targets.

## Run

Use the pinned Isaac Sim 6.1 / IsaacLab / YAM environment in `ENVIRONMENT.json`.
From the repository root:

```bash
# CPU checks; these do not prove simulation or task success.
.venv/bin/python -m unittest discover -s tasks/peg-out-a-tshirt -p test_local.py
.venv/bin/python tasks/peg-out-a-tshirt/run.py --check-only

# Bounded native physics controls.
python tasks/peg-out-a-tshirt/probe.py --mode clamp --seconds 3 --output /tmp/closed-peg
python tasks/peg-out-a-tshirt/probe.py --mode open-clamp --seconds 3 --output /tmp/open-peg
python tasks/peg-out-a-tshirt/probe.py --mode task-layout --line-pegs --physics-hz 480 --seconds 3 --output /tmp/shirt-reset

# Contact diagnostic, not a submission demo.
python tasks/peg-out-a-tshirt/run.py --mode motion-probe \
  --plan tasks/peg-out-a-tshirt/peg-open-plan.json --steps 340 \
  --judging-views --out /tmp/peg-opening
```

The full station runs at 480 Hz physics and 20 Hz control. The shared
`reset_scene.py` resets once and advances exactly 100 ready-position control
steps (5 seconds) before the first policy observation. Cloth and free pegs
settle together. Every policy must use this same reset. The task limit is
2,400 actions, including the final five-second released hold; settling is
recorded separately. The seed defaults to zero.

The runner saves ordinary camera images, native 960×720 judging views when
requested, source hashes, actual runtime and assessor telemetry. It checks
native deformable/self-contact registration and rejects attachments or
kinematic peg jaws. Frozen plans supply ordinary joint commands only; object
and mesh readings are assessor-only unless `--state-assisted-grasp` is
explicitly selected. That scripted feasibility mode measures the reset hem once
to center ordinary fingers, then uses bounded joint actions. It never writes
cloth or prop state and is separate from the Dream image/joint policy.
Interrupted runs remain marked as
interrupted. All current diagnostic scores are null.

## What has been demonstrated

The passive closed-peg control retains a cloth coupon; the open control drops
it. The actual task has free pegs, so that control alone does not prove pickup
or line capture. The thin laundry board required 480 Hz physics: the selected
reset has no sampled initial tunneling or final triangle/fixture intersections.

Batch020 completed the 620-action garment carry in 308.6 wall-clock seconds.
Both hem layers followed the grippers through a 331 mm lift. During the
one-handed line hold, the whole garment cleared the board by at least 35 mm.
It fell back onto the board after both hands opened. Seventeen sampled full
triangle/fixture audits were clear. This establishes contact and transport,
not successful hanging.

The earlier rest pickup opened a peg to 8.9 mm and lifted it 136 mm. Its later
horizontal line insertion failed integrity: cloth crossed the line axis and
the shirt touched the table. That recording earns no score.

The current reset instead has two spare pegs clipped to the empty line, with
handles downward. A three-second native test retained both freely moving pegs;
their final half-second hinge movement was below 3.3 µm. The shirt stayed on
the board with no sampled full-triangle fixture intersection. The combined
five-second YAM reset also completed in batch031. Its first feeding attempt
failed: the right forearm hit the line, never opened the target peg and the
shirt slipped from the other hand. The original vertex-only planner check
missed a thin line passing through a convex hull; it now clips the finite line
axis against every convex face. The old plan is blocked. Batch033 confirms that a tilted approach keeps the
wrist below the line and reaches the handles; a deeper ordinary hem grasp
also retains the shirt. However, dangling fabric brushes the peg off before
the squeeze. The isolated empty-peg trial035 opens its mouth to8.32mm, closes it and
leaves it on the line. Trial037 then opens the peg with the garment held
clear, but sideways fabric entry dislodges the upward-facing peg. It falls
on release, so that trial also earns no score. The next candidate withdraws
the held peg downward, turns its jaws downward in free space and clips the
cloth and line from above/front. No hanging demonstration exists yet.
The runner refuses plans still marked as awaiting their collision audit.

Line-clamp coupons exposed loaded jaw penetration. Halving the timestep or
raising passive damping reduced the maximum depth from 1.60 mm to about
0.55 mm, without a line-axis crossing. Neither change is adopted in the task.
The next robot trial tests slow ordinary handle closure; loaded contact must
be inspected before assigning any score.

## Setup, physics and scoring

`task.draft.json` lists the proposed prop sizes and positions. The shirt is
400 mm across its sleeves, 280 mm across its body and 300 mm long, with nominal
180 g/m² fabric and 33.9 g mass. Surface FEM handles stretch, bend, gravity and
self-contact; the taut 3 mm line is rigid. Cotton anisotropy, yarns, tearing and
wetness are omitted. Material stiffness, friction and peg torque are
engineering estimates, not calibrated physical measurements. Native strain
alone cannot certify intact fabric.

`JUDGING.md` defines visible capture, released retention and simple ruler
measurements. One valid peg earns partial credit; two separated by at least
180 mm earn full credit. The shirt must remain supported only by the line and
pegs for five seconds with at least 20 mm table/floor clearance. A peg merely
near the line earns nothing. Unknown integrity or contact leaves the result
unscored.

```bash
python tasks/peg-out-a-tshirt/judge.py /path/to/judging.json \
  --evidence-dir /path/to/trial --out /path/to/reviewed-score.json
```

The judge verifies the evidence-file digests before applying the rubric.
`interpret_motion.py` and `interpret_peg.py` provide offline diagnostics, never
success flags. No completed judging record exists yet.

Native authoring follows [NVIDIA surface deformables](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/deformables_beta/deformable_beta.html).
The earlier [sock-pegging submission](https://github.com/robocurve/benchmark-tasks/pull/760)
failed for rigid cloth, automatic clips and proximity scoring. This design
addresses those omissions, but ownership and novelty still need review.
[BEHAVIOR clothesline hanging](https://behavior.stanford.edu/knowledgebase/tasks/hanging_clothes_on_clothesline-0.html)
is relevant prior work; its draping task does not establish novelty here.

Trial043 physically removes and turns the opened spare peg by120degrees.
The hand deflects24mm upward under load, so its mouth misses the line;
the hem also creeps out before closure. Both props fall, with no score.
The revised1,220-action candidate deepens the hem bite10mm and corrects
the clipping target using ordinary right-arm joint observations. Its bounded
PI changes only ordinary joint targets; it never reads cloth or peg state.
All reference poses pass the rigid-hull and finite-line-axis rejection check.
Actual capture, contact integrity and released retention still need native proof.

The next scripted candidate can use `--state-assisted-grasp` to handle measured
reset variation. Both observed043 and050 reset shapes pass the200-action
collision rejection check after this calibration. All later reference actions
remain unchanged. The actual executed plan, input-state hash and grasp targets
are saved with the trial. This calibration physically retained the shirt in
later trials; it does not establish correct clipping or hanging.

Batch058 retained the unused peg throughout the corrected approach. The first
clip was withheld after830 actions when the mouth controller could not produce
a reachable target. Its corrected outer loop integrates the desired TCP instead
of adding measured hand compliance repeatedly; all11 available recorded input
states pass the local hull screen. Batch064 tests six seconds of alignment
before closure. Its mouth alignment converged to1.47mm and the peg closed.
However, eight garment faces crossed the3mm line axis and remained there
after both hands withdrew. That retention is invalid and receives no score.

A denser mesh is under test with the same garment, mass, material and line.
Adaptive refinement introduced0.2mm seam features; its069 reset moved some
sleeve nodes through the support board. The regular2.5mm-grid candidate keeps
the1.6mm seam width, has30,538nodes, and changes no physical geometry. Select
it explicitly with `--regular-refined` in either the passive probe or YAM
runner. Batch072 completed the five-second passive reset with no sampled
board/leg/table triangle intersections. Batch075 lifted the shirt but lost it
when one hand released: material passed through the remaining finger pads
by3.36mm. It never reached the line. The next320-action diagnostic uses an
ordinary finite pinch target (0.939mm commanded jaw gap) with unchanged
physics. Real intact grasp and released line capture remain unproved.
