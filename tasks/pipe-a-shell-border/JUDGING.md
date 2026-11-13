# Draft judging

Use a top photo, a low side photo and a millimetre ruler. Judge the finished icing,
not the nozzle path or the number of squeezes. A full-score native robot demonstration exists. Final close-up photo agreement
and the Dream baseline remain pending.

The marked section is 90 mm long. Its permitted strip extends 9 mm on either
side and 2 mm beyond each end mark. A shell has a head 6–16 mm wide and 2.5–8 mm
high. Within 4–22 mm after that head, its tail must include a section 1 mm or more
wide, at least 0.5 mm high, at most 3 mm high, and no wider or higher than 65% of
the head. Its leading edge to qualifying tail must span at least 1.25 times its head width;
a round mound does not count. A finer point beyond this section is allowed. Head-to-tail motion can vary; shells have no fixed
centres, but distinct heads must be at least 6 mm apart. A low shoulder below
the minimum head height is part of a tail, not another head. Oversized or
over-height mounds remain obstructions; a shell cannot use a tail beyond them. For full credit, each counted shell needs at least two ridges at least
1 mm high, separated by 1.5 mm or more, with a dip of at least 0.3 mm between
them. Both ridges must continue for at least 2 mm on the shell, including its
tapered shoulder; an isolated bump does not count. Top and close side photographs
show their length, separation and depth. Measure head height within 2 mm before
to 4 mm after its widest point, where width is at least 75% of the maximum.

Measure the total marked length occupied by valid head-and-tail shapes:

- Below 20 mm: 0.
- At least 20 mm: 0.25.
- At least 40 mm: 0.5.
- At least 60 mm: 0.75.
- At least 80 mm, at least five valid ridged shells, no gap over 2 mm, and the
  dispenser released clear of the border: 1.0. For the final second, the
  dispenser must remain at least 5 mm from every robot part and 20 mm from
  the decorated strip, moving no more than 2 mm.

Score zero if the trial is incomplete, the metal tool gouges more than 1 mm into
the cake, or visible icing at least 0.5 mm thick covers over 20 mm² outside the
permitted strip. Lost material outside the recorded scene makes evidence
incomplete. Unmodeled robot/icing interpenetration also invalidates evidence.
The simple footprint test replaces an earlier, unsuitable spilled-volume rule.

`scoring.py` computes a draft analogue from the final surface. It finds actual
peaks and tapered tails rather than requiring six exact bins. It defaults to
incomplete evidence and cannot certify completion from a material file alone.
Negative shape controls and native surface replay pass. Exact ridge dimensions
still need comparison with the final close-up photographs. A repeated
row of smooth blobs, a plain line or a drawn texture is not a shell border.
