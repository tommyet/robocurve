# Finite adaptive-heading opening screen — CPU only

Result: **no surviving next-angle node at -40 degrees in the retained finite
beam**. The best sampled prefix reaches -45 degrees from the actual initial
-78.5576 degrees. This is not a global impossibility result or an opening demo.
No candidate reaches 185 degrees, and no whole-arc interpolation is certified.

The search followed `adaptive-heading-plan.json` without adding a pose family:
candidate31, hypothetical rigid carton world-Y +90-degree transform, RIGHT
span+55 mm, normal sign -1, initial heading0. Only north_bottom rotates about
its actual hinge; all twelve initial panel poses come from native cut011. The
parked cutter remains at its actual pose. The carton reorientation itself is
unproved and was not executed or written into any live scene.

## Results

- LEFT actual cut011 q to first allowed READY target: 44 samples with joint
  increments <=1 degree, plus the reoriented endpoint, all315 collision pieces,
  all twelve panels/three cutter boxes/table and actual parked RIGHT. Pass;
  minimum hard clearance1.3989 mm (fixed base/table), mutual272.65 mm.
  The alternative raised target was not needed or searched.
- Physical patch: span+55 mm and2.5 mm inboard of the free edge, with
  `TCP = patch - R @ [0,0,.0105]`. Heading changes move TCP to preserve that same
  patch. Both full finger meshes are tested open at3 mm/jaw and loaded at the
  common first-contact opening, without independent finger controls.
- At heading0, first-contact openings are1.468924/1.468283 mm. Common opening
  1.468603 mm gives signed target gaps -0.315/+0.322 micrometres. Real inward-pad
  contact unions have areas3.528/5.377 mm², tangential spans14.653 mm, and actual
  depths1.646/1.648 mm. Their finite polygons are >=2 mm inboard of the edge.
  These are geometry proxies, not native force/friction/grip evidence.
- Astra clarified that2 mm means **setback into the board**, not a2 mm-deep
  contact rectangle. The preliminary stricter interpretation is preserved in
  `initial-rectangle-interpretation-report.json`; the search uses the clarified
  criterion and reports real polygons/areas without inventing a rectangle.
- Beam width4, angle steps5 degrees, heading neighbors0/+/-5/+/-10 degrees,
  headings bounded +/-60 degrees. It retained coarse nodes through -45 degrees;
  best heading sequence0,10,20,30,30,30,40,40 degrees.
- At -40 degrees, headings15–35 collide with gripper/south_bottom (about
  1.0–3.55 mm overlap). Headings40/45/50 collide with RIGHT link4/south_top
  (2.148/10.179/18.932 mm overlap). Other-arm separation is positive. Exact
  rejected q/TCP/R and pair IDs are in `failure-poses.json`.
- Search:58 IK attempts,151 full315 certificates,77.68 seconds execution wall
  time. Postvalidation checks idle LEFT against every retained node's current
  panel geometry and open/loaded RIGHT:49 nodes/98 checks, all pass. Reproducing
  the three existing failed poses adds3 IK/3 full checks. Combined:61 IK,
  252 full checks, about81.1 seconds execution, below2000/300/180-second caps.
  No extra angles, seeds or branch family were added by postvalidation.

## Geometry and provenance

`geometry.py` reuses the reviewed batched far-OBB reductions and original scalar
SAT fallback, with explicit LEFT/RIGHT bases. It retains every315-piece/task
pair and tests all315-by-315 other-arm pairs. Negative AABB warnings are refined
with the same facet/edge convex SAT as Astra's existing refinement. Exceptions
are only the two active finger links against north_bottom; palms, other panels,
table, knife and the other arm remain hard obstacles at0.2 mm. Loaded target
penetration must remain within the unchanged10 micrometre numerical tolerance.

Pad contact uses actual inward STL facets near the central pad rather than a
TCP/foretip witness. Polygon union uses a piecewise-linear scanline arrangement
so overlapping convex pieces do not double-count area or fill holes. The inward
facet filter is a0.995 normal-direction cosine and TCP-pad Z>=8 mm, recorded in
the code for review. Contact first stops use bisection over0..3 mm/jaw. No pad
compliance, load magnitude, friction coefficient or native contact is inferred.

Six focused tests pass: patch/TCP continuity math; only target-flap pose changes;
local jaw shifts versus pinned URDF FK; real opposing/common-scalar polygons;
LEFT/RIGHT base roles and all315x15 pair counts; polygon overlap and hole area.
All reported accepted nodes are checked by pinned FK/IK and native URDF limits.
They are coarse sampled poses, not continuous servo or swept-motion proof.

The final `planner.py` differs from the executed search only by storing a
fractional heading as float in the **unreached** densification branch. The exact
executed source is preserved as `executed-planner.py` and hash-bound by the
original report. No search was rerun after that recording-only fix.

Heading twist at a fixed board patch is not a rigid no-slip grasp transform.
It would require controlled pad slip/torsional friction or a measured regrasp.
The prefix's cumulative/max heading changes40/10 degrees are reported only as
kinematics. No loaded native opening should assume free twist. No body support,
box-roll trajectory, RIGHT acquisition path or completed opening is proved.

## Reproduce

```sh
cd /private/tmp/carton-adaptive-opening
/private/tmp/robocurve-media-env/bin/python -m unittest -v test_planner_geometry.py
/private/tmp/robocurve-media-env/bin/python planner.py
/private/tmp/robocurve-media-env/bin/python validate_retained_left.py
```

The code reads the pinned local YAM and frozen coupon/guard sources. It writes
only local CPU reports. No native/GPU process, physics, task source, scoring,
or production/frozen controller was changed. `MANIFEST.json` and
`PROVENANCE.json` bind all inputs/results. Additional planning or native work
requires coordinator authorization and review.
