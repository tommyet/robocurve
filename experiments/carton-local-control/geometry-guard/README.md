# Isolated scoop guard CPU candidate

This directory contains a CPU-only optimization and replay report. It is **not**
installed in the frozen opening coupon or a task runner. It does not change
controller behavior, mechanics, scoring, collision thresholds, or intended pairs.

The frozen `baseline_safety.py` is the exact opening-coupon safety implementation
SHA256 `b10826b42913bdc326b76513788e352f6380a845d00ba4a95bc0c55ba8c750ba`.
The controller copied for provenance is
`5e845320e986f282d65b58b8227c5005f7cc98923b8f901778af67e8d21cb192`.
Neither frozen original was modified. Native 013 was intentionally cancelled at
30 simulated seconds before contact; it was not scored as a completed attempt.

## Measured cost and change

Baseline cProfile: nine representative ticks / eighteen actual-or-candidate
checks took 3.113 seconds under profiling. Guard checks consumed 99.4%; 85,050
piece/box scalar calls consumed 87.3%. IK consumed 0.017 seconds. The inter-arm
315-by-315 piece AABB test was already vectorized and was not the dominant cost.

`fast_safety.py` batches far-box extrema for **all 315 pieces against all 15
panel/cutter OBBs**, then uses the original SAT function for near pairs. It retains
the table test, row-major minimum-pair ordering, 0.3 mm narrowphase branch,
0.2 mm safety threshold, and narrow tip_right/north_bottom exception. Possible
minimum ties are refined with the original scalar calculation. An extra 1e-12 m
dispatch band adds scalar work rather than removing a pair or widening safety.

Only parked-arm FK/AABBs are cached. The key contains the exact float64 values of
all six right joints and both fingers. Fresh panel/cutter poses are rebuilt on
every call. Left actual/candidate geometry is rebuilt on every call.

## Evidence

`comparison-report.json` includes all 321 reviewed route poses, twelve deliberate
collision cases, in-place scene mutation and exact-value cache invalidation:
336 finite cases total. Clearance values matched exactly (maximum difference
0.0 m), as did decisions, intended scope and minimum-pair identifiers. Three
matched warm nine-tick batches measured median **2.826 s baseline / 0.990 s
candidate = 2.855x**. Initialization and asset I/O were excluded for both.
These are local CPU results, not native/GPU timing or general geometry proof.

That full run used candidate hash `1ef09fdfb430791f5621c620c5cfaa6a1cb457059f09797e99003dbda634da32`.
The only final delta preserves baseline behavior when a caller omits the target
panel. Six subsequent focused tests passed, including this case, in-place right
finger invalidation, fresh scene/cutter arrays, both sides of the 0.2/0.3 mm
thresholds, tied pairs and nonfinite input. Final candidate hash is
`64af6ff63e1646466a41e6183de7562e0d1ae2e8cd95026afaa93fbb666e4f5c`.
Astra independently reviewed this final delta and passed the same six tests;
approval applies to a future integration, not a GPU run.

```sh
cd /private/tmp/carton-scoop-guard-profile
PYTHONPATH=/private/tmp/spray-yam-source /private/tmp/robocurve-media-env/bin/python profile_baseline.py
PYTHONPATH=/private/tmp/spray-yam-source /private/tmp/robocurve-media-env/bin/python compare.py
/private/tmp/robocurve-media-env/bin/python -m unittest -v test_fast_safety.py
```

The copied scene/config/crease/capture/model files are import dependencies only.
`route321.json` and `snapshot-row.json` are pinned inputs; the route workload uses
the existing measured panel poses and reviewed hinge motion, not a live scene.

## Tracking diagnosis, separate from optimization

`tracking-recommendation.json` and `tracking_diagnosis.py` inspect the native 013
last-100-row data and hypothetical augmented-command geometry. They do not
implement a controller. Joint-command FK was about 55 micrometres from the
reference while the native arm lagged that command by about 2.1 mm. The median
joint-six residual was -8.35 mrad. A separate bounded proprioceptive feedback
test is warranted; no mechanical gain or progress threshold change is proposed.
The report distinguishes PRE-command/PRE-measurement from POST-measurement and
does not interpret absent sampled contact forces as all-substep contact proof.
All eleven sampled recent scenes retain at least 1.3989 mm hard clearance after
adding the median measured joint offset to the issued command. This does **not**
justify carrying that offset throughout the route: applying the same offset to
all 321 nominal poses makes one underedge-insert command overlap north_bottom
by 1.234 mm, while that flap is still a hard obstacle. The unchanged augmented
command guard must remain active; later transfer/contact needs its own review.

No active source, GPU, remote process, object pose, native force, or task scorer
was changed by this work. Further integration and native testing require the
coordinator's authorization and controller/geometry review.
