# True a wobbly bicycle wheel

**Development package. Not ready to submit.** Native112 rotates one nipple
90.54° during its tightening stroke, but early contact loosens it and withdrawal
stays engaged. The trial stops at379/380 actions. Rim integrity and the sampled
unintended-collision screen pass; intended jaw contact has up to0.451mm authored
solid overlap and still needs improvement. The clearer122 entry stops at174/448:
native tracking overshoots into the nipple, and re-alignment then exceeds the
wrist workspace. A full repair, released revolution and Dream baseline are
still required. No further manipulation run is released.

A locally screened alternative now moves the fixture 10 mm forward / 50 mm toward
the right arm and shortens the stand 10 mm. Its slower 652-action first-quarter
route and matching explicit native flag are described in
`RELOCATION_DIAGNOSTIC.md`. Native reset, contact and withdrawal remain untested.

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
Native104 subsequently reached190 actions before a stage-boundary orientation
relatch requested an unreachable handle pose. The corrected latch passes local
measured-state replay and future hull checks; a native retry remains necessary.
Read the JSON status: Isaac can exit with code zero after a Python failure.

The optional `--batch-sdf-notices` changes only how identical native Float
updates are notified. A matched5000-step control preserved all501 sampled
states and final attributes exactly, with material-plus-physics time6.7% lower.
It does not lower the physics rate or skip material updates. The two-action YAM gate also passes, with matching final authored/cache
values. Native112 then turns the nipple90.54° during the intended tightening
stroke. Entry loosens it before seating, and withdrawal stays engaged; the
trial stops at379/380 actions during clearance. All380 sampled hull checks and
all native rim-integrity checks pass, but this is not a completed repair cycle.

The `clearance_contact_plan.py` diagnostic uses a14mm lead-in and
16mm withdrawal, with longer settling and a measured whole-square mouth-clearance
guard before moving across the wheel plane. It changes only ordinary robot
commands. Native122 nevertheless overshoots: actual whole-square clearance
changes from12.49mm to−1.72mm before intended insertion, rotating the nipple
over6°. Re-alignment stops with a57.3mm native-run IK residual. Local alternative
seeds/damping do not solve this workspace issue. Slower approach and a modest
fixture relocation need full local screening before another manipulation trial.
The complete1630-action service route passes its nominal hull screen,
but is not released for a native run until entry and withdrawal work.

`scene_probe.py --recenter-at-axle` is a separate coordinate precision
diagnostic. Before native attachment, it translates the complete fixture, bench
and world-ended joint anchors by the same offset. It audits all authored world
transforms; body-local anchors, material values and rotations are unchanged.
Native poses are reported in that translated frame, with the station origin
recorded explicitly. Native117 passes the geometry audit but retains the same
unexplained TGS axle momentum; the precision hypothesis is rejected. This
option has not been promoted into the robot runner.

The matched124 TGS control instead applies external forces once per step. At
100ms, axle momentum falls66% versus117 and its late growth rate decays, while
rim geometry/tensions remain similar. Startup momentum still greatly exceeds
the integrated gravity impulse. This short control does not establish long-run
validity; it has not replaced PGS or been used for a robot run.

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
