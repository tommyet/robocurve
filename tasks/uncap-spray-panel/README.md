# Uncap a spray can and coat one circular plaque

This task now asks for one stationary coating position: remove and park the cap,
coat the fixed white circular plaque, release the button, and finish with the
can upright and steady in the left gripper and the right hand clear. The user
explicitly selected this held finish after the earlier parking variant failed.
The prior four-zone and single-plaque parking trials remain development
evidence, not demonstrations of this revised endpoint. **Fresh capped-start
held-finish trial 029 reached native score 1.0 and passed independent trace
audit on 2026-11-15.** A completed video shows an explicitly labelled offline
exact recorded physics replay. No Dream run, media upload or PR was performed.

## Fixed setup

World metres; table z=0.7475. No object jitter. Configuration is in `config.py`.

| Object | Geometry and starting state |
|---|---|
| Can | Orange aluminium cylinder, 52 mm diameter, 140 mm overall height, 250 g. Starts upright at (0.26,0,0.8675), nozzle +x, on a 50 mm riser. |
| Cap | Hollow charcoal plastic friction cap, 60 mm diameter × 34 mm height, 18 g; initially seated. Compound 24-segment ring, approximately 3 mm wall and 2 mm lid. |
| Button | White plastic 18 mm diameter × 10 mm actuator, 3 g; native 3 mm prismatic travel, initially released. |
| Target | Fixed white circular plaque, 80 mm diameter × 2 mm thick, axis x. Front x=0.47; centre (y,z)=(-0.035,0.9525). No rigid-body dynamics. |
| Backing | Fixed grey 360 × 360 × 12 mm board, aligned with plaque centre. |
| Stand | Fixed steel frame behind the backing; two feet, uprights, braces, crossbar and mounts. |
| Pads | Blue cap pad at (0.34,-0.10); grey can pad/riser at (0.26,0), each pad 100 × 100 × 2 mm. |

The controller retains a separate transit can anchor (0.26,0,0.9105) and uses
one coating hold at (0.26,-0.035,0.8755). Changing plaque centre does not move
the transit twice. It uses privileged measured state and ordinary bounded
14-dimensional robot commands; it does not write object poses or paint doses.

## Scoring

End-state score; invalid telemetry or a can/cap drop more than 30 mm below the
table invalidates all credit.

- 0.25: cap removed at least 60 mm from its seated position and parked within
  45 mm horizontally and 12 mm vertically, with speed below 20 mm/s.
- 0.50: above, at least 50% plaque coverage and at most 15% cumulative overspray.
- 0.75: above, at least 90% plaque coverage.
- 1.00: above, can upright within 10°, speed below 20 mm/s, button travel below
  0.5 mm, and right TCP more than 70 mm from both can and cap, continuously for
  one second. The left `tip_left` and `tip_right` must each report at least
  0.1 N of native normal contact with the can, with opposing directions
  (normalized dot product at most -0.5). Bodies are resolved by unique names;
  missing, nonfinite or malformed contact data cannot establish this finish.
  This is contact presence, not a calibrated high grip-force threshold. No can
  pad position, left-hand clearance or off-support condition is required.

Coverage samples a 10 mm grid: 52 cell centres lie inside the exact 40 mm
radius. A cell needs 0.08 effective centre-plume seconds. The plume retains its
12° half-angle, 120–300 mm scored range and 12-second supply. At least 2 mm
actual button travel emits paint after cap removal. Overspray includes emitted
flux missing the circle, backing, range, facing direction, or coarse occluders;
it cannot be erased by later paint. The paint and cap thresholds are unchanged. The single circle and the held
endpoint are explicit task-definition revisions, not a rescore of old trials.

Appearance uses the same measured per-cell doses. Cell meshes partition white
plaque and grey backing at an inscribed 128-sided circle (under 13 micrometres
radial approximation error); scoring uses the exact radius at cell centres.
Recorded per-face color arrays preserve that boundary in offline replay.

