# Pipe a shell border

Pipe a joined shell border between two marks on a cake. Each shell should have
a rounded head, visible ridges and a tapered tail. Leave the cake and surrounding board
clean.

**Development package; not ready to submit.** Partial robot trials exist, but no
full-score demo, Dream run or media upload. `task.draft.json` is deliberately
not named `task.json`. See `VALIDATION.json` for the remaining gates.

## Setup

The YAM station table is at Z = 0.7475 m. A 180 × 140 × 50 mm rectangular,
crumb-coated cake has its centre at (0.300, 0, 0.7755) m. Its top is Z = 0.8005 m.
A 200 × 160 × 3 mm aluminium cake board is centred at (0.300, 0, 0.749) m. The marked border is
the 90 mm edible guide line from (0.235, −0.045) to (0.235, +0.045) m on the cake top.
The line is 0.5 mm wide; its two transverse end marks are 10 × 0.5 mm.
All guide marks are 0.1 mm thick.

Use a hand-operated 20 ml plastic icing syringe with a passive sliding piston
and a stainless steel six-point star nozzle. Nominal barrel grip: 30 × 80 × 30 mm; piston diameter:
25 mm; maximum stroke: 40.74 mm. The nozzle is 40 mm long, tapering to a hollow
star aperture with a 2.5 mm mean radius. The model starts with 20 ml of icing.
Its barrel begins at (0.180, −0.160, 0.7775) m, nozzle along −Y; the plunger centre
is at (0.180, −0.100, 0.7775) m, 60 mm behind it. Both bodies start at yaw 180°.
A 50 × 40 × 15 mm plastic rest at (0.180, −0.160, 0.755) m supports the dispenser. The tool starts
on the table, outside both hands. The 80 g barrel and 25 g plunger are dynamic.

This is a proposed reproducible prop specification. No real dispenser or recipe
has yet been measured. A syringe avoids pretending that a
rigid object is a deformable piping bag; pressure control still comes from
physical piston movement.

## Run and inspect

Use the pinned Linux/NVIDIA environment in `ENVIRONMENT.json`. From the repository
root, compile the fixed plan, run it, then score the saved physical record:

```bash
python tasks/pipe-a-shell-border/plan.py --mode shell --press-stroke .007 --shell-count 3 --release-tool --out artifacts/piping-plan.json
python tasks/pipe-a-shell-border/run.py --policy demo --joint-feedback --plan artifacts/piping-plan.json --steps 2400 --out artifacts/piping-demo
python tasks/pipe-a-shell-border/audit_run.py artifacts/piping-demo --out artifacts/piping-demo/audit.json
```

The current three-shell plan is a development test, not a full border. The plan
is compiled from robot kinematics and a fixed, recorded tool-grasp calibration.
During execution, bounded PI correction reads ordinary joint angles only. It
changes action targets, not motor gains or object poses. The independent audit
uses the deposited material and measured tool/robot geometry. Confirm agreement
with the matching top and side photographs; a numeric score alone is insufficient.

A direct baseline uses the same scene and ordinary Dream observations:

```bash
python tasks/pipe-a-shell-border/run.py --policy dream --steps 2400 --out artifacts/piping-dream
python tasks/pipe-a-shell-border/audit_run.py artifacts/piping-dream --out artifacts/piping-dream/audit.json
```

Dream credentials must be configured privately through the client's credentials
file or environment. The Dream branch is implemented but has not yet run.
Do not use the generic scene runner's placeholder score; this task requires
`run.py` and `audit_run.py` for material coupling and assessment.

Trials use a fixed starting layout, no object jitter and 20 Hz control. The limit
is 2,400 actions, or 120 simulated seconds. The latest three-deposit
trial took 382.8 wall seconds for 957 actions on an RTX 6000 Ada. Full demo and
Dream runtimes remain unmeasured. Each run saves its exact Python source, plan,
video, photographs, joint actions, material state and contact audit.

## Validation so far

Run CPU checks without renting a GPU:

```bash
python -m unittest discover -s tasks/pipe-a-shell-border -p 'test_*.py' -v
```

