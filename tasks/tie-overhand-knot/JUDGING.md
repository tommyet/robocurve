# Judging the knot

**V4 protocol; new feasibility evidence is still required.**

Start with the intact 131 cm outside-length, 10 mm cord in the flat, uncrossed
U shown in the setup. Nothing holds either end. The robot gets 150 seconds,
including the final five-second release check. There is no evaluator pull.

Follow the cord from one coloured end to the other and resolve every crossing
from the recording. Exactly one overhand knot is required: an end passes
through a loop. Either handedness is allowed. A bight tucked through a loop,
plain crossing, slipknot, figure-eight knot or tangle does not qualify. Use
additional views if needed; a silhouette alone is insufficient. Do not move,
tighten or repair the knot while judging it.

| Score | Requirement |
|---|---|
| 0 | No qualifying final released knot, damaged cord or invalid simulation evidence. |
| 0.5 | One intact overhand remains for the final five continuous seconds, with all cord surfaces at least 3 cm from every robot part. |
| 1.0 | The same knot also previously remained intact for one continuous second with its outer tips at least 117 cm apart and every cord surface at least 1 cm above the tabletop. It then passes the five-second release check. |

Use a ruler or calibrated images to measure the straight-line distance between
the outer coloured tips and the minimum surface clearances. Use the video
clock for durations. Table contact after release is allowed. Regrasping resets
the five-second release interval. Untying the knot cancels its earlier span
qualification; a new knot must qualify again. Ambiguous crossings cannot
establish a continuous qualifying interval. Score the final outcome, not the
best earlier frame.

The span target is a geometric definition: outside cord length minus fourteen
cord diameters. It bounds slack in the whole cord without guessing where the
knot begins or ends. It does not measure tension, strength or maximal
compactness. The robot may use any valid strategy; the scripted demo is
intended to pull the two ends simultaneously with both arms.

## Numerical audit

`bimanual_scoring.py` reconstructs the capsules from measured poses. The outer
tips include their hemispherical caps. To avoid credit from accumulated joint
gaps, the numerical span is reduced by the sum of all joint gaps; an intact
physical cord has no such correction. Joint gaps over 2 mm, actual centreline
intersections, or nonlocal penetration exceeding 5% of diameter invalidate the
recording. Robot clearance uses complete collision-link envelopes.

`topology.py` checks several exterior closures and views, with qualifying
crossings on the actual cord. The finite certificate is conservative; it is
not a substitute for reviewing the video or the physics. Qualifying span and
release intervals are checked at every recorded 20 Hz frame. Missing frames,
preformed starting knots, a crossed starting layout, fixtures or declared
external-force phases cannot establish this task. Source and recording review
must also confirm that no hidden attachments or forces were introduced.

Full credit requires clean recording finalization. The scorer cannot
authenticate logs or establish what happened between physics samples. No real
cord trial has yet been performed.
