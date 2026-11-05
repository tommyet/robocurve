# Judging: Join two 2×2 blocks

Use the complete trial video, a ruler or calipers, a protractor, and paused frames. Follow
the same physical brick through the trial. Red must finish above blue.
All four lower studs must be inserted.

At full seating, the horizontal body centres coincide and every lower stud is covered.



| Score | Observable requirement |
|---|---|
| 0 | No qualifying pickup, or either brick leaves the permitted table area. |
| 0.25 | The robot holds red with its lowest point at least 20 mm above the table for 0.20 s. |
| 0.5 | After pickup, red is seated on blue in the required configuration for 0.20 s. |
| 1 | After seating, hold red only with blue's lowest point at least 20 mm above the table for 1 s; then leave the joined pair upright and released on the table for 1 s. |

Seated means the required 4 stud/socket centre matches are within 1 mm
laterally and 0.75 mm vertically of full insertion. The undersides of red's body
and the top of blue's body meet at full insertion; stud height does not add an
extra gap between the bodies. Their upward axes differ by at most 3°. Two 2×2
pieces also align their edges within 3°, allowing quarter-turn symmetry. A
single round stud permits arbitrary yaw where the physical bodies fit.

For a manual check, infer the stud centres from the supplied part drawings and
the visible body edges; the socket interiors need not be visible. Measure the
two horizontal offsets in a top view and the body-to-body gap in a side view.
The combined lateral mismatch of each required pair must be at most 1 mm,
not 1 mm independently on each axis. Use elapsed video timestamps for each
hold, and views where the table, both bricks and both grippers remain visible.
An oblique image alone cannot resolve hidden gaps or submillimetre seating.

During the lift proof, every part of both arms must be at least 2 mm clear of
blue. Blue must retain the required pose relative to red for the whole second.
Supporting blue directly, gripping both bricks, or balancing a loose stack does
not establish retention. The robot must actually hold red: the automated check
requires both named finger envelopes to lie within 1 mm of red's body, with the
holding TCP within 35 mm. Robot-link envelopes are conservative bounds derived
from all collision meshes, not point estimates at the fingertips.

At the finish, blue's bottom is within 3 mm of the table and its up axis within
3° of vertical. Both arms are at least 5 mm clear of both bricks. Each brick's
position remains within 2 mm and full orientation within 5° of its pose at the
start of a continuous one-second rest interval. Drifting outside these limits
restarts the interval. Small harmless movement inside the limits is allowed.

The permitted region contains the entire brick, including studs: X from
−0.17 to 0.89 m, Y from −0.63 to 0.63 m. A brick's lowest point more than 15 mm
below the table also invalidates the trial. Falling off or leaving these bounds
makes the final score zero. The rigid-body simulation has no destructible parts.

Judge the state at the end. A failed attempt may be retried within 1,200 actions.
Pickup credit survives a normal failed joining attempt. Separation or the wrong
final configuration removes connection credit and resets the lift proof. Correct
seating without the proof earns 0.5. A valid lift without a released stable finish
also earns 0.5. No historical maximum is substituted for the final score.

The audit samples every 50 ms. Durations use timestamps, not frame counts alone.
Missing intervals longer than 75 ms reset active timing windows; malformed,
nonfinite or non-increasing evidence invalidates the automated score. For replay,
use the source archived with the trial. The passive rulers help interpretation;
perspective is not a universal millimetre scale away from their planes.
