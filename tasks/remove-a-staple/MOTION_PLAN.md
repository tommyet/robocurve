# Proposed robot sequence

The current candidate uses one hand. The left arm stays at READY; the free
remover's 15 mm-wide heel supplies the opposing local contact on the sheets
while the forks lift the crown. This removes an optional distant hand brace,
not the paper or steel mechanics. All 386 nominal hull frames are clear. The
native extraction still needs demonstration. After pickup, an explicit scripted
servo may use the measured remover grasp to correct ordinary joint targets.

The earlier braced candidate below remains as a development record. Its slower
touchdown still stops at 89 actions with 171.59 µm positive panel aperture,
no native hinge-break notification and no steel crossing. That is a numerical
contact observation, not a demonstrated tear.

This is a planning note, not a demonstrated extraction. Full-size passive
panel-paper reset and short YAM integration pass. Actual bracing reaches 46
control actions; the next trial changes touchdown speed and records geometric
continuity and native break events.

1. Approach the remover and paper brace. Pause with the left fingertips 2 mm
   above the sheets, let the wrist level, then lower 2 mm over 1.5 seconds. The
   final nominal brace pose is unchanged.
2. Pick up the remover across its 18 mm handle width and lift it clear of the
   tabletop. Keep the papers held by ordinary left-finger contact.
3. Approach the staple from its right side, with the heel over the support
   and fork tips under the crown, inside both legs.
4. Insert at about 5.54° downward pitch, then pivot to level using contact
   with the support. Further rotation would drive the handle into the board.
5. Lift the held remover 12 mm. Both legs must unbend and leave their holes
   through physical contact. A floating stack or retained leg is not removal.
6. Keep the complete staple at least 10 mm clear of both sheets, put down and
   release the remover, then leave staple and papers released for 3.2 seconds.
   The staple may remain on the remover. Sheet separation is unnecessary.

The 446-action candidate lasts 22.3 seconds within the proposed 600-action limit.
Its first 30commands match the earlier 386-action plan; it adds a slower brace
and settling holds. All 446commanded hull frames pass the offline rejection
screen. Flexible contact and actual motor tracking require the native trial.

The next 144-action prefix ends after pickup and before tool alignment over
the staple. The later nominal poses pass inverse kinematics and geometry
screening, but physical grasp rotation may require a disclosed pose-assisted
scripted controller. Such feedback may issue only normal bounded robot joint
targets; it cannot edit object poses, forces, attachments or actuator limits.
Dream will receive ordinary camera and joint observations only.

Every native substep retains steel continuity and wire-crossing checks.
The next geometric paper diagnostic records positive empty aperture, finite
shared-edge overlap, raw endpoint errors and separate native break events.
A diagnostic recording is not automatically a valid task demonstration.
