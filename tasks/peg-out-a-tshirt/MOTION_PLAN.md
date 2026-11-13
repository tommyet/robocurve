# Pegging development plan

This is an unfinished controller, not a successful hanging demonstration.
The robot uses ordinary joint and finger targets. A disclosed scripted demo
may read cloth and peg positions to plan those actions. Dream uses only its
normal camera and joint observations, with the identical scene and reset.
No controller writes cloth or prop poses, adds attachments or changes forces.

1. Settle the flexible two-layer shirt over the laundry support for five
   seconds. Both free spring pegs start clipped to the empty line. The regular
   2.5 mm cloth mesh passes the passive reset check.
2. Pinch the two exposed hem corners, pull clear of the support and lift.
   Coarser-mesh carry demonstrations worked, but the regular-mesh shirt has
   passed through a finger pad when one hand releases. The current short
   control tests 128 cloth solver iterations with the same finite pinch.
   A full sequence stops early if the hem plainly leaves the retaining hand.
3. Keep the shirt forward of the line. Use the free hand to squeeze a spare
   peg's handles, remove it from the line and turn its open jaws downward.
4. Carry the hem over the line, then lower the open peg over fabric and line.
   Align from the actual free-jaw poses. Permit ordinary handle release when
   the line lies within both jaws; a nominal 1.5 mm point-target tolerance is
   not a task requirement. Actual contact and retention still determine
   whether the clip worked.
5. Withdraw the peg hand, release the cloth hand and check the first clip.
   Then exchange roles: pick up the other free hem corner, open the spare peg
   and clip from above. The peg separation must be at least 180 mm. The
   mirrored second-peg fragment is only a planning aid; it needs the actual
   supported shirt state and a physical pickup.
6. Withdraw both hands. Record five seconds with the whole shirt at least
   20 mm clear of table and floor, supported only by the line and pegs.
   Judge jaw/line/fabric capture from close views and the released hold.

The first complete valid clip, second fastening and full-score demo remain
unproven. Dense native traces retain every cloth state so a line crossing or
finger tunneling cannot be mistaken for successful hanging. Only after a
complete physical demo should the same setup receive a Dream run.
