# Pipe a shell border

Pipe a joined shell border between two marks on a cake. Each shell should have
a rounded, ridged head and a tapered tail. Leave the cake and surrounding board
clean.

**Development package; not ready to submit.** There is no robot demonstration,
Dream run, media upload or measured task score. `task.draft.json` is deliberately
not named `task.json`. See `VALIDATION.json` for the remaining gates.

## Setup

The YAM station table is at Z = 0.7475 m. A 180 × 140 × 50 mm rectangular,
crumb-coated cake has its centre at (0.300, 0, 0.7755) m. Its top is Z = 0.8005 m.
A 200 × 160 × 3 mm board is centred at (0.300, 0, 0.749) m. The marked border is
the 90 mm line from (0.235, −0.045) to (0.235, +0.045) m on the cake top.

Use a hand-operated 20 ml icing syringe with a passive sliding piston and a
six-point star nozzle. Nominal barrel grip: 30 × 80 × 30 mm; piston diameter:
25 mm; maximum stroke: 40.74 mm. The nozzle is 40 mm long, tapering to a hollow
star aperture with a 2.5 mm mean radius. The model starts with 20 ml of icing.
Its barrel begins at (0.180, −0.160, 0.7775) m, nozzle along +Y; the plunger centre
is 60 mm behind it. A 50 × 40 × 15 mm rest supports the dispenser. The tool starts
on the table, outside both hands. The 80 g barrel and 25 g plunger are dynamic.

This is a proposed reproducible prop specification. No real dispenser, recipe
or piping reference has yet been measured. A syringe avoids pretending that a
rigid object is a deformable piping bag; pressure control still comes from
physical piston movement.

## Local checks

From the repository root:

```bash
.venv/bin/python -m unittest discover -s tasks/pipe-a-shell-border -p 'test_*.py' -v
.venv/bin/python tasks/pipe-a-shell-border/probe.py --out artifacts/piping-cpu-new
```

The CPU probe prescribes nozzle motion to test the material law. It is **not** a
robot policy or full-score demonstration. It took 0.19 s for 1.5 simulated seconds
on the development machine; that is not a GPU trial-runtime estimate. It produced
0.567 ml of icing with volume-balance error below 6 × 10⁻²² m³. The resulting
single deposit is a blob, not evidence of a complete shell border.

## Next native probes

Run only inside the existing team Isaac Sim environment after compute is funded:

```bash
python tasks/pipe-a-shell-border/probe_native.py --out artifacts/piping-native-zero --seconds 3 --force-n 0
python tasks/pipe-a-shell-border/probe_native.py --out artifacts/piping-native-force --seconds 3 --force-n 8
python tasks/pipe-a-shell-border/preview_yam.py --out artifacts/piping-yam-preview --steps 60
```

The first two clamp the barrel as a diagnostic and push the ordinary dynamic
plunger with a force; there is no imposed piston position. The YAM preview uses
the unclamped tool and ordinary ready robot pose. All are unscored diagnostics.
Their runtime, native contacts and SDK compatibility remain untested. CPU and
native probes use deterministic starting values and no random jitter; intended
task seed is 0. Intended task limit: 2,400 actions at 20 Hz.

## Material and acceptance limits

`material.py` contains a finite reservoir, compression pressure, yield pressure,
nozzle resistance, ballistic parcels and conservative viscoplastic surface flow.
Only current piston position, nozzle state and material state affect flow. The
material model has no target coordinates or shell list. `native.py` applies
pressure reaction to both native bodies and measured metal-lip contact reaction
to the barrel. The star opening is physical geometry, not a painted marking.

This is an approximation, not a calibrated cream simulation. It cannot model
overhangs, suspended strings or voids. The 1 mm default grid may smooth away
important star-tip ridges; the observed CPU deposit does not establish ridge
retention. Full scoring requires visible ridges, so a smooth bead cannot pass.
The surface is not yet coupled to every robot finger/body contact. A valid robot
runner must implement those contacts or conservatively reject such overlap;
neither has yet been validated. Cake damage is a conservative penetration audit,
not a cake-fracture simulation. Reset/trial recording and independent photo
scoring also remain to be completed after the mechanism passes.

The scene preview deliberately always scores zero. Do not turn CPU probe motion
into a demo, add hidden object-pose feedback to a policy, or fill in scores/media
before genuine robot runs. Demo and Dream must eventually use the same task,
material, seed, camera observations and run limit, followed by final rescoring.

## Review calibration

Accepted [filing #1374](https://github.com/robocurve/benchmark-tasks/pull/1374)
shows contact-based material laws can be useful. [Caulking #1454](https://github.com/robocurve/benchmark-tasks/pull/1454)
was asked to make flow depend on a working trigger; [cake smoothing #674](https://github.com/robocurve/benchmark-tasks/pull/674)
was rejected for lacking actual icing manipulation. These sources inform the
design, not approval of this untested implementation. All geometry and source in
this folder are original team work; no accepted task source was copied.
