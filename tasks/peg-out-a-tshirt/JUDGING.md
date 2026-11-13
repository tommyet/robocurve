# Proposed judging rubric

Use the final five seconds of video and close-up photographs of each jaw. A
ruler or printed scale supplies distances. Inspect the actual hem captured
between each peg's jaws together with the line; a peg nearby, closed in air or
resting on top of the fabric does not count.

- **0:** no valid retained fastening; the robot, laundry support or another object supports the
  shirt; any part is within 20 mm of the table or floor; or integrity fails.
- **0.5:** one valid peg retains the shirt, supported only by the line and pegs for five
  seconds, with at least 20 mm clearance. Two valid pegs less than 180 mm apart
  receive the same partial credit.
- **1:** both pegs capture the line and separate portions of the bottom hem,
  their centres are at least 180 mm apart, and the shirt remains supported only by
  the line and pegs with at least 20 mm clearance for five seconds.

All score levels require an intact shirt, line and pegs. Torn cloth, broken
pegs, hidden attachment, cloth passing through itself or another collider, and
any unsupported geometry manipulation invalidate the run. If damage or contact
integrity cannot be assessed, leave the result unscored until reviewed. A
native strain diagnostic alone cannot certify the absence of tears.

The run ends at its declared action limit; earlier temporary success does not
override a dropped shirt. The hold must occur within the limit. Judge the
outcome rather than an arm-by-arm procedure: either arm and any physically
valid order of operations may be used.

`scoring.score(record)` consumes the reviewed values. Its evidence digest map
must include the released video and both jaw photographs. Synthetic records in
unit tests are test fixtures only. None is a demonstration result.

These thresholds are design choices. Fix and validate them before final media.
