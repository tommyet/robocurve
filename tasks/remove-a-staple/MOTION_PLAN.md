# Proposed robot sequence

This is a planning note, not a demo or a claim of feasibility. The nine corrected right-arm
poses from `plan_reach.py` pass offline inverse kinematics. The current 236-action
lever plan also passes every-action sampled hull screening against the robot,
tool and support, with the left brace at (0.405, 0.050) m. Flexible paper and
wire contacts remain native-test requirements. This is not a successful grasp
or extraction, and the final sheet slide is not yet planned.

1. Pick up the remover across its 18 mm grip width and lift it clear of the
   table. The gripper closes across the handle, not against its two ends.
2. Use the left fingertips to hold the papers flat beside the staple. They must
   touch the papers normally; no attachment or pose correction is allowed.
3. Approach the staple from its right side. This keeps the remover heel on the
   document support. The two fork tips align below the crown, inside its legs.
4. Insert with the tool pitched down about 5.54 degrees. Pivot to level against
   the support. Do not rotate past level: the handle would hit the support.
   This angle comes from the 50 µm tip, heel geometry and fixed crown height.
   The old four-degree sketch put the tips about 1 mm above the crown.
5. Lift the held remover about 12 mm, continuing to hold the sheets down. The
   staple legs must straighten and leave the original holes through contact.
   A bent crown, floating stack or still-threaded leg is not extraction.
6. Clear the remover and staple. Slide the top sheet away under gentle fingertip
   contact, then release both papers for three seconds. Thin-edge pinching is
   not assumed feasible merely because an inverse-kinematics target exists.

The final slide needs at least30 mm of additional relative movement beyond
the initial12 mm sheet stagger. The sheets can still overlap; shifting the
whole stack together earns no separation credit. This avoids an unrelated
full-sheet transport while demonstrating that the fastener no longer joins them.

Every substep keeps the paper strain and wire-crossing guards active. A stopped
trial remains invalid even if a later continuation could look successful.
