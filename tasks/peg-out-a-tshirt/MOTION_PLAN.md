# Pegging development sequence

This is a controller plan, not a successful demonstration. The robot may use
ordinary joint and finger commands. An explicitly disclosed scripted feasibility demo may use measured reset
cloth state to plan these actions. Dream remains camera/joint only, with the
identical scene and reset. No controller may write cloth/prop poses or forces.

1. Let the loose garment settle over the laundry support. Confirm the hem is
   exposed, the cloth clears the support solids and the starting state is at
   rest. Both freely moving pegs start clipped to the empty line, with handles down.
2. Approach the two exposed hem corners from in front, close vertically across both fabric layers,
   pull the fabric away from the support, then lift. The current 21-second
   grasp/release diagnostic tests only this contact stage; it is not a hanging
   demonstration. The selected 8 mm support uses 480 Hz physics. The five-second YAM reset
   and all 420 sampled approach poses pass their geometric audits; the first
   physical grasp/lift has now succeeded in batches016 and020.
3. Lift the garment high enough to clear the board and carry the hem toward
   the line. Keep one corner supported while positioning the first fastening
   site; do not rely on an invented cloth-to-hand attachment.
4. With one arm retaining the garment, the other approaches the handles of a spare peg already on the line.
   Squeezing the handles must open the two real jaws through their hinge.
   Feed the fabric into the open mouth beside the line, then release the handles
   so the passive spring closes the peg. Hand clearance and retained fabric
   must be visible; merely moving a closed peg nearby earns no credit.
5. Release the first cloth grasp only after the physical first peg supports
   it. Use the freed hand to present the opposite hem corner, while the other
   hand operates the second peg. Finish with at least 180 mm between pegs.
6. Open both grippers and withdraw. Record five seconds with the whole shirt
   at least 20 mm clear of the table/floor, supported only by the line and pegs.
   Judge actual jaw/line/fabric capture from close views and the released hold.

The small passive-clamp and open-clamp controls precede this sequence. If the
pegs cannot retain native fabric, fix their physical model before attempting a
full robot episode. Convenient physical peg rests may expose the handles, but
must be listed in the setup and cannot fixture the peg to the world during
robot use. No successful peg manipulation or full hanging trajectory exists yet.


Current continuation plan (2026-11-13): the state-assisted reset grasp in054
retained the garment through its full carry. The peg missed the line and fell;
cloth crossings after that failure invalidate the run. The058 candidate uses
measured free-jaw poses only to guide ordinary robot actions before closure.
It aborts if mouth alignment is worse than1.5mm. Neither state-assisted step
writes cloth, body or force state, and neither is available to Dream.

For the second fastening, exchange arm roles: the right hand picks up a free
edge of the already supported garment and presents it toward y=-0.115m. The
left hand approaches the spare peg from below, squeezes its handles, withdraws
it, turns it in free space and clips from above. The mirrored920-action
fragment has passed IK/speed checks; it is not a whole episode and remains
blocked until the first clip, actual second cloth pickup and its contact path
are demonstrated. Allow about200actions for that pickup, giving roughly
2240actions for the complete first/second fastening and final released hold.
