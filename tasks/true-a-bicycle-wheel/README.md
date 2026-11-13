# True a wobbly bicycle wheel

**Development package; not submission-ready.** The CPU mechanics checks pass.
The isolated native ring passes a two-second fine-step response test. Full
wheel/thread/contact integration remains unproven. No truing demo, Dream run or media ID exists.

The robot adjusts spoke nipples to leave a wheel straight, centred and freely
rotating. Finding the wobble and redistributing tension is the task; matching a
hidden target nipple angle is not a scoring criterion.

## Current implementation

The 420 mm centreline-diameter rim has 32 independent curved sectors connected
by compliant native joints. The tension-only steel spokes pull on both sides
of a freely rotating hub. Four neighbouring same-side nipples start 1.1 turns
looser than the balanced reference. Measured physical nipple rotation changes
spoke rest length by the thread pitch and applies an opposing thread torque.
The native wrench must transfer that torque through contact.

The curved rim avoids the 1.06 mm radial scallop of the earlier 32-box geometry;
its six arc subdivisions per sector keep geometric chord error below 0.03 mm.
The full scene includes a stand, colliding spoke rods, rotating square brass
nipples and an open-slot wrench. The spoke heads can tilt but cannot freely
spin; thread advance uses the nipple's measured rotation relative to the outer
spoke. Lead and friction torques act between those two actual bodies. A common
wheel/spoke/nipple rotation does not shorten a spoke. Clockwise nipple rotation
viewed from the rim tightens the right-hand thread. Midspan bending is
compliant, so a real
tension-gauge measurement has a corresponding physical response.

A YAM asset bridge registers the 130 native bodies and resets them only at an
episode reset. A before-substep material callback reads actual body state and
applies thread torques; it does not write object poses. The DirectGPU version
uses native tensor pose/force views. This bridge and the full scene are not yet
runtime validated.

The simplified material properties, thread friction and geometry are disclosed
engineering choices. They are not measurements of a specific commercial wheel.
Thread travel outside ±3 turns invalidates model scope. Detailed thread
stripping, permanent rim damage and unrestricted spoke buckling are not yet
represented. Native damage-domain, contact and stability checks remain needed.

## Evidence and commands

The 29 CPU checks use NumPy, take under one second and use no randomness:

```sh
python -m unittest discover -s tasks/true-a-bicycle-wheel -p 'test_*.py' -v
python tasks/true-a-bicycle-wheel/probe.py --out artifacts/wheel-cpu-probe.json
```

The small-displacement CPU model predicts 1.663 mm starting lateral runout and
about 0.125 mm lateral response to a single quarter turn. These are model
outputs, not robot evidence. Its frozen prestress approximation makes load
predictions invalid after a spoke becomes slack.

In the pinned Isaac 6.1 environment, run the isolated ring gate first:

```sh
python tasks/true-a-bicycle-wheel/native_probe.py --out artifacts/wheel-ring --seconds 2 --dt .000025 --adjust-at .1
```

This diagnostic fixes the hub, disables gravity and changes one spring rest
length halfway through. It is not a robot or wrench demonstration. The first
native DistanceJoint version did not respond at this scale. A D6 soft distance
limit produced a response; a 100 microsecond, damped run initially settled to
about 0.160 mm lateral runout but later developed an unstable translation/twist
mode. Reducing TGS velocity iterations from 32 to 4 did not fix it. Read both
`complete` and `bounded_small_response`; a completed process alone is not a
physical pass. A failed Isaac run may still leave exit code zero.

An isolated D6 spring under a known 700 N diagnostic load responds to a
quarter-turn rest-length change by 0.113398 mm, versus 0.1135 mm expected. Its
absolute equilibrium position is about 46 µm too short at a 100 µs step, so
the constitutive check fails. `spring_probe.py` separates this timestep/solver
question from the full ring. Its saved report is `evidence/native-spring-008.json`.
At a 25 µs step, the same isolated spring passes: static error falls to 2.8 µm
and the observed rest-length response is 0.113487 mm. This supports a timestep
convergence diagnosis.
The attempted four-second fine-step ring test hit a 240-second wall limit;
its old runner did not preserve motion samples. The runner now writes atomic
checkpoints and finalizes on termination. The subsequent 0.8-second test passes:
131 µm maximum adjustment response, 10.2 µm late drift and locked joint gaps
below 0.59 µm. Rim strain energy stays bounded after the adjustment. Its 50.8
seconds of wall time informed a two-second follow-up, with the adjustment at
0.1 seconds. That follow-up remains bounded throughout the earlier instability
window: 138 µm maximum response, 5.72 µm final drift and stable rim energy. It
takes 130 wall seconds. This validates the isolated ring gate, not the full
130-body scene or a truing action.

The next bounded diagnostic is the full scene:

```sh
python tasks/true-a-bicycle-wheel/scene_probe.py --out artifacts/wheel-scene --dt .000025 --seconds .1
python tasks/true-a-bicycle-wheel/wrench_contact_probe.py --out artifacts/wheel-contact --dt .000025 --turn-deg -90
python tasks/true-a-bicycle-wheel/wrench_contact_probe.py --out artifacts/wheel-no-contact --dt .000025 --turn-deg -90 --no-contact
python tasks/true-a-bicycle-wheel/preview_yam.py --out artifacts/wheel-yam-preview --steps 2 --physics-hz 40000
```

The wrench test uses an explicitly kinematic diagnostic fixture. The no-contact
control offsets it 40 mm along the nipple axis. Neither is a robot demo. The
YAM preview holds the ready pose and records cameras and measured body state;
it is unscored. Each output directory must be new. Native trial runtime, final
physics rate and total task cost remain unestablished.

## Judging and remaining work

`JUDGING.md` uses the stand pointer, feeler gauges and a basic mechanical spoke
tensiometer. Full credit requires at most 0.5 mm lateral runout; partial credit
allows 1.5 mm. Both require radial runout at most 1 mm, dish error at most 0.5 mm,
every spoke within this fixture's 400–1000 N range, a complete released
revolution and intact equipment. The old eight rim weight tests and 32 separate
hanging-weight/caliper tests have been removed.

Next establish stable mechanics and smaller-step agreement, contact-driven
nipple rotation with a no-contact control, thread friction/creep and invalid
outcome handling. Then complete collision-safe YAM manipulation, show a full
score within the run limit and run Dream on the same scene. A simple physically
reproducible assessor must score both recordings before media is finalized.

Accepted [filing](https://github.com/robocurve/benchmark-tasks/tree/main/tasks/file-a-steel-block-flat-down-to-a-scribed-line)
and [cord cutting](https://github.com/robocurve/benchmark-tasks/tree/main/tasks/cut-taut-cord)
informed the causal before-substep material structure. NVIDIA documents the
[D6 joint and soft-limit formulation](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/rigid_bodies_articulations/joints.html)
and [native tensor force interface](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/extensions/runtime/source/omni.physics.tensors/docs/api/python.html).
Their existence does not substitute for this task's own runtime evidence.
