# Peg a T-shirt onto a clothesline

**Development only; not ready to submit.** The latest pickup misses the hem,
and an independent audit finds front/back fabric intersections in its reset.
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

# Passive reset with the validated sewn-seam rest angles.
python tasks/peg-out-a-tshirt/probe.py --mode task-layout --line-pegs \
  --regular-refined --solver-iterations 128 --physics-hz 480 --seconds 5 \
  --rest-bend-angles restShapeDefault --output /tmp/shirt-rest-bend
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
A matched contact-filter control did not resolve it. The default bending
convention tries to flatten the sewn side folds. Matched one- and five-second controls preserving their actual rest angles
have zero sampled self-crossings, gravity-consistent initial motion and no
final fixture intersections. The corrected rest convention is now adopted.
The follow-up YAM trial113 still has 1,255 transverse pairs at reset and misses
the garment. The standalone result does not validate the integrated reset.
A matched YAM control121 changes only the supported force-integration option
to once per step. All eight recorded reset states have zero transverse
self-crossings, final fixture checks are clear, and maximum edge strain is
4.45%. This isolates a numerical instability; it does not establish its exact
underlying cause.

Diagnostic125 uses that setting with an explicitly taller, 180 mm laundry
support and a measured lateral hem approach. It completes 320 actions in
549.94 seconds, but misses the pickup: the hem rises less than 1 mm and remains
on the support. Eight sampled self-contact states, fifteen fixture checks and
twelve robot checks are clear. The left target lies in the native fingers'
central notch; the right hem moves aside during entry.

The local-only `lateral_pad_candidate.py` instead re-observes the hem just
before insertion and aims at continuous pad surfaces, 8 mm off that notch.
All 320 commanded rigid checks and fourteen sampled cloth-approach checks
pass. It is not wired into the runner or tested physically; finger contact
and retention remain unproven. The draft still specifies the 100 mm support.
`VALIDATION.json` preserves the evidence and failures.

To reproduce the unsuccessful short pickup diagnostic125:

```bash
python tasks/peg-out-a-tshirt/run.py --mode motion-probe \
  --plan tasks/peg-out-a-tshirt/gentle-wide-grasp-plan.json --steps 320 \
  --regular-refined --solver-iterations 128 \
  --external-forces-once-diagnostic --raised-support-diagnostic \
  --state-assisted-grasp --reset-diagnostic --binary-cloth-trace \
  --judging-views --out /tmp/shirt-lateral-pickup
```

Use a new output directory for each trial. This is a diagnostic command, not
an instruction to spend compute automatically.

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
