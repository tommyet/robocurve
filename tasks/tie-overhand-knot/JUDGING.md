# Judging the knot

**Draft protocol. A complete robot demonstration and Dream run are still
required before submission.**

At the end of the robot's actions, inspect the cord from enough angles to
follow it from one coloured end to the other. Either handedness is allowed.
There must be exactly one overhand knot: one loop with an end passed through
it. A plain crossing, untucked loop, slipknot, figure-eight knot or tangle
does not qualify. Use the complete recording to resolve an obscured crossing;
do not infer a knot from its silhouette alone.

Measure each free tail along the cord from the outside of the knot to its end.
Both must be at least 4 cm. Every part of the robot must be at least 3 cm clear
of the cord. In a jig trial, every part of the cord must be at least 1 cm
clear of the pegs and their supports; the permanent
standing-end bench clamp is the only permitted attachment.

| Score | Requirement |
|---|---|
| 0 | No qualifying released overhand knot, insufficient tail, damaged cord, or invalid simulation evidence. |
| 0.5 | A qualifying released knot exists when the robot finishes. |
| 1.0 | That knot remains tied, with both tails at least 4 cm, throughout the load test below. |

The evaluator gradually applies opposing 0.981 N endpoint loads over 2 seconds,
then holds the full load for 5 seconds. Full-load tolerance is ±5%. This is
approximately the force from a 100 g mass at each loaded end. The evaluator
must not tuck, rethread or otherwise repair the knot. A genuine knot that
comes undone during this test keeps its 0.5 pre-test credit. Invalid physics
or incomplete evidence invalidates the entire score.

A real-world check would use a ruler, timer and small weights or a spring
balance. The fixture and loading procedure must be validated against the
simulation before claiming physical equivalence; no physical trial has been
performed for this draft.

## Automated audit

The scorer reconstructs every rigid capsule from its measured pose. It checks
continuity, self-contact, release and crossing order, rather than trusting the
controller's claimed score. Multiple views and exterior closures must agree
on a single overhand-knot certificate. Ambiguous geometry earns no credit.

The two-second seating and five-second proof intervals are recorded separately.
Topology is checked at every assessor frame. Actual simulator force-buffer
readback establishes the applied load. The last policy action is held during
the assay; the policy receives no additional observations or action calls.

Projected knot size and apparent crossing-envelope movement are diagnostics
only. They are not reliable substitutes for ruler measurements of knot size
or material slipping through a knot.

The preformed-knot diagnostic always scores zero, even when it survives the
load. It tests the simulator and cannot establish task feasibility.
