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
Its barrel begins at (0.180, −0.160, 0.7775) m, nozzle along −Y; the plunger centre
is at (0.180, −0.100, 0.7775) m, 60 mm behind it. Both bodies start at yaw 180°.
A 50 × 40 × 15 mm rest supports the dispenser. The tool starts
on the table, outside both hands. The 80 g barrel and 25 g plunger are dynamic.

This is a proposed reproducible prop specification. No real dispenser or recipe
has yet been measured. A syringe avoids pretending that a
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

Twenty CPU tests cover finite volume, pressure causality, passive seal-force
direction, contact/damage gates, incomplete evidence, and rubric invariance.

The 13 November native positive/negative controls exercised the free piston in
a fixed diagnostic barrel. An 8 N press for 0.5 s followed by 0.5 s release
emitted 0.1587 ml; the zero-force control emitted none. Flow stopped on release,
and retained volume matched extrusion. Each one-second probe took about 7 s
including simulator startup. The recorded source hashes and traces are in
`evidence/native-passive-2026-11-13.json`. This proves pressure causality for that
revision, not a robot grasp or finished shell border.

## Next native probes

Run inside the pinned team Isaac Sim environment:

```bash
python tasks/pipe-a-shell-border/probe_native.py --out artifacts/piping-native-zero --seconds 3 --force-n 0
python tasks/pipe-a-shell-border/probe_native.py --out artifacts/piping-native-force --seconds 3 --force-n 8
python tasks/pipe-a-shell-border/preview_yam.py --out artifacts/piping-yam-preview --steps 60
python tasks/pipe-a-shell-border/plan.py --out artifacts/piping-pickup-plan.json
python tasks/pipe-a-shell-border/preview_yam.py --out artifacts/piping-pickup --steps 400 --plan artifacts/piping-pickup-plan.json
```

The first two clamp the barrel as a diagnostic and push the ordinary dynamic
plunger with a force; there is no imposed piston position. The YAM preview uses
the unclamped tool and ordinary ready robot pose. All are unscored diagnostics.
The fixed pickup plan is compiled before the trial from URDF kinematics and has
no live object-state input. Its interpolated path passes the local IK check;
grasp, retention and collision remain native simulation tests. The preview
records video, camera images and measured tool, piston, flow and contact state.
A 20-action native ready-pose preview completed in 25.9 s including startup,
with zero emission and no invalid collider contact. Pickup contact, material
appearance and complete-task runtime remain untested.
CPU and native probes use deterministic starting values and no random jitter; intended
task seed is 0. Intended task limit: 2,400 actions at 20 Hz.

## Material and acceptance limits

`material.py` contains a finite reservoir, compression pressure, yield pressure,
nozzle resistance, ballistic parcels and conservative viscoplastic surface flow.
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
heads and tapered tails; ridge retention still needs inspection in the native
robot render. Full scoring requires visible ridges, so a smooth bead cannot pass.
`contact_audit.py` conservatively rejects non-nozzle body overlap with icing or
cake, using every dynamic collision shape and measured rigid-body transforms.
This boundary prevents omitted finger smearing from earning credit; it may
reject a near miss because bounding boxes overestimate occupied volume.
Unknown collider types fail the preview. The ready-pose preview passed this
audit; manipulation and deliberately invalid contacts still need native checks.
Cake damage is a conservative penetration audit,
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

The planned motion follows [Wilton's shell technique](https://wilton.com/content/downloadable/WLTECH-131_Shells.pdf):
hold the star nozzle at 45°, build a head, then reduce pressure while drawing out
the tail and overlap the next shell. This supports the manipulation technique,
not the simulation's provisional cream or seal parameters.
