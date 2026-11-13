# Draft judging

Use photos of both sides with a millimetre ruler. Count a tacking stitch as
removed only when its red thread is clear of both patches. A cut thread still
caught in either patch does not count. Any safe method of unpicking is allowed.

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
not infer that cutting six native joints released six stitches. `inspection.py`
provides a conservative geometric removal test for measured thread capsules and
cloth surfaces. Strain beyond the declared 2% simulation envelope also invalidates
a trial; this is not a claim that 2% is a measured cotton failure threshold.
Native damage telemetry and agreement with photo judgment remain to be validated
before submission.
