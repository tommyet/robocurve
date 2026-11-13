# Proposed robot sequence

The current candidate uses one hand. The left arm stays at READY; the free
remover's15mm-wide heel supplies opposing local contact while the forks lift
the crown. After pickup, a disclosed scripted servo uses the measured remover
grasp to correct ordinary bounded robot joint targets. It cannot change object
poses, forces, attachments, materials or actuator limits. Dream cannot use it.

The584-action candidate lasts29.2 seconds within the600-action limit. All584
nominal hull frames and584 frames corrected for the native114 pickup grasp pass
local IK/hull screening. This is planning evidence; complete physical extraction
is not demonstrated.

1. Pick up the remover across its18mm handle width and lift it clear.
2. Orient at6.651° downward pitch and approach with the heel6mm above the paper.
3. Pause1.5 seconds, lower to1mm above in2 seconds and pause1 second. Creep the
   final1mm over5 seconds, then settle for1 second. The lowest of all eight heel
   corners targets the upper paper surface; the fork fits below the crown.
4. Slide the fork under the crown and lever to level. Lift12mm so both legs
   straighten and leave both sheets through native contact.
5. Carry the complete staple at least10mm clear, set the remover on the table,
   release it and observe for3.2 seconds. The staple may rest on the remover.

`slow_heel_plan.py` replaces only the12-action final descent in the corrected
386-action plan. Its first118 commands and insertion/extraction/release suffix
remain bit-identical. The final1mm descent has0.375mm/s peak commanded speed;
materials, scene geometry and integrity checks are unchanged.

Native106 exposed a placement error: the tilted heel's lowest corner was below
the paper because the planner referenced its bottom-centre and bare support.
The corrected114 trial targets the upper sheet, but still stops at129 actions.
The151.46µm positive aperture alone is not a tear. Exact native solid checks show
that the tool overshot through both sheets, with34 transverse inter-sheet
triangle intersections, before insertion. Slower touchdown tests this dynamic
cause before adding a new fixture. It has not run yet.

Earlier braced plans stopped on local paper aperture while the spare hand
pressed the stack. They remain historical diagnostics. No bracing, extraction,
full-score or no-damage claim follows from those recordings.

Every native substep checks steel continuity and wire crossings. The paper
monitor records positive empty aperture, finite edge overlap, raw endpoint
errors and native break events separately. Diagnostic mode cannot automatically
certify a task score. Actual contact, complete extraction, paper preservation
and final released clearance must pass before this becomes a demo.
