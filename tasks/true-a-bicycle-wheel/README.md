# True a bicycle wheel

**Development package — not ready to submit.** The CPU model demonstrates
coupled spoke/rim response. It is not a robot demonstration and does not establish
that a complete task can be built for $3. No simulator or Dream run has occurred.

The task is to correct lateral runout by adjusting spoke nipples, then leave the
wheel straight, centred and usable. The assessor spins it to measure runout. This tests locating a structural error and
redistributing tension, rather than turning a marked screw to a target angle.

## What is implemented

- A 32-spoke, 420 mm rim-diameter engineering model. Each steel spoke is a
  tension-only axial spring; each nipple turn changes rest length by the thread
  pitch. Ring hoop/bending stiffness couples all spoke locations.
- A deterministic reset with four neighbouring same-side nipples loosened by
  1.1 turns; quarter-turn and reverse-turn probes;
  a complete slackening adversary; an assessor load probe.
- A conservative, provisional scorer with explicit integrity, free-rotation,
  centring and load-recovery checks. Unknown observations fail closed.
- An authored native PhysX probe with 32 rigid rim segments, implicit compliant
  D6 rim joints and tension-only distance-joint spoke springs. It is not yet run.
- A further authored stage builder, `wheel_scene.build_scene`, adds the fixed
  stand, freely rotating hub, colliding steel spoke segments, rotating square
  nipples and an open-slot wrench in the proposed station layout. Its measured
  thread coupling is implemented, but no native scene or robot run is validated.

All geometry, stiffness and tolerance values are development choices, **not
measurements of a selected commercial wheel**. The model linearizes rim motion
and freezes transverse prestress stiffness at its reference state. Its load
prediction is out of scope once any spoke is slack. It does not include
crossing friction, rim torsion/buckling, hub bearing friction or wrench contact.

## Reproduce the local checks

From the repository root:

```sh
.venv/bin/python -m unittest discover -s tasks/true-a-bicycle-wheel -p 'test_*.py' -v
.venv/bin/python tasks/true-a-bicycle-wheel/probe.py --out tasks/true-a-bicycle-wheel/evidence/mechanics-probe.json
```

These NumPy-only checks take under one second on the development machine and use
no GPU, API key or network. No random seed is used. `evidence/` contains the
actual CPU output, explicitly labelled as a mechanical probe. The algebraic
restoration of the initial nipple lengths is a solver sanity check, not a demo
policy. Full trial runtime and run limit remain unverified.

The final local reset produces **1.663 mm** lateral peak-to-peak runout, 0.383 mm
dish shift and 0.279 mm radial runout in the linearized CPU model. These are
model outputs, not physical calibration. They supersede an earlier exploratory
sinusoidal reset involving all spokes.

On the funded existing Isaac environment, from the repository root:

```sh
python tasks/true-a-bicycle-wheel/native_probe.py --out artifacts/wheel-native-001 --dt 0.001 --seconds 8
```

This bounded isolated test fixes the hub, disables gravity and changes one
spring rest length by a quarter turn halfway through. It tests the native ring
response, not wrench skill or robot success. Its output includes `initial.usda`,
`final.usda` and measured transform samples. Repeat at half the time step only
if the first run is stable, then compare runout and ring gaps. The native model
is a different discretization from the CPU linearized solver; matching is a
validation requirement, not an asserted fact.

Once that isolated probe passes, the complete proposed native geometry and
thread coupling have a separate bounded settling diagnostic:

```sh
python tasks/true-a-bicycle-wheel/scene_probe.py --out artifacts/wheel-scene-001 --dt 0.001 --seconds 2
```

It records live PhysX transforms and material state. There is no robot, tool
motion plan, task score or claim of successful truing in this diagnostic.

`wheel_scene.build_scene(stage, root)` is the next native stage. Call it during
scene authoring, then create `thread_coupling.NativeThreadCoupler(stage_id,
metadata)` after attaching the stage. The runner must call `before_step()`
before every physics substep, as accepted custom force models do. This callback
must not be exposed to a robot policy. A YAM custom-asset/reset wrapper and full
trial runner are not yet wired; importing this module alone does not install it.

The full stage uses two colliding steel half-rods per spoke, joined by an
implicit axial soft limit. They transmit tension without an axial compression
spring. Square-nipple rotation shortens the spoke rest length and produces the
equal/opposite thread lead torque on nipple and hub. Native capped angular
damping approximates thread friction; creep and work balance need checking.
The model has no hidden attachment, object pose update or proximity trigger.
Travel outside ±3 turns from the nominal reference **invalidates the trial**;
it is not silently clamped. Physical thread stripping, rim damage and detailed
spoke buckling are not yet represented. The native scene remains unrun.

## Required before a GPU task trial

1. Select a real wheel/stand/wrench and measure its geometry, loaded response,
   nipple torque and usable adjustment range. Validate the judging tolerances.
2. Validate the authored native scene and thread coupling. The visible wrench
   must rotate nipples through actual contact, with reaction torque reaching
   the tool. Check free hub rotation, thread friction/creep, slack and slip;
   add a credible damage/stripping model or an explicit invalid-outcome domain.
3. Verify substep stability and force/energy behaviour before adding the robot.
   The stiff spoke/rim constants cannot safely be fed as explicit forces at
   240 Hz without stability analysis; a kinematically reshaped visual rim would
   omit the interaction being tested.
4. Make an open-loop or camera/joint-feedback demo, then one ordinary Dream run
   on the identical scene. Do not use privileged rim/tension feedback in a demo.
5. Rescore the actual videos, record runtime/environment, and create media.

The deterministic proposed layout is in `setup.json`: the hub is 1.005 m above
the floor and the 420 mm rim sits above the 747.5 mm tabletop. The robot must
rotate the wheel to bring each nipple into reach; this has not been checked.

Accepted [filing](https://github.com/robocurve/benchmark-tasks/tree/main/tasks/file-a-steel-block-flat-down-to-a-scribed-line)
and [cord cutting](https://github.com/robocurve/benchmark-tasks/tree/main/tasks/cut-taut-cord)
were inspected for their before-substep material/contact hooks and concise task
structure. Their acceptance does not validate this wheel model.

The native spring implementation follows NVIDIA's documented
[distance-joint spring schema](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/schemas/physxschema.html)
and [isolated simulation stepping](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/simulation_control/simulation_control.html).
Implicit springs avoid the explicit-force stability limit; they still require
runtime, contact and convergence validation.
