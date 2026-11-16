# Seal a preloaded carton with an ordinary tape roll

The two cuboid products start inside the carton, and all four top flaps start 160 degrees open so both products are visible. The robot must close the flaps, then pull material from a normal loose packing-tape roll, press one connected strip along the seam and at least 35 mm down each end, cut it with the guarded cutter, then release the tools and leave the seal retained. The ordinary tape roll starts with 60 mm of its existing film already unwound. There are no pre-laid carton strips, software tape deposition or extra grasp handles.

This is a development task, not a completed demonstration. The earlier pickup/placement prefix is removed. Starting contents and already unwound material earn zero credit. Native preloaded/open-flap stability passed historically, but its closure probe failed. The revised open-flap/free-leader setup requires a fresh native check; no sealing success is claimed.

## Setup and approximation

Carton: 220 × 180 × 100 mm, 3 mm board, twelve rigid panels with crease joints. Contents: blue 80 × 50 × 30 mm, 100 g cuboid and orange 60 × 40 × 30 mm, 70 g cuboid, both on the two-layer bottom. The weak top-crease rest is 10 degrees open; joints are not locked shut. Tape roll: 48 mm width, 50 micrometre film, 100 mm outer diameter, 76.2 mm open core. The outer 360 mm is 72 finite rigid film cells; remaining wound supply is conserved analytically. The outermost 12 cells (60 mm) start in a straight tangential continuation from the last wound cell, without their wound-tack constraints. They remain joined by ordinary film hinges, have the same width/thickness/mass as every other film cell, and are not attached to the box or any fixture. This openly simplified starting condition removes initial end-peeling, but not flap closing, application, further payout, cutting or retention. Tool: ordinary 55 g guarded cutter on a pad. Sizes, fixed poses and colors are in config.py/task.py.

Adhesion requires measured contact pressure of at least 0.5 N for 100 ms, on the adhesive face within 0.5 mm. Native force-coupled bonds and blade crossings—not controller phases—supply coverage and cut measurements. These adhesive parameters are uncalibrated approximations, not a validated material model. Coarse rigid film/hinges replace thin-film deformation.

## Score

The two products must remain contained, the flaps closed within 5 degrees with inner flaps below outer flaps, and the tape connected and within its strain/capacity bounds. Initial placement or prepared free ribbon alone earns nothing.

- 0.25: at least 11 of 44 seam cells have at least 80% width bonded from one connected material component with at least 55 mm actual payout.
- 0.5: all 44 seam cells meet that coverage.
- 0.75: one blade-cut, detached strip supplies the complete seam and both 35 mm end wraps.
- 1.0: retain the complete seal with hands clear, tools parked and carton speed below 10 mm/s for 2 seconds.

Broken creases, drops, excess strain, nonfinite state or material-accounting violations invalidate the run. A nonzero score does not establish full completion.

## Validation commands

Use the pinned Isaac Python and a fresh output directory:

```sh
/data/IsaacLab-Arena/.venv/bin/python run.py --mode settle-probe --no-video --out /home/ubuntu/yam-eval/sealing-open-leader-settle-001
```

All default modes use the same open-flap/free-leader starting layout. `closure-probe` attempts only the flap-closing prefix; `roll-pickup-probe` attempts only acquisition/lift. `bench` and `adhesion-probe` use diagnostic loads/fixtures and cannot receive robot task credit. Camera-free runs capture the composed scene and actual native actor poses for clearly labelled offline previews. They do not provide RGB observations or a completed model run.

Full flap closure, further ordinary-roll peeling, application and cutting remain unproved. No full-score demo or Dream score is claimed.

Ordinary-roll checkpoint (not sealing; fresh output directory):

```sh
/data/IsaacLab-Arena/.venv/bin/python run.py --mode roll-pickup-probe --no-video --out /home/ubuntu/yam-eval/sealing-roll-pickup-001
```

Before this open/free-leader revision, the first native prefix timed out after 372 controls/18.6 simulated seconds, during closure of the fingers. One opposing-contact frame was observed; no lift, peel or seal was demonstrated. Its contact snapshot is pre-action, while actor poses are post-step; timestamps are retained. The force gate sums all 73 configured roll-family filters, so it does not depend on individual filter-column ordering, which is not independently read back. The checkpoint is explicitly unscored.

## Latest CPU-only closure check

The previous east-flap approach contacted the unrelated north flap before acquisition. The revised plain-rim point is 55 mm from the hinge instead of 40 mm. At both 160 and 175 degree open starts, 39 sampled ready/hover/entry/closure configurations pass full 315-piece arm and obstacle checks. The full fold arc is **not** clear: the north flap blocks the later carrier path. Runtime checks actual and issued configurations before stepping, allowing contact only between the selected flap and its active fingertips. This is a bounded acquisition/partial-fold candidate, not a completed flap-closing sequence or continuous clearance certificate.

Native open/leader follow-up: the two-second preloaded stability check scored0, with connected film and no unintended bonds/cuts. The robot attempt ended at8.6s: last applied action was the plain-rim pinch; the next east-fold command was rejected by the unrelated-object guard before stepping. No flap closure or sealing is demonstrated.

## Face-push controller development (2026-11-16)

The later native closure002 prefix also scored zero. Replaying its final measured
state identified a different obstruction: the issued intended fingertip/flap
proxy was already 0.966 mm deep, close to its unchanged 1 mm limit. Every next
fold candidate was rejected; the measured contact depth was only about
0.022 mm. This does not establish inadequate motor force.

A replacement strategy is being checked locally: open jaws straddle the lateral
rim, and one inner finger pad pushes the underside past vertical. The hand then
withdraws laterally while the flap falls closed. Full finite robot and obstacle
geometry is retained. Planning checks and gravity estimates are not a native
closure demonstration. Neither the old rim controller nor this development
establishes complete sealing.

The optional fast geometry certificates preserve the same pair-specific limits:
1 mm intended fingertip/flap depth, 0.2 mm unrelated-object clearance. A box-axis
separation can certify a passing pair; otherwise the complete original SAT is
computed. Reported fast gaps are conservative separation bounds, not exact
penetration measurements or contact force. The default geometry path is
unchanged.

Selected-flap force acquisition uses separate native singleton contact sensors,
with native filter/body binding and freshness checks. Family-wide force sums
remain diagnostic and cannot prove contact with the selected flap. CPU tests
cover the reader contracts; installed native binding and physical closure remain
unvalidated. The final released seal hold now credits only intervals whose two
measured endpoints both satisfy every finishing condition.

The face-push diagnostic can be limited to one released, parked flap:

```sh
/data/IsaacLab-Arena/.venv/bin/python run.py --mode closure-probe \
  --closure-controller face-push --closure-flaps 1 --max-steps 1400 \
  --no-video --out /home/ubuntu/yam-eval/sealing-face-prefix-001
```

This command is a candidate validation run, not previously demonstrated success.
The requested flap prefix finishing does not finish the packing task and earns
no seal credit. For local route planning, the complete four-flap prefix needs
roughly 220 simulated seconds before tracking delays. Its separate diagnostic
ceiling is 6,000 controls (300 seconds); the existing rim diagnostic keeps its
3,600-control ceiling. A short GPU allowance is insufficient to assume the full
prefix will finish. Bound wall time separately, including VM boot and shutdown.

Native attempt on2026-11-16: the existing VM never became SSH-ready, so the
face-push controller did not run. Early stop requests returned server errors;
shutdown was ultimately confirmed. There is no new native score, motion evidence
or video from that attempt. The93-task-test/5-experiment CPU results above remain
the current evidence; physical closure and sealing still need validation.