## Fidelity

Native rigid colliders, guided cap detent (1800 N/m) and spring-return button
(2200 N/m, damping 1 N·s/m) approximate the mechanism. The can's finite torsional
contact patch is an uncalibrated finger-pad approximation. No material, mass,
actuator gain, force limit or grasp feature was changed for the scope revision.
Paint is geometric cone quadrature, not aerosol/fluid simulation. Cap/hand
sphere occlusion is coarse. Mist points and surface colors are appearance only.

## Reproduction and validation

Validated source commit: `b54d516`. Fresh `spray-held-029` reached score **1.0**
in **38.95 simulated seconds**, with 780 recorded rows (including the initial
sample), **100% coverage** and **5.24152% overspray**. It emitted paint for
0.95 s and maintained the approved finish for 1.05 s: cap parked, can upright
and steady with opposing measured left-finger contacts, button released and
right TCP clear. The final button travel was 0.0137 mm, can tilt 1.793° and
speed 1.441 mm/s; right TCP distances were 117.0 mm from the can and 242.6 mm
from the cap. Independent source-integrity/all-sample scorer replay passed,
bound to trace SHA-256
`724856a92bb31df854fd49403fdf10c83415855133be994331406b2ab5550997`.

Native task termination occurred during `coat_unpress_0`. The controller's
auxiliary 20 mm finger-face cleanup gate had not completed: its final measured
face clearance was 0.643 mm and it recorded zero passing cleanup frames.
The successful evidence establishes the user-approved held/nozzle-off endpoint;
it does not establish completion of that additional cleanup sequence or can
parking. Earlier failed parking trials retain their original outcomes.

Local evidence is in `/private/tmp/spray-held-029/` (`audit.json`,
`score-summary.json`, source snapshot and exact native pose/paint trace).
The completed preview is `artifacts/task-previews/spray-cap-off-and-coat-demo.mp4`:
780 H.264 frames at 20 Hz, 39.0 s, SHA-256
`25fbc85be01718f6065e9eb3b9e3ad38f8b35ff968303563502f454b17c45ba9`.
It is **offline exact recorded physics replay**, with actual native actor poses
and recorded paint colors, not native RTX camera footage. Its trace-bound
assembly record is
`artifacts/native-four-task-20261114/spray-held-029-completed-video.json`.
No task-board media ID or submission is claimed.

The current CPU tests cover circular dose/layout, exactly one coating sequence,
calibrated grasp retention, opposing-contact/right-clear finish gates, physical
button release and captured color replay. The policy never opens the left
gripper after coating; it retreats the right arm and holds the last issued
joint commands, with the original measured-grasp safety guard still active. Old
027 first-shot rays retrospectively cover this circle, but that is only a
feasibility diagnostic. The fresh 029 result above supplies the revised task's
native score; the older run was not rescored as held-finish success.

A fresh full trial uses 960 Hz physics, 20 Hz control (48 physics steps/action),
baseline body solver settings, and the unchanged limit of 2400 actions/120 s:

```sh
/data/IsaacLab-Arena/.venv/bin/python tasks/uncap-spray-panel/run.py \
  --policy demo --stage full --physics-hz 960 --no-video \
  --max-steps 2400 --log-dir ~/yam-eval/spray-held-029
```

`--no-video` is a state-only engineering run, with no native camera images or
eligible submission media. Exact native body/paint captures can be replayed
separately with an explicit offline-physics-replay label. `--contact-diagnostic`
is opt-in for unscored stages only and records raw native normal/friction
snapshots; it is disabled for the fresh full trial. No ordinary full run can
silently enable it.

```sh
PYTHONPATH=/private/tmp/spray-yam-source /private/tmp/robocurve-media-env/bin/python \
  -m unittest discover -s tasks/uncap-spray-panel -p 'test*.py'
/private/tmp/robocurve-usd-env/bin/python -m unittest discover \
  -s tasks/uncap-spray-panel -p test_replay_usd.py
```
