# Adult necktie development plan

This is an unfinished physical controller, not a successful demonstration.
The current scene uses a 1.45 m tie on a standalone folded collar. The target
is a simple (Oriental) knot, starting with the tie inside out. A complete knot,
wearable fit and released retention remain unproven.

A disclosed scripted demo may read native cloth positions to choose ordinary
bounded joint and finger actions. Dream receives only its normal camera and
joint observations, on the same scene and reset. No controller may reposition
cloth, add attachments, change material rest lengths or apply hidden forces.

1. Settle the untied collar drape for five seconds. Check both free ends and
   collar contact. The source-authored reset shape comes from recorded gravity
   settling; it contains no knot.
2. Lift the wide strand and physically transfer its tip to the other hand.
   The adult pickup is proven; the first handoff pushes the tip aside and
   lifts empty. Batch115 carries the held strip 70 mm forward and retains it.
   The released receiver uses a finger-axis approach and 10 mm pad bite.
   Rigid checks pass; predicted contact with the loose narrow tip requires
   native integrity review. Batch119 retains the transfer, but the released
   middle section folds through the wide strip. Batch126 instead raises the
   receiving tip while both hands retain the material, then opens the original
   pinch. It retains the tip through recovered action549, but residual wide
   self-crossing and transient pad penetration still invalidate the transfer.
   An empty pinch stops the original release.
3. Keep the receiving left hand on the wide tip if the transfer succeeds.
   The free right hand stabilizes the narrow end without pulling it taut. Reach
   and actual cloth contact must pass before the next stage.
4. Pass the wide end under the narrow end and back across its front. Keep a
   loose front opening using an ordinary finger or pinch. The robot must
   create and retain this wrap through contact; no loop is fixed in place.
5. Feed the wide tip upward through the neck loop, then downward through the
   front opening. Use a physical handoff if the wrist cannot clear a loop.
6. Pull the wide end through, dress the knot and slide it toward the collar
   while holding the narrow end. Leave the wide face outward and the narrow
   tip hidden behind it, at least 10 mm above the wide tip.
7. Withdraw both hands and record five seconds of released retention. Measure
   collar gap, knot centering, front-face orientation and both tip positions.

The proposed final wide-tip drop is 400–440 mm below the collar's lower edge
at z=1.20 m. This is a provisional fit target until a complete physical knot
is demonstrated. Prior child-tie experiments remain in `VALIDATION.json`;
they are not evidence for this adult task. Dream runs follow a full demo.

Batch115 confirms the forward carry with a retained 23 mm pinch and no sampled
self, fixture or deep robot intersections. Batch119's retained receiving pinch
is physical progress, but 66 transverse self-crossing pairs after original-hand
release invalidate its transfer integrity. The corrected126 sequence preserves
its approach, raises the receiving tip first, then opens and withdraws the
original hand. All 300 commanded continuation poses pass the rigid screen,
but native126 still has two transverse wide-strip pairs and transient 1.85 mm
pad penetration. The next route must keep the unsupported middle fold away
from the receiving fingertips and collar-side strand before release. No such
continuation is released. This is an unfinished transfer, not a knot or score.
