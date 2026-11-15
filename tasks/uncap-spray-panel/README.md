# Uncap a spray can and coat one circular plaque

This task now asks for one stationary coating position: remove and park the cap,
coat the fixed white circular plaque, release the button, and leave the can
upright on its pad with both hands clear. The prior four-zone panel task is
retired. Its failed trials and sources remain development evidence, not a
demonstration of this revised task. **A fresh capped-start full-score trial is
pending.** No Dream score, submission media, or completed demo is claimed.

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
- 1.00: above, can on its pad within 35 mm horizontally and 12 mm vertically,
  upright within 10°, speed below 20 mm/s, button travel below 0.5 mm, and both
  TCPs more than 70 mm from can/cap centres, continuously for one second.

Coverage samples a 10 mm grid: 52 cell centres lie inside the exact 40 mm
radius. A cell needs 0.08 effective centre-plume seconds. The plume retains its
12° half-angle, 120–300 mm scored range and 12-second supply. At least 2 mm
actual button travel emits paint after cap removal. Overspray includes emitted
flux missing the circle, backing, range, facing direction, or coarse occluders;
it cannot be erased by later paint. These thresholds are unchanged from the
retired task; only the target geometry and single-position scope changed.

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

The current CPU tests cover circular dose/layout, exactly one coating sequence,
calibrated grasp/return, physical release gates and captured color replay. Old
027 first-shot rays retrospectively cover this circle, but that is only a
feasibility diagnostic. It does not establish the revised task's native score.

A fresh full trial uses 960 Hz physics, 20 Hz control (48 physics steps/action),
baseline body solver settings, and the unchanged limit of 2400 actions/120 s:

```sh
/data/IsaacLab-Arena/.venv/bin/python tasks/uncap-spray-panel/run.py \
  --policy demo --stage full --physics-hz 960 --no-video \
  --max-steps 2400 --log-dir ~/yam-eval/spray-single-028
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
