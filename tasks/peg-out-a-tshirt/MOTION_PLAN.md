# Pegging development plan

This is an unfinished controller, not a successful hanging demonstration.
The robot uses ordinary joint and finger targets. A disclosed scripted demo
may read cloth and peg positions to plan those actions. Dream uses only its
normal camera and joint observations, with the identical scene and reset.
No controller writes cloth or prop poses, adds attachments or changes forces.

1. Settle the flexible two-layer shirt over the laundry support for five
   seconds. Both free spring pegs start clipped to the empty line. The regular
   2.5 mm mesh preserves the sewn edges' actual rest bends. Matched YAM
   control121 additionally uses once-per-step force integration: eight reset
   samples have no transverse self-crossings and the final rigid-fixture
   check is clear. Earlier YAM113 and118 resets are invalid and cannot
   support a task-success claim.
2. Pinch the two exposed hem corners, pull clear of the support and lift.
   Diagnostic125 explicitly raises the support from 100 to 180 mm and uses
   a measured lateral entry, with ordinary 0.018 finger targets. Its actual
   settled shirt must pass self-contact and fixture checks before any motion;
   all commanded grasp poses receive a rigid-hull screen. It finishes 320
   actions with clean sampled integrity but misses the pickup. The left
   target lies in the pad notch and the right hem moves aside during entry.
   A local candidate re-observes action100 cloth and targets continuous pads
   8 mm off the notch. Its commanded rigid and sampled cloth checks pass;
   it is not wired or native tested. Earlier093 retained pickup had an invalid
   reset. No valid pickup on the current setting has been demonstrated.
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
   supported shirt state and a physical pickup. Its complete 980-action route
   includes the measured peg alignment and final hold. A candidate episode
   budget is 1,180 actions through the first release, 150 for the second cloth
   pickup, about 60 to join the continuation and 980 for the second clip:
   2,370 actions in total. Reach, cloth tension and physical retention may
   require changes; this is not a validated full sequence.
6. Withdraw both hands. Record five seconds with the whole shirt at least
   20 mm clear of table and floor, supported only by the line and pegs.
   Judge jaw/line/fabric capture from close views and the released hold.

The first complete valid clip, second fastening and full-score demo remain
unproven. Dense native traces retain every cloth state so a line crossing or
finger tunneling cannot be mistaken for successful hanging. Only after a
complete physical demo should the same setup receive a Dream run.
