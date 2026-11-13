# Proposed robot sequence

This is a planning note, not a demo or a claim of feasibility. The nine corrected right-arm
poses from `plan_reach.py` pass offline inverse kinematics. The current 236-action
lever plan also passes every-action sampled hull screening against the robot,
tool and support, with the left brace at (0.405, 0.050) m. Flexible paper and
wire contacts remain native-test requirements. This is not a successful grasp
or extraction. The full-size panel reset currently fails before robot actions.

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
6. Leave the complete staple at least10mm clear of both sheets, then release
   the tool and papers for three seconds. Both legs must be present and clear
   of the original holes. Moving or separating the sheets is unnecessary.

Every substep keeps the selected material's continuity and wire-crossing guards
active. A stopped trial remains invalid even if a later continuation could look
successful. The panel candidate uses finite native hinge strength; the older
surface-FEM path has separate membrane validity limits.

A separate `finalize_plan.py` appends ordinary remover placement, release and
3.2 seconds of final observation. The resulting candidate has 386 actions
(19.3 seconds) within a proposed 600-action/30-second limit. It can leave the
intact staple on the released remover, at least10mm from the paper, as allowed
by judging v4. The old236-action lever plan remains available for the first
contact test; neither plan is a completed native extraction demonstration.
