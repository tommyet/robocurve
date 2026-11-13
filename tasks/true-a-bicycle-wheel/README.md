# True a wobbly bicycle wheel

**Development package, not ready to submit.** The robot has picked up the free
wrench, but no valid tightening demonstration exists. A clean CPU PGS central
spring control now matches the isolated load law and remains bounded for 0.3 s
with live thread coupling. The wheel's angular momentum settles, rather than
continuously accelerating as in earlier TGS trials. The corrected-state PGS128 control retains 410–423 N spoke tension. Loaded
robot engagement and a complete released revolution remain unverified.
No Dream run or submission media exists.

The robot adjusts spoke nipples until the wheel runs straight, remains centred
and spins freely. Scoring measures the resulting wheel, not hidden target
nipple angles.

## Scene and mechanics

The 420 mm rim has 32 curved sectors with compliant native joints. Steel spokes
pull from alternating sides of a freely rotating hub. Actual nipple rotation
relative to its spoke changes rest length by the 0.454 mm thread pitch; the
material applies equal and opposite reaction torques to those bodies. Rotating
the whole wheel does not tighten a spoke. Clockwise rotation viewed from the
rim tightens the right-hand thread.

The free wrench has a 3.25 mm working slot and a 5 mm flared mouth. Its physical
lead-in guides engagement; there is no automatic attachment or pose correction.
The jaws must turn the 3.23 mm nipple flats through collision. Internal bearing
and eyelet interfaces are represented by joints and filtered only against their
own connected bodies. External wrench contacts remain active.

The current nipple flats are exposed 16 mm inward from the rim centreline.
The current wrench has a 175 × 10 × 4 mm steel neck and a 55 mm grip, with
195 mm between the slot and the grasp point. Its 90 g mass includes a steel
tang inside the polymer grip. The longer handle and shorter front axle give
the robot room to reach the nipples. This geometry passes sampled hull checks;
native pickup has lifted it about 74 mm. The grasp-point translation stays within about 0.8 mm, but the tool rotates
about 3° in the grasp, shifting the jaws roughly 10 mm at the long lever arm. Earlier kinematic jaw tests
transfer rotation, but an offline intersection check found up to 175 µm of
persistent penetration; finite-load engagement still needs validation.

A conservative 0.2 N m handle moment gives roughly 7.5 MPa weak-axis bending
stress in this rectangular neck (M divided by section modulus). This is an
engineering sizing estimate, not a measured tool certification.

An implicit elastic Coulomb drive models thread friction. It holds an adjustment
without restoring the nipple to its starting angle. All material torques are
applied every physics step. A cache skips only identical native float32
attribute writes. Object poses are written only during episode reset.

The reset loosens nipples 0 and 2 by 0.75 turn. After native settling it has
0.889 mm runout and190–647 N spoke tension, so it earns zero. A separate static
control with two quarter-turn corrections per nipple reaches0.297 mm runout
but only375 N minimum tension; it still fails the400 N floor. The planned
physical demonstration will make three quarter-turn corrections per nipple.
The older four-defect reset remains available only as a diagnostic reference.

These are declared engineering approximations, not measurements of a commercial
wheel. The model uses elastic rim compliance, tension-only spokes and simplified
thread friction. A latched guard checks rim strain, twist and joint integrity
at every material substep; leaving its declared domain ends the trial. It does
not render permanent rim damage or stripped threads. Thread travel is limited
to ±3 turns. See `VALIDATION.json` for parameters, limits and test history.

## Reproducing the current checks

The 61 CPU checks need NumPy, use no randomness and take under one second:

```sh
python -m unittest discover -s tasks/true-a-bicycle-wheel -p 'test_*.py'
```

In the pinned Isaac 6.1 environment, use a new output directory for each run:

```sh
python tasks/true-a-bicycle-wheel/scene_probe.py --out OUTPUT --seconds .5 --dt .0001 --solver-type PGS --solver-position-iterations 128 --solver-velocity-iterations 4 --reset-profile zero-defect-control --wheel-clocking-deg 55 --nipple-flat-phase-deg 45 --central-spring-candidate --distance-tolerance-compensation-m .025
python tasks/true-a-bicycle-wheel/preview_yam.py --out OUTPUT --steps 2 --physics-hz 10000 --device cpu --solver-type PGS --solver-position-iterations 128 --central-spring-candidate --distance-tolerance-compensation-m .025 --wheel-clocking-deg 55 --nipple-flat-phase-deg 45
```

The first command is a passive corrected-state control. The second holds the
ordinary robot ready pose. Neither is a task demonstration. The service plan
and disclosed pose-feedback options are described in `MOTION_PLAN.md`. Read
the JSON status and physical checks: Isaac may exit with code zero after a
Python failure. The older controls below preserve development history; they
are not the current task configuration.

An isolated spring passes the expected quarter-turn displacement check at a
25 µs step. The isolated rim remains bounded for two seconds. The full assembly
with elastic Coulomb friction passes 0.3 seconds at 25 µs and 32 solver
iterations: final runout 2.033 mm, final 20 ms rim drift 0.364 µm and thread drift
1.41e-6 turns/second. That run took 56 wall seconds. The minimal reset also passes0.3 seconds at50 µs with a valid guard at every
substep. Its0.902 mm runout differs by12.6 µm from25 µs, and it takes31 wall
seconds. Wrench interaction still needs its own convergence check. Curated reports are in `evidence/`; none demonstrates robot truing.

