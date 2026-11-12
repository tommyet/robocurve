# Draft judging

Use photos of both sides with a millimetre ruler. Count only stitches that no
longer join the two patches at the end; a cut thread still caught through both
patches is not a released stitch. Any safe method of unpicking is allowed.

- Fewer than two released stitches: 0.
- Two or three: 0.25.
- Four or five: 0.5.
- All six, but incomplete separation: 0.75.
- All six, both patches separated edge-to-edge by at least 30 mm, no thread bridge,
  and the tool released clear: 1.0.

A new cut or tear extending more than 2 mm beyond an original needle hole scores
zero at every level. Incomplete trials or missing final inspection also score
zero. In simulation, a blade crossing a cloth triangle conservatively invalidates
the trial; this is a development damage guard, not validated cloth fracture.

The `scoring.assess` function checks these supplied final measurements. It does
not infer that cutting six native joints released six stitches. Final inspection,
cloth damage telemetry and agreement with simple photo judgment remain to be
implemented and validated before submission.
