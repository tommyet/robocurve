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
python tasks/peg-out-a-tshirt/probe.py --mode task-layout --seconds 3 --output /tmp/shirt-reset

# Contact diagnostic, not a submission demo.
python tasks/peg-out-a-tshirt/run.py --mode motion-probe \
  --plan tasks/peg-out-a-tshirt/peg-plan.json --judging-views --out /tmp/peg-pickup
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
and mesh readings never control the robot. Interrupted runs remain marked as
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

The selected ordinary peg rests expose 20 mm of each handle. Their native
passive check settled about 1 mm; final half-second position range was below
0.24 µm. Raw constrained-jaw velocities were not equally quiet, so this is a
pose-stability observation. The 300-action native pickup opens the mouth to 8.9 mm, lifts the peg 136 mm
and holds it for two seconds. It drifts about 8 mm and yaws 28° in the fingers;
replacement on the narrow rest fails. `attach-plan.json` uses the measured
held transform to attempt line capture and a five-second released hold. Its
1,160 actions pass the sampled hull checks; native fastening remains untested.

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
