# Draft judging

Use photos of both sides with a millimetre ruler. Count a tacking stitch as
removed only when its red thread is clear of both patches. A cut thread still
caught in either patch does not count. Any safe method of unpicking is allowed.

- Fewer than two released stitches: 0.
- Two or three: 0.25.
- Four or five: 0.5.
- All six removed, but the tool is still held or not safely put down: 0.75.
- All six removed, no remaining thread bridge, and the seam ripper released by
  the robot and resting on the table at least10 mm from either patch: 1.0.

The patches may remain in the fixture. Moving them apart is not required; all
thread fragments must be visibly clear of both patches in the final inspection.
The earlier draft required30 mm patch relocation; this was removed before any
scored demo because it adds a separate handling task rather than proving seam
removal. This change does not relax thread clearance, fabric-damage or native
validity checks.

A new cut or tear extending more than 2 mm beyond an original needle hole scores
zero at every level. Incomplete trials or missing final inspection also score
zero. In simulation, a blade crossing a cloth triangle conservatively invalidates
the trial; this is a development damage guard, not validated cloth fracture.

The `scoring.assess` function checks these supplied final measurements. It does
not infer that cutting six native joints released six stitches. `inspection.py`
provides a conservative geometric removal test for measured thread capsules and
cloth surfaces. Strain beyond the declared simulation envelope also invalidates
a trial. The preview defaults to 2%; an explicit 5% operating-domain option
retains independent 2% warning telemetry. Neither limit is a measured cotton
failure threshold or a substitute for inspecting both fabric surfaces.
Native damage telemetry and agreement with photo judgment remain to be validated
before submission.
