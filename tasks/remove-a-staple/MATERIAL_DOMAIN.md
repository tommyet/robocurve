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
and whether steel crosses intact paper triangles. The legacy 25 µm paper
endpoint-gap guard is a numerical model boundary, **not a tear detector**.
A small constraint error must be interpreted against the 100 µm panel thickness,
the direction of the displacement and actual contact. Averaging vertices must
never conceal a genuine broken connection or allow a staple through intact
paper. The task's visible damage rule remains a tear extending more than 2 mm
from an original hole, or any new cut or puncture elsewhere.

The full reset passes a passive PGS control at 500µs and a short YAM control.
Actual bracing reaches 46 actions. The 128-iteration comparison still stops on
29.57 µm raw error. A separate 100 µm observation diagnostic stops five native
steps later, at 167.41 µm. Its largest raw mismatch is mostly compression and
slip. Across every shared edge, maximum positive opening is 120.69 µm; normal
disagreement remains within the physical paper thickness and shared edges
still overlap. No wire crossing occurs. These are contact observations, not
proof that the papers tore or that removal succeeded.

The next diagnostic measures **empty aperture**: positive in-plane opening
combined with any normal separation beyond the two panel half-thicknesses.
Every shared edge must retain finite projected overlap. Its 150 µm aperture
bound is half the 300 µm steel-wire thickness; it conservatively screens gaps
that might compromise steel contact. It is not a new tear-size rubric.
Compression, tangential slip and raw endpoint distances remain telemetry.
Native finite-strength joint-break notifications are recorded separately,
including construction, reset and episode events. No notification alone
certifies undamaged paper. The runner marks this mode diagnostic-only and the
assessor will not certify a task score from it.

The next motion pauses 2 mm above the sheets and lowers those final 2 mm over
1.5 seconds. This addresses the observed finger touchdown while the wrist was
still levelling; it changes no material, motor effort or final brace pose.
Complete extraction remains unproven.

Earlier FEM and triangular-facet diagnostics remain preserved in `evidence/`.
Their 0.3% elastic-domain and 1% strain stops were diagnostic boundaries, not
paper-rupture measurements. Later FEM controls let steel cross intact triangles
even below 0.6% membrane strain; increasing the strain allowance could not fix
that contact defect. Those models are not the active panel-paper candidate.
