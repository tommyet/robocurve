# Peg a T-shirt onto a clothesline

**Development only; not ready to submit.** The latest pickup retains the hem,
but an independent audit found front/back fabric intersections in its reset.
The longer trial is held. A valid two-peg hang, full-score demo, Dream run and
submission media are still missing; no score is claimed.

Hang a small T-shirt using two spring pegs, then let go. The garment has two
sewn fabric layers and open neck, cuffs and hem. Each wooden peg has two free
jaws, a hinge and a passive closing spring. The robot must open the handles,
feed fabric and line between the jaws, and release them through contact.
There are no cloth attachments, proximity grasps or animated object paths.

## Run

Use the pinned Isaac Sim 6.1 / IsaacLab / YAM environment in `ENVIRONMENT.json`.
Run from the repository root. Current commands are diagnostics, not successful
task demonstrations:

```bash
.venv/bin/python -m unittest discover -s tasks/peg-out-a-tshirt -p 'test*.py'
.venv/bin/python tasks/peg-out-a-tshirt/run.py --check-only

# Passive controls: the closed peg should retain the coupon; the open one drops it.
python tasks/peg-out-a-tshirt/probe.py --mode clamp --seconds 3 --output /tmp/closed-peg
python tasks/peg-out-a-tshirt/probe.py --mode open-clamp --seconds 3 --output /tmp/open-peg

# Actual free-peg opening and release, with the garment untouched.
python tasks/peg-out-a-tshirt/run.py --mode motion-probe \
  --plan tasks/peg-out-a-tshirt/peg-open-plan.json --steps 340 \
  --judging-views --out /tmp/peg-opening

# Short rest-bending diagnostic; this override is not adopted in task physics.
python tasks/peg-out-a-tshirt/probe.py --mode task-layout --line-pegs \
  --regular-refined --solver-iterations 128 --physics-hz 480 --seconds 1 \
  --rest-bend-angles restShapeDefault --no-render --output /tmp/shirt-rest-bend
python tasks/peg-out-a-tshirt/audit_self_contact.py /tmp/shirt-rest-bend \
  --out /tmp/shirt-rest-bend-audit.json
```

The station uses 480 Hz physics and 20 Hz control. Every policy gets the same
reset: the shirt starts over the laundry board, both pegs are freely clipped
to the empty line, and native physics settles for five seconds. The task limit
is 2,400 actions, including a final five-second released hold. The seed is zero.

A disclosed scripted feasibility controller may read actual cloth and peg
positions to select ordinary bounded joint and finger targets. Dream gets
normal camera/joint observations with identical scene physics and reset.
Neither controller may write material or prop poses, add constraints or change
forces. Recorded evidence includes native cloth states, robot and peg poses,
executed actions, source hashes, runtime and optional 960 × 720 judging views.
Interrupted trials remain marked as interrupted; diagnostic scores are null.

## Evidence and current blocker

The passive peg controls behave differently as expected. Native robot trials
also demonstrate physical peg opening, removal, turning and released capture
of the empty line. Those mechanisms do not establish garment hanging.

An earlier coarse-mesh clipping attempt let eight cloth faces cross the 3 mm
line axis. Its apparent retention is invalid. A regular 2.5 mm mesh addresses
that contact scale. With 128 cloth iterations and a wider ordinary pinch,
trial093 retains the hem after the other hand releases; its marked patch rises
345 mm. Sampled fixture and forearm checks are clear. Local fingertip contact
still has up to 0.410 mm nodal overlap and 1.10 mm linear-triangle overlap.

A subsequent self-contact audit finds 3,001 transverse front/back triangle
pairs in that trial's reset. The authored garment has none. Independent
edge/plane checks confirm sampled crossings away from sewn edges; separated,
coincident and shared-vertex controls are not flagged. This invalidates the
reset's layer-integrity claim. Native topology is verified to match the audit.
A matched contact-filter control did not resolve it. The next bounded control
tests the documented rest-bending convention: the default tries to flatten
the garment's sewn side folds instead of preserving their rest angles. The
longer clipping sequence must wait for a valid reset. `VALIDATION.json` preserves earlier
results and failures; `MOTION_PLAN.md` describes the unfinished sequence.

## Setup and judging

`task.draft.json` lists the proposed fixed layout. The shirt is 400 mm across
its sleeves, 280 mm across its body and 300 mm long, with nominal 180 g/m²
fabric and 33.9 g mass. Native surface FEM models stretch, bend, gravity and
self-contact. The 3 mm line is rigid. Cotton anisotropy, yarns, tearing and
wetness are omitted; stiffness, friction and peg torque are engineering
estimates. Numerical strain alone cannot certify undamaged cloth.

`JUDGING.md` uses visible jaw/fabric/line capture, a ruler and released retention.
One valid peg earns partial credit; two at least 180 mm apart earn full credit.
For five seconds, the whole shirt must remain at least 20 mm clear of table
and floor, supported only by the line and pegs. Unknown integrity or contact
leaves the result unscored.

```bash
python tasks/peg-out-a-tshirt/judge.py /path/to/judging.json \
  --evidence-dir /path/to/trial --out /path/to/reviewed-score.json
```

The judge binds measurements to evidence hashes. No completed judging record
exists. Native authoring follows [NVIDIA surface deformables](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/110.0/dev_guide/deformables/deformable_bodies.html).
The prior [sock-pegging submission](https://github.com/robocurve/benchmark-tasks/pull/760)
failed for rigid cloth, automatic clips and proximity scoring. This design
addresses those mechanisms, but novelty and ownership still require review.