## Scoring and remaining evidence

`JUDGING.md` uses a pointer, feeler gauges, a ruler and a mechanical spoke
tensiometer. Full credit requires lateral runout ≤0.5 mm; partial credit allows
≤1.5 mm. Both require radial runout ≤1 mm, dish error ≤0.5 mm, all 32 spokes
within this fixture's 400–1000 N range, intact equipment and a complete released
revolution. Destructive or invalid outcomes receive zero.

Reciprocal controls 044 show that the force-integration option materially changes
this scene. They do not establish a general simulator defect. The202-action
robot trial 049 keeps every rim check valid but does not turn either nipple:
the wheel rotates during startup, while the fixed key path misses the target.
The physical tool grip also rolls progressively under load, reaching about 11°.

A preloaded starting shape does not solve the reset. In 055, with runtime thread
forces frozen and once-per-step integration, native angular momentum increases
by 0.0471 kg m²/s in 0.3 seconds (approximately 0.157 Nm). The rim stays intact;
that alone is insufficient to validate the mechanics. A CPU native DistanceJoint
candidate replaces the negative-offset axial D6 soft spring with a central
positive-distance spring. It is a diagnostic option, not the task default.
See `evidence/native-preloaded-reset-054-055-summary.json`.

PhysX documents the two integration options as alternative ways to integrate an
external impulse over a step ([TGS force application](https://nvidia-omniverse.github.io/PhysX/physx/5.8.0/docs/Simulation.html#tgs-force-application)).
These observed differences are specific to the tested scene. Preserve the
matched controls instead of promoting either option as universally correct.

The next demo may use clearly disclosed native tool-pose feedback to compensate
the physical grasp, issuing ordinary bounded robot joint targets. Scripted
feasibility demos are permitted; Dream retains camera/joint observations only.
Neither controller may alter object poses, attachments, forces or actuator
limits. The physical reset and genuine key engagement still need validation.

Use CPU physics with GPU-rendered cameras. Trial049 took 758 wall seconds for
10.1 simulated seconds; complete repair runtime remains unmeasured. No full-score
demo, Dream baseline, media ID or submission certificate exists.

### Latest native evidence: batches059–063

The compensated central DistanceJoint matches the isolated700N spring test:
initial equilibrium error1.2nm, final error0.372µm, and quarter-turn shortening
113.13µm against113.5µm expected. The physical modulus/rest length is unchanged;
the authored limit compensates PhysX's25mm numerical tolerance. Standard
proportional force integration passes; once-per-step integration retains45.7µm
static error.

This does **not** validate the whole wheel. At100µs, full-scene runout is0.905mm
and rim integrity passes, but unexplained axle torque is about−0.405Nm with
runtime thread torques/rest updates disabled. Native masses/COMs predict less
than0.0002Nm gravity torque. At500µs the first-step locked gap is131.6µm and
fails the unchanged100µm validity bound. See
`evidence/native-central-spring-063-summary.json`. The optional candidate bridge
and pose-assisted controller remain unvalidated; older successful short-settle
or offline hull screens do not establish a truing demonstration.

### Latest controls, 13 November

The compensated native DistanceJoint passes a clean PGS load-law test at a
100 µs step: a quarter-turn changes length by −113.502 µm, versus −113.500 µm
expected. Both equilibrium errors are below 1.3 nm. The full 55°-clocked wheel
with live thread coupling completes 0.3 s in 13.4 wall seconds at 32 position
and four velocity iterations. Runout is 0.852 mm; the loose nipples remain
stable. Axle angular momentum reaches −0.000242 kg m²/s and changes by only
−1.39×10⁻⁶ kg m²/s during the last 0.1 s. This is a passive-mechanics gate,
not a robot repair. Spoke tension is 25–478 N, so a nominal-rest-length control
must establish that the planned repair can satisfy the 400 N floor.

The inextensible-rim TGS diagnostic still develops artificial axle torque and
is not promoted. Historical TGS settling numbers above are not the current
PGS task baseline. See `evidence/native-pgs-071-074-summary.json`.

### Current corrected-state control and review evidence

PGS128 preserves410–423N spoke tension in the nominal corrected state, with
2.68µm lateral runout. The matched32-iteration result falls below the unchanged
400N floor. Both results are preserved in
`evidence/native-pgs-preload-080-082-summary.json`. This establishes a possible
corrected physical state, not robot repair. All 61 CPU checks pass.

`assess_trace.py` reconstructs the actual outer rim surface from native poses,
including rigid-sector rotations, and reports lateral/radial runout, dish and
all32 spoke tensions. It includes the known radial chord-error bound and never
labels robot-held rotation as a free revolution. Final judging still requires
continuous release and integrity review. `--judging-views` adds fixed key/gauge
cameras; they never enter policy observations.

`--dream` uses ordinary camera/joint observations in the same runner, rejects
demo feedback, and records raw versus ordinary bounded actions. No Dream
request or successful complete native repair has been recorded yet.

### Latest approach check

Native085 reached 158 actions before the scripted IK guard stopped a clear
approach. Only commands 159–160 need an approximate target: their computed
jaw errors are 0.379/0.602 mm including rotational error, within the physical
mouth's 0.885 mm half-clearance. The controller now reserves 0.135 mm of this
clearance during approach; insertion and turning keep their stricter checks.
The 202-command replay and 44-frame measured-geometry suffix screen pass
offline. Native engagement and repair are still unproven.
