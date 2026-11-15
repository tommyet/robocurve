# Conditional NORTH continuation with SOUTH bottom185 — CPU only

**Result: the retained beam reaches NORTH -40 degrees, then every retained
next-step option at -35 degrees collides with the fixed SOUTH wall.** No complete
arc, interpolated whole-path certificate, physical SOUTH opening, retention,
LEFT body brace, box roll, or native/full-score feasibility is claimed.

This is the single condition authorized by Astra under root's CPU-strategy
delegation. SOUTH bottom is hypothetically rotated to185 degrees about its
actual hinge. SOUTH top and every other panel keep their measured cut011 poses,
under the same world-Y+90-degree whole-carton transform. The original frozen
planner/report and native coupon are unchanged. No live object pose was written.

`conditional185.py` inherits the pinned role-explicit planner/geometry:

- LEFT actual q to READY/open:44 joint samples plus reoriented endpoint.
- Revalidates all49 original retained prefixes, their pinned FK, both open and
  common-loaded jaws, full315/task/mutual geometry and prefix ancestry.
- Checks idle LEFT/task geometry at each angle; moving RIGHT versus LEFT is
  independently checked in both jaw states at every accepted candidate.
- SOUTH185 and NORTH panel/table OBB checks run at every candidate angle.
  Only each flap's directly connected hinge-wall pair is excluded from these
  panel checks; unconnected panels, actual knife and table remain present.
  Panel nonpenetration uses the existing10 micrometre numerical tolerance;
  robot hard clearance remains0.2 mm. No new contact exception is introduced.
- Continues from the revalidated -45-degree beam using the same width4,
  5-degree increments, headings+/-60, and neighbors0/+/-5/+/-10 degrees.
  Actual physical patch, raw pad polygons, one common gripper scalar and all315
  collision pieces retain their previous definitions and thresholds.

All49 source nodes revalidate. At -40 degrees the retained headings are
35,30,25,20 degrees. At -35 degrees all eight unique successors hit
`gripper/south`: headings10–40 have5.267–6.946 mm overlap; heading45 has
0.172095 mm overlap. This wall remains present and is structurally distinct
from the SOUTH bottom flap removed from that location by the condition.
Panel/table checks themselves pass there. These are desired-pose gripper
geometry rejections, so they occur before an unnecessary IK solve.

The bounded run used8 IK attempts,166 full315 certificates and18.51 seconds
execution wall time, below its2000/600/180 limits. It stopped at the concrete
next-angle blocker and did not expand the family. Three focused tests pass:
condition/hinge integrity; actual fixed-wall collision versus safe panel state;
and panel SAT overlap/separation. No native run or production edit occurred.

The result is conditional and beam-limited, not global infeasibility. Heading
twist still requires physical pad slip/torsional friction or a measured regrasp;
the kinematic patch is not represented as a rigid no-slip attachment. SOUTH185
has not been physically achieved or shown to remain there, and LEFTREADY does
not simultaneously supply a body brace or hold SOUTH.

```sh
cd /private/tmp/carton-opening-order185
/private/tmp/robocurve-media-env/bin/python conditional185.py
/private/tmp/robocurve-media-env/bin/python -m unittest -v test_conditional185.py
```

`conditional-report.json` records all prefix rechecks, new nodes, terminal pair
IDs, panel checks, exact condition and input hashes. `PROVENANCE.json` and
`MANIFEST.json` bind this isolated candidate. The copied planner/geometry remain
byte-identical to their prior reviewed versions. Further strategy/CPU/native
work needs a new Astra/root assignment; no next family is self-started.
