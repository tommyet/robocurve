# Judging the knot

**Draft protocol. A complete robot demonstration and Dream run are still
required before submission.**

At the end of the robot's actions, inspect the cord from enough angles to
follow it from one coloured end to the other. Either handedness is allowed.
There must be exactly one overhand knot: one loop with an end passed through
it. A plain crossing, untucked loop, slipknot, figure-eight knot or tangle
does not qualify. Use the complete recording to resolve an obscured crossing;
do not infer a knot from its silhouette alone.

Every part of the robot must be at least 3 cm clear
of the cord. In a jig trial, every part of the cord must be at least 1 cm
clear of the pegs and their supports; the permanent
standing-end bench clamp is the only permitted attachment.

| Score | Requirement |
|---|---|
| 0 | No qualifying released overhand knot, damaged cord, or invalid simulation evidence. |
| 0.5 | A qualifying released knot exists when the robot finishes. |
| 1.0 | That knot remains tied and clear of the robot and jig throughout the load test below. |

Keep the yellow end in its permanent clamp. The evaluator pulls the red end
away from the yellow end, increasing the force from zero to 0.981 N over
2 seconds, then holding it for 5 seconds. Full-load tolerance is ±5%.
The evaluator must not tuck, rethread or otherwise repair the knot.
A genuine knot that comes undone during this test keeps its 0.5 pre-test
credit. An unfinished load test cannot earn full credit. Invalid physics or
missing evidence needed to establish the pre-test knot invalidates all credit.

A real-world check would use a ruler for clearance, a timer, and a spring
balance on the red end, aligned away from the fixed yellow end. A 100 g mass
weighs approximately 0.981 N, but hanging masses from both ends is not the
procedure for this clamped setup. The loading procedure has not been physically
validated; no physical trial has been performed for this draft.

## Automated audit

The scorer reconstructs every rigid capsule from its measured pose. It checks
continuity, self-contact, release and crossing order, rather than trusting the
controller's claimed score. Multiple views and exterior closures must agree
on a single overhand-knot certificate. Ambiguous geometry earns no credit.

The two-second seating and five-second proof intervals are recorded separately.
Topology is checked at every assessor frame. Actual simulator force-buffer
readback establishes the applied external load. The current numerical assay
also applies an equal opposite force to the fixed yellow link, reacted by its
clamp. It does not measure internal rope tension or apply twice the stated
free-end load. The last policy action is held during the assay; the policy
receives no additional observations or action calls.

Projected knot size, apparent crossing-envelope movement and inferred tail
lengths are diagnostics only. They depend on the projection and do not define
the physical outside of the knot. None is a scoring condition.

The preformed-knot diagnostic always scores zero, even when it survives the
load. It tests the simulator and cannot establish task feasibility.
