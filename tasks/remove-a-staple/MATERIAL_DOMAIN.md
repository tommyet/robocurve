# Paper model and its limits

The current candidate uses two flexible sheets of native 100 µm box panels.
Passive edge hinges provide bending compliance and finite breaking strength;
no sheet is a single rigid body or attached to the table. Analytic boxes avoid
the native convex cooker thickening the earlier triangular prisms. Explicit
punctures and all external steel contacts remain active.

The bending rigidity is `E h³ / (12(1−ν²))`, with E=2 GPa and ν=0.3. Panels
are internally inextensible and bending is elastic: permanent creases and
anisotropic fibre mechanics are simplified. A crease alone is not a tear and
does not fail the judging rubric.

Hinge strength is 1500 N per metre of shared edge. One laboratory study of
78.7 gsm, 102 µm copy paper reports directional tensile indices of 57.43 and
19.31 kNm/kg; the weaker direction gives about 1520 N/m. The chosen isotropic
strength is a disclosed engineering approximation, not a calibration of crack
growth around a staple puncture.
[Copy-paper characterization](https://crimsonpublishers.com/acsr/fulltext/ACSR.000566.php)

Every native substep checks panel continuity, complete steel-chain continuity
and whether steel crosses intact paper triangles. The current 25 µm paper
endpoint-gap guard is a numerical model boundary, **not a tear detector**.
A small constraint error must be interpreted against the 100 µm panel thickness,
the direction of the displacement and actual contact. Averaging vertices must
never conceal a genuine broken connection or allow a staple through intact
paper. The task's visible damage rule remains a tear extending more than 2 mm
from an original hole, or any new cut or puncture elsewhere.

The full reset passes a passive PGS control at 500 µs and a short YAM control
with about 4–6 µm endpoint disagreement. The first extraction attempt reaches
45 actions, then the upper-sheet residual reaches 29.73 µm as the left hand
braces it. Steel continuity and crossing checks remain clean. This does not
establish a tear or a valid complete task; a higher-iteration comparison with
endpoint-vector telemetry is pending. No successful extraction has been claimed.

Earlier FEM and triangular-facet diagnostics remain preserved in `evidence/`.
Their 0.3% elastic-domain and 1% strain stops were diagnostic boundaries, not
paper-rupture measurements. Later FEM controls let steel cross intact triangles
even below 0.6% membrane strain; increasing the strain allowance could not fix
that contact defect. Those models are not the active panel-paper candidate.
