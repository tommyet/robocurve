# Uncap a spray can and coat a panel

Development prototype: local scorer checks pass. Native scene initialized and
ran a 150-step stability probe. A 600-step two-arm cap-removal diagnostic
failed to detach the cap; no paint was emitted. Robot access, cap removal,
nozzle operation and a full-score demonstration remain **unverified**.
No model score, successful demo, media ID or submission is claimed. A complete
601-frame three-camera H.264 diagnostic video exists locally; it is explicitly
labelled as a prototype, not a spraying demonstration.

The robot removes an ordinary friction cap, parks it, grips the cylindrical
can and presses its button while sweeping blue spray over a white panel. This
tests bimanual tool use and spatial coverage rather than a priming rule.

## Fixed setup

World metres; table surface z=0.7475. No object jitter. See `config.py` and
`task.py` for all positions. Paint and fixtures are procedural assets.

| Object | Geometry, material and starting state |
|---|---|
| Can | Orange aluminium cylinder, 52 mm diameter × 140 mm overall body height, 250 g, upright at (0.26,0), nozzle points +x. No handles. |
| Cap | Hollow charcoal plastic friction cap, 60 mm outside diameter × 34 mm height, 18 g, approximately 3 mm side wall and 2 mm lid. Initially on the can. Compound 24-segment rigid ring. |
| Button | White plastic 18 mm diameter × 10 mm high actuator, 3 g, 3 mm native prismatic stroke. Starts released, centre 77 mm above can centre. |
| Target | Fixed white steel panel, 140 × 140 × 2 mm, vertical face x=0.47, centre y=0,z=0.9875. |
| Backing | Neutral grey backing, 360 × 360 × 12 mm, fixed behind target. |
| Stand | Two-foot steel frame with 18 mm square uprights, diagonal braces, crossbar and four panel mounts behind the backing. |
| Pads | Blue cap pad and grey can pad, each 100 × 100 × 2 mm, fixed on table. |

## Proposed rubric

End-state score, with irreversible invalidation if the can or cap falls more
than 30 mm below the tabletop or telemetry is invalid:

- 0.25: cap detached, cap centre moved more than 60 mm from its seated position at least
  once, cap subsequently on its pad (45 mm horizontal tolerance, 12 mm vertical
  tolerance, speed below 20 mm/s).
- 0.50: above, and at least 50% of the target receives the minimum coat, with
  no more than 15% cumulative overspray.
- 0.75: above, and at least 90% coverage.
- 1.00: above, can upright within 10 degrees on its pad (35 mm horizontal,
  12 mm height tolerance; speed below 20 mm/s), nozzle released to below 0.5 mm
  depression, both TCPs more than 70 mm from can/cap centres, held for 1 second.

Coverage uses 10 mm square cells and at least 0.08 effective centre-plume
seconds per cell. Overspray is emitted flux missing the panel, including rays
that miss the backing, face away or hit conservative cap/hand occluders.
It is cumulative and cannot be erased by a later successful pass. The can has
a finite 12-second spray supply. A press is at least 2 mm actuator displacement.
The cap must have been removed before spraying can receive credit.

## Fidelity and unresolved work

Can, cap and button use native rigid colliders. The cap uses a guided axial
spring detent (1,800 N/m) released after 4 mm travel; this approximates a snap
fit and is not calibrated to a commercial product. The nozzle is a native
spring-return piston (2,200 N/m). The cap has no extra robot grasp features.

Paint is a geometric 12-degree half-angle cone, integrated at 20 Hz with
centre-weighted angular flux on a fixed plane. Scored range is 120–300 mm.
There are no aerosol particles, airflow, droplets, wet-film flow or drying.
Coloured surface tiles visualize measured accumulated dose. Sparse spray-mist
points are appearance only, enabled by measured actuator depression; they
do not apply forces or contribute to scoring. A 35 mm cap sphere
and 10 mm TCP spheres provide coarse occlusion; full finger/arm mesh raycasting
remains missing. TCP spheres do not represent complete gripper geometry.
Mass conservation uses a small-angle quadrature approximation. Numerical coat
thresholds require validation before any real-world fidelity claim.

