# Judging the knot

**Evaluated in simulation: scripted demo 1.0; Dream-1 0.0. Not submitted.**

At the end of the robot's actions, follow the intact cord from one coloured
end to the other, checking each crossing from enough angles to see which
strand passes over it. There must be exactly one overhand knot: an end passed
through a loop, rather than a folded bight passed through it. Either
handedness is allowed. A plain crossing, untucked loop, slipknot, figure-eight
knot or tangle does not qualify. Use the complete recording to resolve hidden
crossings without moving or repairing the cord. A silhouette alone is
insufficient.

Measure clearance between surfaces. The entire cord must be at least 3 cm
from every robot part and at least 1 cm from every peg and support. The yellow
end remains in its permanent bench clamp; that is the only permitted attachment.

| Score | Requirement |
|---|---|
| 0 | No qualifying released overhand knot, damaged cord, or invalid simulation evidence. |
| 0.5 | A qualifying released knot exists when the robot finishes. |
| 1.0 | That knot remains tied and clear of the robot and jig throughout the load test below. |

Keep the yellow end in its permanent clamp. The evaluator pulls the red end
away from the yellow end along the line between the ends (within 10 degrees),
increasing the force linearly from zero to 0.981 N over 2 seconds, then holding
it for 5 seconds. Full-load tolerance is ±5%, or 0.93195–1.03005 N.
The evaluator must not tuck, rethread or otherwise repair the knot.
A knot that comes undone or loses the required clearance during this test
keeps its established 0.5 pre-test credit. An unfinished or out-of-tolerance
load test cannot earn full credit. Damaged cord, invalid physics or missing
evidence needed to establish the pre-test knot invalidates all credit.

A real-world check would use a ruler for clearance, a timer, and a spring
balance on the red end, aligned away from the fixed yellow end. No physical
trial has been performed. Surviving this
gentle pull does not establish a product load rating or a stopper-knot function.

## Automated audit

The scorer reconstructs every rigid capsule from its measured pose. It checks
continuity, self-contact, release and crossing order. An open cord's numerical
knot classification depends on how its ends are virtually joined. The scorer
requires agreement across several exterior closures and views, with the
qualifying crossings on the actual cord. This finite check reports an
`overhand_candidate`; ambiguous geometry earns no credit. It supports the
visual inspection and load test, rather than establishing physical validity
by itself.

The two-second seating and five-second proof intervals are recorded separately.
Topology is checked at every recorded assessor frame, at 20 Hz. Simulator
force-buffer readback records the applied external load; replay checks the
record's consistency, not its authenticity. The current numerical assay
also applies an equal opposite force to the fixed yellow link, reacted by its
clamp. It does not measure internal rope tension or apply twice the stated
free-end load. The last policy action is held during the assay; the policy
receives no additional observations or action calls.

Projected knot size, apparent crossing-envelope movement and inferred tail
lengths are diagnostics only. They depend on the projection and do not define
the physical outside of the knot. None is a scoring condition.

The preformed-knot diagnostic always scores zero, even when it survives the
load. It tests the simulator and cannot establish task feasibility.
