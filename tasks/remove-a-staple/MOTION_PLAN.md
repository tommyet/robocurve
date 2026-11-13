# Proposed robot sequence

This is a planning note, not a demo or a claim of feasibility. The nine right-arm
poses from `plan_reach.py` pass offline inverse kinematics. Contacts, collisions,
left-arm access and the complete sequence remain untested.

1. Pick up the remover by its polymer grip and lift it clear of the table.
2. Use the left fingertips to hold the papers flat beside the staple. They must
   touch the papers normally; no attachment or pose correction is allowed.
3. Approach the staple from its right side. This keeps the remover heel on the
   document support. The two fork tips align below the crown, inside its legs.
4. Insert with the tool pitched down about four degrees. Pivot to level against
   the support. Do not rotate past level: the handle would hit the support.
5. Lift the held remover about 12 mm, continuing to hold the sheets down. The
   staple legs must straighten and leave the original holes through contact.
   A bent crown, floating stack or still-threaded leg is not extraction.
6. Clear the remover and staple. Slide the top sheet away under gentle fingertip
   contact, then release both papers for three seconds. Thin-edge pinching is
   not assumed feasible merely because an inverse-kinematics target exists.

The current support is only 210 mm wide. A later geometry revision may extend
it along x so the top sheet can slide 250 mm to a final 40 mm edge gap without
falling over a sharp 20 mm step. That wider board is not part of the current
native settling test. Its dimensions, screenshot and reset would need updating
together if adopted.

Every substep keeps the paper strain and wire-crossing guards active. A stopped
trial remains invalid even if a later continuation could look successful.
