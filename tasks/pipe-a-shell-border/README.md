# Pipe a shell border

Pipe a joined row of ridged icing shells between two marks on a cake, then set
the dispenser down. The task tests coordinated pressure and tool motion.

**Awaiting final review evidence and Dream baseline.** Native trial 099 scores 1.0:
six ridged shells covering 87 mm, with the dispenser released. Its broad photographs
support the shape, but close-ups are being recorded to inspect the small ridges.
No media has been uploaded and no PR has been opened.

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
star aperture with a 2.5 mm mean radius, six lobes, and radial limits of 1.625–3.375 mm. The metal outer radius is 4 mm (minimum wall 0.625 mm). The model starts with 20 ml of icing.
Its barrel begins at (0.180, −0.160, 0.7775) m, nozzle along −Y; the plunger centre
is at (0.180, −0.100, 0.7775) m, 60 mm behind it. Both bodies start at yaw 180°.
A 50 × 40 × 15 mm plastic rest at (0.180, −0.160, 0.755) m supports the dispenser. The tool starts
on the table, outside both hands. The 80 g barrel and 25 g plunger are dynamic.

This is a proposed reproducible prop specification. No real dispenser or recipe
has yet been measured. A syringe avoids pretending that a
rigid object is a deformable piping bag; pressure control still comes from
physical piston movement.

## Run and score

Use the Linux/NVIDIA stack pinned in `ENVIRONMENT.json`, with its YAM adapter
installed. Run from the repository root, using the IsaacLab environment's Python.
The saved plan includes the complete physical pickup, six shells and release:

```bash
python tasks/pipe-a-shell-border/run.py --policy demo --joint-feedback --state-assisted-demo --plan tasks/pipe-a-shell-border/demo-plan.json --steps 2400 --tool-substep-trace --out artifacts/piping-demo
python tasks/pipe-a-shell-border/audit_run.py artifacts/piping-demo --out artifacts/piping-demo/audit.json
python tasks/pipe-a-shell-border/run.py --policy dream --steps 2400 --out artifacts/piping-dream
python tasks/pipe-a-shell-border/audit_run.py artifacts/piping-dream --out artifacts/piping-dream/audit.json
```

Configure Dream credentials privately through the client environment or its
credential file. Never put a key in a command, task file or recorded artifact.
Use a new output directory for every run. The generic scene runner's placeholder
score is not this task's score; `run.py` performs the material coupling and
`audit_run.py` independently scores the saved physical record.

Both policies get the same fixed layout,240 Hz physics,20 Hz controls, motor limits
and 2,400-action limit (120 simulated seconds). There is no object jitter or
randomized scene seed. The demo ends after 994 actions (49.7 s); trial 099 took 459 s
on an RTX 6000 Ada. Dream wall time remains unmeasured.

The scripted demo openly uses native barrel/plunger poses and joint angles to
command bounded ordinary joint targets. A fixed pressure/motion recipe and
recorded joint feedforward compensate tracking lag. It never moves objects,
changes motor gains, reads the score or injects icing. Dream receives its normal
camera and joint observations, without this assistance.

Each trial saves native video, setup and judging photographs, actions, tool
poses, material state, contact audit, source hashes and the exact demo plan.
The optional substep trace allows a separate consistency check:

```bash
python tasks/pipe-a-shell-border/replay_material.py artifacts/piping-demo --out artifacts/piping-replay
```

That replay is a diagnostic of measured inputs, not another robot demonstration.

## Judging and evidence

[JUDGING.md](JUDGING.md) defines the ruler/photo checks and partial credit. Count
actual raised heads, tapered tails and continuous ridges; a plain line or row of
round blobs cannot pass. The scorer uses the final material surface, not intended
shell locations. Full credit also requires a joined finish and released tool.

Trial 099's exact 11,928-step input replay reproduces deposited volume to numerical
precision. Its independent audit finds 87 mm of valid decoration, six ridged shells,
no qualifying spill or cake gouge, and more than 63 mm clearance from the border
at release. A visible film outside the strip is at most 0.097 mm thick; the rubric
counts spill from 0.5 mm. This film is present in the photographs and is not hidden.
See [the recorded evidence](evidence/native-six-shell-099.json).

The scorer originally treated a low tail shoulder as a separate head and
truncated the last shell. Its correction applies the existing 2.5 mm head-height
minimum before segmentation. Over-height and oversized mounds still obstruct a
shell; disconnected icing cannot supply a tail. No judging threshold changed.

```bash
python -m unittest discover -s tasks/pipe-a-shell-border -p 'test_*.py'
```

The 43 CPU checks cover pressure causality, finite volume, physical contact,
damage, negative shape controls, segmentation and released-tool evidence.
Older experiments remain in `evidence/` and `VALIDATION.json`; their scores are
historical and should not be substituted for the final pair of runs.

## Simulation limits

A passive sliding piston compresses a finite reservoir. Pressure drives flow
through the physical star aperture. Ballistic parcels and a conservative 0.5 mm
surface grid model deposited icing; a Herschel–Bulkley law controls spreading.
The tool receives pressure, seal-drag and contact reactions. Both the metal
nozzle and material law use the same aperture. See [MATERIAL.md](MATERIAL.md).

The cream and seal parameters are engineering approximations, not measurements
of a particular commercial recipe. The model omits suspended strings, overhangs,
voids and thixotropy. It cannot simulate finger smearing: non-nozzle overlap with
icing or cake invalidates the run. Cake gouging is a penetration measurement,
not a fracture simulation. Review the native photographs alongside the score.

The technique follows [Wilton's shell-border guide](https://wilton.com/how-to-pipe-a-shell-border/wltech-131/):
build a head, draw a tapered tail while reducing pressure, and overlap the next
head with it. Accepted [filing #1374](https://github.com/robocurve/benchmark-tasks/pull/1374)
and feedback on [caulking #1454](https://github.com/robocurve/benchmark-tasks/pull/1454)
and [cake smoothing #674](https://github.com/robocurve/benchmark-tasks/pull/674)
informed the need for causal material manipulation. Those decisions do not
establish acceptance of this task. No other team's task code was copied.
