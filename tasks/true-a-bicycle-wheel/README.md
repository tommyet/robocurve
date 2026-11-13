# True a wobbly bicycle wheel

**Development package, not ready to submit.** The native wheel now settles and
holds its spoke adjustments in short tests. Wrench contact, robot manipulation,
a full-score demo and a Dream run are still outstanding.

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

An implicit elastic Coulomb drive models thread friction. It holds an adjustment
without restoring the nipple to its starting angle. All material torques are
applied every physics step. A cache skips only identical native float32
attribute writes. Object poses are written only during episode reset.

The historical reset loosens nipples 0, 2, 4 and 6 by 1.1 turns. A shorter
candidate loosens nipples 0 and 2 by 0.75 turn. Its linear CPU estimate starts
at 0.697 mm runout and 354 N minimum tension; two quarter-turn corrections per
nipple predict 0.232 mm runout and 585–777 N tension. This candidate needs native
verification before becoming the task reset. It does not require restoring an
arbitrary reference tension exactly.

These are declared engineering approximations, not measurements of a commercial
wheel. The model uses elastic rim compliance, tension-only spokes and simplified
thread friction. A latched guard checks rim strain, twist and joint integrity
at every material substep; leaving its declared domain ends the trial. It does
not render permanent rim damage or stripped threads. Thread travel is limited
to ±3 turns. See `VALIDATION.json` for parameters, limits and test history.

## Reproducing the current checks

The 38 CPU checks need NumPy, use no randomness and take under one second:

```sh
python -m unittest discover -s tasks/true-a-bicycle-wheel -p 'test_*.py'
```

In the pinned Isaac 6.1 environment, use a new output directory for each run:

```sh
python tasks/true-a-bicycle-wheel/scene_probe.py --out OUTPUT --seconds .3 --dt .000025 --solver-position-iterations 32 --reset-profile two-defect-candidate
python tasks/true-a-bicycle-wheel/wrench_contact_probe.py --out OUTPUT --dt .000025 --turn-deg -90
python tasks/true-a-bicycle-wheel/wrench_contact_probe.py --out OUTPUT --dt .000025 --turn-deg -90 --no-contact
python tasks/true-a-bicycle-wheel/preview_yam.py --out OUTPUT --steps 2 --physics-hz 40000
```

The wrench tests are explicit kinematic fixtures, not robot demos. Their
no-contact control moves the wrench 40 mm off the nipple. The YAM preview only
holds the ready pose and records cameras and native state. Read the JSON status
and physical checks: Isaac may exit with code zero after a Python failure.

An isolated spring passes the expected quarter-turn displacement check at a
25 µs step. The isolated rim remains bounded for two seconds. The full assembly
with elastic Coulomb friction passes 0.3 seconds at 25 µs and 32 solver
iterations: final runout 2.033 mm, final 20 ms rim drift 0.364 µm and thread drift
1.41e-6 turns/second. That run took 56 wall seconds. A 50 µs comparison still
had a small settling transient at 0.1 seconds; it is not yet a validated runtime
choice. Curated reports are in `evidence/`; none demonstrates robot truing.

## Scoring and remaining evidence

`JUDGING.md` uses a pointer, feeler gauges, a ruler and a mechanical spoke
tensiometer. Full credit requires lateral runout ≤0.5 mm; partial credit allows
≤1.5 mm. Both require radial runout ≤1 mm, dish error ≤0.5 mm, all 32 spokes
within this fixture's 400–1000 N range, intact equipment and a complete released
revolution. Destructive or invalid outcomes receive zero.

Next verify contact-driven tightening and release, complete ordinary YAM
joint-command manipulation, and demonstrate full score within the run limit.
Then run Dream with the same physics and score both recordings. No media ID,
final runtime, task score or submission certificate exists yet.
