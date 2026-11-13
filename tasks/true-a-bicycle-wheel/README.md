# True a wobbly bicycle wheel

**Development package. Not ready to submit.** Native trial 091 completes 202
robot actions, but a requested 90° wrench turn produces only 22.86° net nipple
rotation. Motor tracking lag loses engagement. The rim integrity checks pass
and the 203 sampled measured poses have no unexpected hull intersections.
A full repair, released revolution and Dream baseline are still required.
The slower096 trial stops at177 actions before insertion because of an overly
strict approach IK angular gate. Its jaw-point error still fits the reserved
mouth clearance. A corrected approach check and one stable re-alignment pass
local recorded-state replay; the native retry remains necessary.

The task is to adjust the spoke nipples until the wheel runs straight, remains
centred and spins freely. Scoring uses the resulting wheel geometry and spoke
tensions, never a hidden target nipple angle.

## Fixed scene

The 420 mm aluminium rim has 32 curved sectors connected by compliant native
joints. Round 2 mm steel spokes pull from alternating sides of a freely rotating
hub. The stand supports the axle and has a fixed runout pointer. Nipples 0 and 2
start 0.75 turn loose. The wheel starts 55° around its axle, with square nipple
flats phased 45°. See `task.draft.json` for the complete proposed setup.

The free 90 g wrench has a 3.25 mm working slot,5 mm flared mouth,175×10×4 mm steel
neck and 55 mm polymer grip. Slot-to-grip distance is 195 mm. A steel tang accounts
for the mass inside the grip. Actual jaw contact must turn the 3.23 mm nipple
flats. There is no attachment or automatic engagement. The left hand holds the
rim during service and must release it for judging.

The nominal corrected-state control retains 410–423 N spoke tension and 2.68 µm
lateral runout with the current accurate solver configuration. The starting
wheel earns zero because some spokes fall below 400 N. Merely making the rim
look straight by loosening it cannot earn points.

## Physics and limits

The model uses elastic rim compliance, tension-only native central springs and
simplified thread friction. Measured nipple rotation relative to its spoke
changes rest length by the 0.454 mm thread pitch. Equal and opposite reaction
torques act on nipple and spoke. Common wheel rotation does not tighten it.
An implicit elastic Coulomb drive supplies thread friction.

PhysX's native DistanceJoint tolerance is 25 mm in this installation. The authored
limit compensates that tolerance while preserving the physical spring rest
length. The isolated load-law control verifies the correction. Internal bearing
and eyelet interfaces use joints and collision filtering only between their
connected bodies; external tool contacts stay active.

These are engineering approximations, not a calibrated commercial wheel.
A latched guard checks rim strain, twist and joint continuity every physics
substep. Thread travel is limited to±3 turns. Unsupported deformation ends the
trial; permanent rim damage and stripped threads are not rendered. Runtime
material updates never move objects or change robot effort limits. A cache
skips only identical native float 32 attribute writes.

## Runtime and reproduction

Use the versions and source revisions in `ENVIRONMENT.json`. The current
configuration uses CPU PhysX and GPU camera rendering: PGS 128 position/4
velocity iterations,100µs physics steps and 20 Hz robot control. PGS 32 and the
500µs/128-iteration control under-resolve spoke preload and must not replace it.
The 200µs/255-iteration control also under-resolves preload (327–363 N) and is rejected.

CPU checks require NumPy and take under one second:

```sh
python -m unittest discover -s tasks/true-a-bicycle-wheel -p 'test_*.py'
```

A passive corrected-state control, using a new output directory:

```sh
python tasks/true-a-bicycle-wheel/scene_probe.py --out OUTPUT --seconds .5 --dt .0001 --solver-type PGS --solver-position-iterations 128 --solver-velocity-iterations 4 --reset-profile zero-defect-control --wheel-clocking-deg 55 --nipple-flat-phase-deg 45 --central-spring-candidate --distance-tolerance-compensation-m .025
```

Compile the service candidate and slower first-quarter diagnostic:

```sh
python tasks/true-a-bicycle-wheel/service_plan.py --out SERVICE.json
python tasks/true-a-bicycle-wheel/slow_contact_plan.py SERVICE.json --out SLOW.json
python tasks/true-a-bicycle-wheel/preview_yam.py --out OUTPUT --steps 380 --physics-hz 10000 --device cpu --solver-type PGS --solver-position-iterations 128 --central-spring-candidate --distance-tolerance-compensation-m .025 --plan SLOW.json --joint-tracking-diagnostic --tool-pose-servo-diagnostic --nipple-target-servo-diagnostic --judging-views
```

This is an unvalidated diagnostic, not the submission demo. It preserves the
first 160 approach actions and adds slower insertion, settling holds and a 4 s
quarter turn. Its 220 new commanded poses pass the measured-grasp offline
collision screen. That screen cannot predict future slip or contact response.
Trial 091 took 825 wall seconds for 10.1 simulated seconds with review cameras;
the slower 380-action candidate is estimated at about 26minutes. No complete
trial runtime or task seed variability has been measured. The interrupted096
trial took777seconds through177actions. Reset is deterministic.
Read the JSON status: Isaac can exit with code zero after a Python failure.

## Controller disclosure and judging

The scripted feasibility controller reads native wrench/nipple poses to correct
its grasp and engagement targets. It issues only ordinary bounded robot joint
commands. Dream uses its standard cameras and joint observations with identical
physics, without the scripted feedback. See `MOTION_PLAN.md`.

`JUDGING.md` specifies a pointer, feeler gauges, ruler and mechanical spoke
tensiometer. Full credit requires lateral runout≤0.5 mm; partial credit allows
≤1.5 mm. Both require radial runout≤1 mm, dish error≤0.5 mm, all 32 spokes within
400–1000 N, intact equipment and one complete released revolution. The limits
are for this fixture, not general bicycle service advice.

`assess_trace.py` extracts measured geometry and tension evidence.
`audit_native_trace.py` checks sampled native poses against robot/scene hulls.
Neither grants a success certificate. `scoring.py` evaluates a completed,
reviewed `wheel-judging-v 2` record. Incomplete, destructive or invalid outcomes
score zero. `VALIDATION.json` and `evidence/` preserve the earlier controls and
failures. No Dream run, media ID or upstream submission exists.
