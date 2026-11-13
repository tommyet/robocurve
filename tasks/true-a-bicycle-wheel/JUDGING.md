# Judging the wheel

This is a development rubric. The tolerances describe this fixture; they are
not a service recommendation for every bicycle wheel. The complete native
scene and robot demonstration still need to satisfy them.

After the robot finishes, keep both hands and its wrench clear. Spin the wheel
through one complete marked revolution in its stand. Use the stand's fixed
pointer and feeler gauges to measure peak-to-peak lateral and radial runout.
Compare the rim centre plane with the marked stand centre. Show the complete
revolution, not a selected arc. Inspect the rim, spokes, nipples and stand for
damage or extra support touching the rim during this final check. Holding the
rim with a robot hand while adjusting a nipple is ordinary task manipulation;
the hand must clear before the judged revolution.

Check each of the 32 spokes with a basic mechanical spoke tensiometer. Use its
conversion chart for round 2 mm steel wire; record all readings in newtons
(1 kgf = 9.80665 N). Each must be 400–1000 N. This prevents earning credit by
loosening the wheel until the rim looks straight. Missing readings, a missing
spoke or a damaged component fail the check. The tool is used by the assessor
after the robot stops; it does not help the robot true the wheel.

This replaces the draft's 32 hanging-weight/caliper measurements and eight rim
proof-load trials. A spring tensiometer is an ordinary bicycle repair tool;
[Park Tool's instructions](https://www.parktool.com/assets/doc/product/TM-1_instructions.pdf)
explain reading the scale and converting by spoke material and diameter. The
400–1000 N window is specified for this proposed small-wheel fixture, not taken
from that manufacturer's recommendations for other rims.

| Score | Requirement |
|---|---|
| 0 | Incomplete evidence, damage, direct rim bending, extra rim support during judging, any spoke outside 400–1000 N, radial runout over 1 mm, or dish error over 0.5 mm. |
| 0.5 | All checks pass and lateral peak-to-peak runout is at most 1.5 mm. |
| 1.0 | All checks pass and lateral peak-to-peak runout is at most 0.5 mm. |

A `wheel-judging-v2` record supplies the three millimetre measurements, 32 spoke
tensions and the reviewed boolean checks listed in `scoring.py`. Missing,
nonfinite or negative values fail closed. A simulation assessor may reproduce
the same observable quantities from measured geometry/material state, but a
hidden target nipple angle is never a scoring criterion.