Twenty-nine tests cover pressure causality, finite volume, contact and damage,
shape scoring and released-tool evidence. Native tests have demonstrated a
physical pickup, passive plunger extrusion and an elongated head and tail.
Native035 released the tool cleanly and scored0.25 under the current independent
scorer: two valid shell shapes, one with continuous ridges. The incomplete,
uneven finish is not submission quality. A full joined border remains pending.

The passive mechanism control emitted 0.1587 ml under an 8 N load and nothing
under zero load; flow stopped after release and volume balance closed. Those
controls are not robot task scores. Dated evidence is listed in `VALIDATION.json`.

## Fidelity and judging

`material.py` contains a finite reservoir, compression pressure, yield pressure,
nozzle resistance, ballistic parcels and conservative viscoplastic surface flow.
The surface now uses a depth-dependent shear yield and Herschel–Bulkley flow law;
see [MATERIAL.md](MATERIAL.md) for equations, sources and numerical limits.
Native033 and035 exercise this material law and whole-face nozzle contact.
Their conserved deposits provide mechanism evidence, not a completed border.
When icing submerges the star aperture, local pressure spreads it sideways over
a declared 2 mm transfer depth. The pressure law sees the nozzle and existing
material, without shell coordinates or templates. The 0.5 mm grid preserves
small ridges better than the initial 1 mm grid.
Only current piston position, nozzle state and material state affect flow. The
material model has no target coordinates or shell list. `native.py` applies
pressure reaction and passive seal drag to both native bodies, and metal-lip contact reaction
to the barrel. The star opening is physical geometry, not a painted marking.
Seal drag is capped at the relative momentum available in one physics step, so
the discrete friction update cannot reverse motion and introduce chatter.

This is an approximation, not a calibrated cream simulation. It cannot model
overhangs, suspended strings or voids. Offline shape probes produce rounded
heads and tapered tails; the native trials retain some ridges, but do not yet
produce a consistent finish. Full scoring requires visible ridges and an elongated head-to-tail shape.
A round mound cannot pass merely because it narrows at its edge.
`contact_audit.py` conservatively rejects non-nozzle body overlap with icing or
cake, using every dynamic collision shape and measured rigid-body transforms.
This boundary prevents omitted finger smearing from earning credit; it may
reject a near miss because bounding boxes overestimate occupied volume.
Unknown collider types fail the preview. Negative CPU controls exercise this
check; completed manipulation diagnostics pass it. Repeat the audit on each
final trial.
Cake damage is a conservative penetration audit,
not a cake-fracture simulation. The complete trial still needs independent photo scoring.

Demo and Dream must use the same scene, material, starting layout, observations
and run limit, followed by final rescoring. Scores and media stay unset until
those runs are complete.

## Review calibration

Accepted [filing #1374](https://github.com/robocurve/benchmark-tasks/pull/1374)
shows contact-based material laws can be useful. [Caulking #1454](https://github.com/robocurve/benchmark-tasks/pull/1454)
was asked to make flow depend on a working trigger; [cake smoothing #674](https://github.com/robocurve/benchmark-tasks/pull/674)
was rejected for lacking actual icing manipulation. These sources inform the
design, not approval of this untested implementation. All geometry and source in
this folder are original team work; no accepted task source was copied.

The physical technique follows [Wilton’s shell-border guide](https://wilton.com/how-to-pipe-a-shell-border/wltech-131/):
build a head with a star nozzle, reduce pressure while drawing a tail, and overlap
the next head with that tail. This supports the intended technique and shape,
not the simulation's numerical material properties. Checked 2026-11-13.

Native038 and042 longer-tail and pressure-taper trials remain uneven (0.25,0,0
under the current scorer). They conserve material and release the dispenser,
but do not demonstrate a full border. See
[evidence/native-three-shell-038-042.json](evidence/native-three-shell-038-042.json).
The next fixed trajectory uses continuous tail motion: two smoothstep segments
had unintentionally stopped the nozzle halfway through the tail. The material
and scoring thresholds are unchanged.
