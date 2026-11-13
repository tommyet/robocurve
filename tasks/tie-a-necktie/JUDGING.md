# Proposed judging rubric

Use front and rear photographs, the tying video and a ruler. The collar form
has a marked centre. Measure tip length downward from the neck form's
lower edge at z=1.0875 m; the acceptable 280–320 mm band stays above the table. Inspect the knot's fabric path: the wide end must pass through the neck
loop and then the front wrap to form a retained four-in-hand. A loose drape,
preformed knot, attached strip or mere visual overlap does not count.

- **0:** no valid four-in-hand remains after both grippers release for five
  seconds, or cloth/contact integrity fails.
- **0.5:** a valid knot remains for five seconds but one or more dressing
  conditions below fail.
- **1:** the retained knot is within 15 mm of the marked collar centre; the
  neckband's greatest gap from the form is no more than 10 mm; the wide end's
  face points outward without an axial half-twist; the narrow end is behind the
  wide end with its tip at least 10 mm above the wide tip; and the wide tip lies
  280–320 mm below the marked collar edge.

With the wide tip pointing down, its front face shows the pale edge mark on
the viewer's left and the gold edge mark on the right. The reverse pattern is
the back face. Check the whole visible wide end for a half-twist; a correctly
oriented tip alone is insufficient.

The five-second hold must finish within the run limit. Pulling the knot apart
after achieving it loses credit. Any torn cloth, mesh crossing, secret grasp
attachment, vertex animation or unsupported tightening invalidates the result.
Unknown integrity must be reviewed before assigning a score. No centreline
topology measure or edge-strain threshold substitutes for the flat-fabric and
visible contact checks.

`scoring.score(record)` calculates credit from these reviewed observations and
requires hashes for the released video and front/rear photographs. The unit
test records are synthetic and cannot be used as task evidence.

Fit bands are provisional design values, not calibrated clothing measurements.
They must be checked against the chosen collar and tie and fixed before the
final demo/Dream pair. The current diagnostic has not produced a wearable knot.
