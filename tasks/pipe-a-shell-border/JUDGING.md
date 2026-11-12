# Draft judging

Use a top photo, a low side photo and a millimetre ruler. Judge the finished icing,
not the nozzle path or the number of squeezes. Numerical thresholds still need a
real reference decoration and a full robot demonstration.

The marked section is 90 mm long. Its permitted strip extends 9 mm on either
side and 2 mm beyond each end mark. A shell has a head 6–16 mm wide and 2.5–8 mm
high, followed by a tail at least 0.5 mm high, no wider than 65% of its head and
no higher than 65% of its head. Head-to-tail motion can vary; shells have no fixed
centres. Fine ridges from the star tip must be visible for full credit.

Measure the total marked length occupied by valid head-and-tail shapes:

- Below 20 mm: 0.
- At least 20 mm: 0.25.
- At least 40 mm: 0.5.
- At least 60 mm: 0.75.
- At least 80 mm, at least five valid ridged shells, no gap over 2 mm, and the
  dispenser released clear of the border: 1.0.

Score zero if the trial is incomplete, the metal tool gouges more than 1 mm into
the cake, or visible icing at least 0.5 mm thick covers over 20 mm² outside the
permitted strip. Lost material outside the recorded scene makes evidence
incomplete. Unmodeled robot/icing interpenetration also invalidates evidence.
The simple footprint test replaces an earlier, unsuitable spilled-volume rule.

`scoring.py` computes a draft analogue from the final surface. It finds actual
peaks and tapered tails rather than requiring six exact bins. It defaults to
incomplete evidence and cannot certify completion from a material file alone.
Its ridge extraction and photo agreement have not been validated. A repeated
row of smooth blobs, a plain line or a drawn texture is not a shell border.
