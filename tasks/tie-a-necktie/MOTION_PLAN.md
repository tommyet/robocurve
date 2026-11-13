# Four-in-hand development sequence

This is the planned robot sequence, not a successful demonstration. The only
permitted controls are ordinary YAM joint and finger targets. Native cloth
positions may be inspected between development runs; a submitted fixed script
must use a frozen trajectory, and any online correction must use the standard
camera/joint observation.

1. **Establish the reset.** Let the untied half-wrap settle under gravity. Check
   that both ends are uncrossed, no cloth intersects the collar or support, and
   the long end is on the intended side. Save the settled nodes as a reset
   asset with the source/physics provenance. Do not carry an in-progress knot
   across resets.
2. **Present the wide tip.** Grasp a hanging part of the wide end, lift it clear
   of the table, and transfer to a grasp near the tip with the other hand.
   Check the pale/gold edge orientation before wrapping. The collar's contact
   and friction support the remaining drape; there is no neck attachment.
3. **Make the front crossing.** Hold the narrow strand below the collar while
   passing the wide end across its front. The hands must retain a visible gap
   for the next wrap; closing the collar loop is not yet the goal.
4. **Wrap behind and around.** Carry the wide end behind the narrow strand and
   return it across the front. Maintain an open front wrap using a real finger
   as a spacer, then release that spacer only after the next handoff. No
   artificial loop is authored or held open by the simulator.
5. **Feed through the neck loop.** Bring the wide tip upward from behind the
   crossing and through the space between the neckband and front knot. A
   handoff lets the receiving gripper take the protruding tip without passing
   its wrist through a loop too small for the real gripper.
6. **Feed through the front wrap.** Pass the wide tip downward through the
   actual front opening. Use the opposite hand to hold the wrap. Confirm the
   passage from both normal wrist views before tightening.
7. **Dress and tighten.** Pull the wide end while holding the knot; then draw
   the knot upward on the narrow end until it sits at the collar. Keep the wide
   face outward and the narrow end behind it. Tightening must be caused by
   these physical pulls, not by editing material rest lengths or applying
   unexplained tension.
8. **Release and judge.** Open both grippers and withdraw. Record the required
   five seconds of unsupported retention within the action limit, front/back
   views, the maximum neck gap, knot-centre offset and both tip positions.
   The narrow tip must finish at least 10 mm above the wide tip.

The first paid checks are the small collar-drape/free-fall contrast and a
single physical grasp-and-release. A failed contact check is fixed before
attempting the full wrap. Freeze a full demo only after a complete physical
trajectory succeeds; run Dream on that identical scene afterward.

[TieBot's original project](https://tiebots.github.io/) confirms that fabric-tie
manipulation is a substantial robotics problem, not a reliable consequence of
having a cloth simulator. Its teacher/student/residual-learning pipeline does
not supply a ready YAM policy or validate our contact model.

## Length budget

The explicitly child-sized tie is 1.10 m long. A 110 mm diameter neckband
uses approximately 346 mm; allowing about 200 mm of extra four-in-hand take-up beyond the hanging
paths leaves
554 mm for the hanging ends, for example a 304 mm wide end and a 250 mm
narrow end. This is additional material use, not the total length inside the knot: for
example a 30 mm high knot containing about 264 mm of material adds about
204 mm beyond the two hanging paths. These are planning estimates; the
recorded final fit remains mandatory. The initial half-wrap uses a 65 mm centreline radius
and 204 mm of material, leaving a 580 mm wide end and a 316 mm narrow end.
The longer wide end supplies the front crossing and knot wraps.

A 1.40 m adult tie was incompatible with the short form's 280–320 mm final
drop: the same rough budget would leave 854 mm for two ends, more than two
320 mm drops can accommodate. The shorter tie is an explicit prop choice,
not hidden slack or relaxed narrow-end judging.
