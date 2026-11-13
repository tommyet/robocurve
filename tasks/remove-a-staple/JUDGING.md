# Judging staple removal

The development reset is two aligned 80 gsm office-paper sheets, 210 × 148 mm,
with one ordinary clinched steel staple near a corner. Its crown midpoint is
12 mm inside each nearest edge, as fixed in `setup.json`. Photograph both faces
of both sheets with a millimetre ruler before assembly. The four original hole
boundaries must be recorded after stapling and before the trial. The nominal
props/layout are fixed; their measured physical match remains unvalidated.

After the trial, inspect the whole of both sheets from both sides. A new tear
extending more than 2 mm from an original staple-hole boundary gives zero.
Any new puncture, cut or tear elsewhere also gives zero. Do not discount a cut
because it is hidden under the original staple or on the back of the paper.

Count a leg as clear only when its entire bent tail has passed out of both
sheets. A crown lifted off the paper, a partly withdrawn leg, or a torn sheet
slipped off an embedded leg does not satisfy that condition.

| Score | Requirement |
|---|---|
| 0 | Neither leg is fully clear, damaged paper beyond the stated tolerance, broken staple, altered sheets or invalid/incomplete evidence. |
| 0.5 | At least one complete leg is clear of both sheets and all preservation checks pass. |
| 1.0 | Both legs are fully clear, every part of the intact staple is at least 10 mm from either sheet, and the staple and papers remain released for three seconds. |

Measure the shortest metal-to-paper clearance in the final state with a ruler
and overhead/side photographs. Include both bent tails, not just the crown.
The three-second release interval starts when neither robot hand touches the
staple or papers. The intact staple may rest in or on the remover, provided
the robot has released that remover onto the work surface. An actively held
remover supporting the staple does not satisfy release. The sheets may stay in their original
stack; no separate paper-transport action is required. Wrinkles and creases
alone are not tears.

Judge the final state, not an earlier successful frame. The staple need not be
straight or neatly placed in a tray. Both tool-assisted methods and successful
direct manipulation are valid; the result and preservation matter. Score from
continuous trial video, after-trial photographs and a ruler. The scorer's
boolean observations are review fields, not automatic claims by the simulator.
The record schema is `staple-judging-v4`. Record `staple_touching_remover` and
`remover_released` explicitly; release of an unused remover elsewhere is irrelevant.

The 2 mm damage allowance and proposed 30-second run limit remain development
choices. Check their suitability with the selected real paper and remover.
