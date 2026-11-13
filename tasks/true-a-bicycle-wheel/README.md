# True a wobbly bicycle wheel

**Development package, not ready to submit.** The robot has picked up the free
wrench. Reciprocal simulator controls identified the setting that caused
unforced wheel acceleration; CPU PhysX now uses once-per-step external forces.
Actual robot tightening and a full-score demonstration remain unproven.

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
native pickup has lifted it about 74 mm. The grasp-point translation stays within about0.8mm, but the tool rotates
about3° in the grasp, shifting the jaws roughly10mm at the long lever arm. Earlier kinematic jaw tests
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

The 47 CPU checks need NumPy, use no randomness and take under one second:

```sh
python -m unittest discover -s tasks/true-a-bicycle-wheel -p 'test_*.py'
```

In the pinned Isaac 6.1 environment, use a new output directory for each run:

```sh
python tasks/true-a-bicycle-wheel/scene_probe.py --out OUTPUT --seconds .3 --dt .000025 --solver-position-iterations 32 --reset-profile two-defect-candidate
python tasks/true-a-bicycle-wheel/wrench_contact_probe.py --out OUTPUT --dt .00005 --turn-deg -45
python tasks/true-a-bicycle-wheel/wrench_contact_probe.py --out OUTPUT --dt .00005 --turn-deg -45 --no-contact
python tasks/true-a-bicycle-wheel/preview_yam.py --out OUTPUT --steps 2 --physics-hz 20000 --device cpu
```

The wrench tests are explicit kinematic fixtures, not robot demos. Their
no-contact control moves the wrench 40 mm off the nipple. Without `--plan`, the YAM preview holds the ready pose. A frozen ordinary
joint plan can be passed for bounded pickup checks; see `MOTION_PLAN.md`.
Both modes record cameras and native state. Read the JSON status
and physical checks: Isaac may exit with code zero after a Python failure.

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

Reciprocal controls044 identify the sustained acceleration: enabling TGS
external forces every iteration reproduces it in the standalone scene, while
disabling it removes it in YAM through1.5 seconds. The latter keeps all15,002
rim checks valid. This configuration is now explicit in the wheel adapter.
The retained constructor-state control has a small initial rotation; the next
service trial uses the normal deterministic reset, which restores native body
poses and velocities before the ordinary robot commands.

PhysX documents both options as alternative ways to integrate the same external
impulse over a step ([TGS force application](https://nvidia-omniverse.github.io/PhysX/physx/5.8.0/docs/Simulation.html#tgs-force-application)).
The observed failure is specific to this tested scene/configuration; no claim
is made about all PhysX scenes. Curated reciprocal measurements are in
`evidence/native-force-integration-044-summary.json`.

Next verify robot-driven tightening, final release and full-revolution judging,
then run Dream with the same physics and score both recordings. The682-action
service candidate uses only ordinary joint commands, with optional bounded
integral joint tracking to compensate measured arm droop. A fixed empirical
grip transform accounts for the observed3° tool rotation; whether that grip
repeats under changing load still needs native evidence. It does not inspect
object state or change actuator effort limits. See`MOTION_PLAN.md`.

Use`--device cpu` with GPU-rendered cameras. The latest30-action diagnostic takes
129 wall seconds including startup. Full repair runtime and cost remain
unmeasured. No media ID, final task score or submission certificate exists yet.
