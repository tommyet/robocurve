# Wheel manipulation plan

This is a development plan, not a successful demo. The frozen commands use the
published setup and robot URDF. They do not read live object poses, spoke
tension, contact flags or the score.

**The pickup is mechanically demonstrated. Reciprocal force-integration
controls remove the sustained unforced wheel acceleration; normal-reset
service is next. The older499-action turn plan remains blocked by geometry**:
its nominal robot hulls intersect the hub and spokes by up to15.4mm. Use the
682-action`service-plan.json` candidate instead.

The pickup candidate starts the wheel 50° around its axle, with square nipple flats
phased by 45°. The 195 mm slot-to-grip wrench and a shorter front axle clear 38 sampled
engagement poses. An offline replacement route has 682 actions (34.1 s) and passes every sampled
commanded-pose hull check. It parks the wrench in front of the wheel, services
nipple 0 at a 55° wheel clocking, physically indexes the rim by −22.5° with the
left hand, then services nipple 2. This replacement is not a native demo and
does not yet include the final released revolution. The left hand approaches the continuous rim from above at a 45°
tilt and steadies it, after narrowing its opening to clear the stand. These are explicit reset settings; the native source
defaults remain unchanged until the candidate is checked.

1. Approach and grip the free wrench handle while the other hand grips the rim.
2. Lift the wrench 80 mm and hold it for inspection.
3. Approach nipple 0, insert the open slot, tighten clockwise by a quarter turn,
   withdraw through the mouth, reset the tool angle and repeat twice.
4. Repeat the three quarter turns at nipple 2, then withdraw and release.

The pickup segment has 82 actions (4.1 seconds at 20 Hz). The current turn
segment has 499 actions (24.95 seconds). The offline IK and velocity checks
pass with the recorded URDF. They establish reachability only. The robot still
needs to demonstrate collision-safe service motion, actual nipple rotation and
a complete released revolution for judging. There is no task score yet.

Compile from the pinned YAM Python environment:

```sh
python tasks/true-a-bicycle-wheel/motion_plan.py --out tasks/true-a-bicycle-wheel/pickup-plan.json
```

The preview checks the plan's source and URDF hashes before running. Begin
with two actions to verify integration, then expand only after inspecting the
native report:

```sh
python tasks/true-a-bicycle-wheel/preview_yam.py --out NEW --steps 2 --physics-hz 20000 --plan tasks/true-a-bicycle-wheel/pickup-plan.json
```

`audit_robot_plan.py` screens sampled commanded poses against the actual URDF
hulls and nominal scene geometry. It assumes a fixed grasp only to examine
clearance, and labels intended finger contacts separately. It cannot prove
grip, continuous-time collision safety or native task success.

The latest 82 sampled pickup poses have no unintended intersections with the
extended wrench, shortened front axle and far-side stand. The corrected straight-slot wrench also
transmits 32.90° of a 45° fixture command through contact, with all 16,000 rim
checks passing. That fixture clamps the hub explicitly for diagnosis; it is not
used by the task or offered as a successful robot demo.

The CPU 100 µs pickup finishes all 82 actions. The wrench rises about 74 mm,
and its final grasp error relative to the actual robot hand is below 0.8 mm.
An independent rotation-aware audit corrects the earlier droop attribution:
about10mm of the12mm jaw-position error comes from3° of tool rotation in the
grasp; only about2mm comes from arm tracking. The new plan includes a fixed
measured grip transform, and ordinary joint feedback addresses the arm error. The unheld hub
reaches 14.4 rad/s before the rim grip arrests it. That unforced acceleration
invalidates any task-success interpretation despite the mechanically sound
grasp. A no-rewind control also accelerates to 10.30 rad/s in 1.5 s.

The kinematic 45° jaw fixture is also insufficient evidence of precise
engagement: reconstructed jaw/nipple intersection reaches 175 µm. A bounded
dynamic fixture now applies at most 10 N and 0.35 N m at the grasp point. It
has not run and is deferred until the unforced wheel motion is resolved.

The portable replacement compiler preserves the exact682 screened commanded
poses, uses an explicit55° initial wheel clocking, and embeds its geometry and
URDF hashes. Compile it with`service_plan.py --out service-plan.json`. The
first202 actions include pickup, one quarter turn and withdrawal:

```sh
python tasks/true-a-bicycle-wheel/preview_yam.py --out NEW --steps 202 --physics-hz 10000 --device cpu --plan tasks/true-a-bicycle-wheel/service-plan.json --joint-tracking-diagnostic
```

This historical command is superseded by the PGS configuration below. The once-per-step force override did not resolve the original TGS assembly problem.
The optional PI controller reads only measured robot joints, bounds compensation
to0.12rad, and enforces the same position, speed and native effort limits. Its
native tracking performance and the first real wrench engagement remain to be
measured; this is not yet a successful task demo.

## Current PGS candidate

The matched zero-defect PGS128 control preserves410–423N spoke tensions and
2.68µm lateral runout. PGS32 underresolves preload and is not used for the
current robot trial. Run the screened682-action service candidate with
`--solver-type PGS --solver-position-iterations 128 --central-spring-candidate
--distance-tolerance-compensation-m .025 --physics-hz 10000 --device cpu`.
The optional scripted tool/nipple pose servo reads native poses only to issue
ordinary bounded joint targets; it never changes object state or effort limits.
Dream receives ordinary camera/joint observations and none of that feedback.

The separate `finalize_plan.py` appends physical key release, an ordinary
left-hand rim-spin attempt and12 seconds of hands-free observation. Its
1073 actions fit the proposed60-second budget. The first807 targets match a
fully screened prefix; all266 revised suffix targets pass the same hull screen.
The hand first withdraws30mm radially before crossing the wheel plane, avoiding
a spoke contact found in the earlier axial-only withdrawal. A full native
repair and released revolution remain unproven.
