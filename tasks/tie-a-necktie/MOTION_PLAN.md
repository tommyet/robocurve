# Four-in-hand development sequence

This is the planned robot sequence, not a successful demonstration. The only
permitted controls are ordinary YAM joint and finger targets. Native cloth
positions may be inspected between development runs; a submitted fixed script
must use a frozen trajectory, and any online correction must use the standard
camera/joint observation.

1. **Establish the reset.** Let the untied half-wrap settle under gravity. Check
   that both ends are uncrossed, no cloth intersects the collar or support, and
   the long end is on the intended side. Use the shared fixed five-second
   native reset procedure for every policy; a later reviewed settled-node asset
   may replace it only with recorded source/physics provenance. Do not carry
   an in-progress knot across resets.
2. **Present the wide tip.** Grasp a hanging part of the wide end, lift it clear
   of the table, and transfer to a grasp near the tip with the other hand.
   Check the pale/gold edge orientation before wrapping. The collar's contact
   and friction support the remaining drape; there is no neck attachment.
3. **Make the front crossing and stabilize.** Pass the wide end across the
   freely hanging narrow strand, then grasp the narrow strand about 40 mm
   above its tip without pulling it away from its current position. Leaving
   it free throughout the rear pass swept it along and unwound the attempted
   wrap. An earlier pulled-narrow-end trial over-tensioned the strip. The
   collar drape must remain supported by ordinary friction and gravity.
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

## Historical child-tie length budget

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

A 1.40 m adult tie was incompatible with the old short form's 280–320 mm final
drop: the same rough budget would leave 854 mm for two ends, more than two
320 mm drops can accommodate. The shorter tie is an explicit prop choice,
not hidden slack or relaxed narrow-end judging.

## Simpler knot candidate

The user's objective permits another normal wearable knot. The
[simple/Oriental technique](https://www.ties.com/how-to-tie-a-tie/simple) begins
inside out, passes the wide end under the narrow end, then across its front,
up through the neck loop and down through the front loop. This removes one
initial crossing from the four-in-hand route; it does not remove threading or
tightening.

The historical child-layout CPU candidate parks the wide hand high, stabilizes the narrow tip and
routes the wide end at 1.12 m height. Its 1,200 commanded poses pass the
fixture/opposite-arm rejection screen. The optional inside-out reset reverses
the material width direction before physics; it has no crossing or knot and
passes the same initial triangle-clearance and strain tests. Both still need
native validation. Those historical child trials have not been relabeled as adult evidence.

After any retained wrap, the next physical milestones are: hold the front
opening with an ordinary pinch near the junction; raise the wide tip through
the neck loop; feed that tip down the front opening to a receiving hand; pull
through and adjust the knot on the narrow tail. The large grippers may require
a handoff. No part of the front opening will be fixed or animated.

## Current adult candidate

The current draft uses a 1.45 m tie and standalone collar centred at z=1.25 m.
The lower reference edge is z=1.20 m; a proposed 400–440 mm wide-tip drop leaves
12.5–52.5 mm above the table. Fit and narrow-tip ordering still need a complete
physical knot; these dimensions are design targets, not demonstrated success.
The simple-knot route starts inside-out and removes the extra four-in-hand
crossing. The preserved native070 pickup is followed by a measured physical
wide-tip handoff, then narrow-strand stabilization and actual loop threading.