First verify collision geometry, joints created before physics initialization,
cap retention force and clearance, normal grasp access, button contact and
release, and actual current/force limits. Then implement a feedback robot demo
using only ordinary arm commands, record a full-score run and repeat from a
sealed start. Only then spend Dream requests. Reproduce scores from measured
telemetry, review all three camera views, and retain hashes of final sources.

The native runner completed a no-model hold probe on the existing L40S. This
is the command to reproduce it:
to check geometry, initial stability, joints and camera views. This probe holds
the arms ready and cannot demonstrate cap removal or nozzle actuation:

```sh
/data/IsaacLab-Arena/.venv/bin/python tasks/uncap-spray-panel/run.py \
  --policy probe --max-steps 150 --log-dir ~/yam-eval/spray-probe-001
```

The `--policy capprobe` mode uses `task.demo()` for a diagnostic cap-removal
attempt. Its first 600-step run failed: measured cap/can centre separation
never exceeded 86.998 mm, cap guide never released, and no spray was emitted.
This is a failed attempt, not a successful task demo. A working feedback
controller and nozzle/painting sequence remain outstanding. Draft run limit is 2,400 controls (120 seconds at
20 Hz); adjust to the demonstrated task before submission.

## Local checks

```sh
python3 -m unittest discover -s tasks/uncap-spray-panel -p 'test_*.py' -v
```

Fifteen tests cover capped/no-press states, detent release without removal,
wrong-facing and out-of-range spray, footprint coverage, hand occlusion,
overspray, finite supply, drop invalidation and final release/parking. Synthetic
states validate the rubric, not the robot's ability to reach these states.

## Related submissions

Read-only search of all 1,953 current upstream PRs on 2026-11-13 found no
direct uncap-and-spray-coat task. #1770 applies primer with a brush. Inhaler
priming #795 was finally rejected for non-robotic difficulty and an unspecified
product protocol. This task must demonstrate physical cap removal, actuator
use and spatial coating; changing the container alone is not novelty.
The task board itself required sign-in. Recheck novelty before submission.

## November 14 corrections in progress

The first failure used positive Waypoint finger targets even though the pinned
YAM uses negative metre values (-0.04695 open to 0 closed); those commands were
clipped fully closed. Corrected target signs and replaced simultaneous vertical
wrist access with a privileged feedback side-grasp controller using ordinary
14D actions. Cap-only run `spray-v2-cap-002` physically detached and parked the
cap, score 0.25 after 23.2 seconds. Full coating validation follows separately.

The revised orange can, dark cap and blue paint are distinct from the grey work
surface and white panel. The stand has two feet, uprights, diagonal braces,
crossbar and bolted-style mounting bars instead of a single support post.
Neither the can nor cap gains extra grip handles. Material/force calibration
and full gripper/arm spray occlusion remain approximations.

### Contact and controller changes

The can body uses a 3 mm torsional contact patch (minimum 1.5 mm), smaller than
its finger contact face, to represent finite pad twist resistance rather than
point contact that freely rolls under an off-centre nozzle press. This is an
explicit, uncalibrated contact approximation; no weld, pose lock, extra handle
or increased hardware effort limit holds the can. NVIDIA documents these
contact-patch parameters in the [PhysX collision schema](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.2/dev_guide/schemas/physxschema.html).

The privileged scripted controller calibrates its grasp from measured can and
hand poses, compensates bounded arm PD deflection and adjusts press height
using measured piston travel (2.7 mm target). It sends ordinary joint targets;
only the environment's geometric spray model writes accumulated surface dose.
The sparse aerosol points are a visual aid, not simulated fluid particles.
