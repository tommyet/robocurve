# Cut the bottom tape, unfold the flaps and flatten a used carton

Native mechanics/controller draft. Thirteen local checks pass, including hinge-anchor geometry and scorer outcomes. A native free-carton stability probe passes, but no full cutting/unfolding/flattening robot demo or Dream score exists.

Start with an **empty used carton**, upright with its four top flaps open and
its four bottom flaps closed and taped. Turn it over, use a guarded cutter to
cut the long bottom seam and the tape across both end folds, park the cutter,
unfold **all four bottom flaps**, then collapse the four-wall tube and leave
the complete carton flat on the table. The carton has no grasp handles.
This is a recycling task after contents have been removed, not another item
retrieval submission. It requires the bottom preparation absent from #1858.

## Geometry and mechanics

Carton: 220 × 180 × 100 mm, 3 mm corrugated board, four 35 g side panels and
eight 18 g flaps. Short flaps are inset one board thickness to fit beneath the
long pair. Four vertical crease hinges form a free closed loop; eight flap
hinges retain every flap. The box is not fixed to the table. `scene.py` exports
this geometry as native USD rigid bodies and revolute joints. Layout tests
check that both local anchors of every hinge coincide initially.

Packing tape is 48 mm wide, across the full bottom seam with 40 mm tails down
both end walls. Three cut paths are sampled at 2 mm resolution. A held blade
must sweep each cell within 1.1 mm, with valid depth/orientation and sampled
motion below 15 mm per control step. Merely positioning the cutter at the end
of the seam earns nothing. The sealed outer bottom flaps may not be forced
past 12 degrees. Future runtime releases native hinge limits only after every
path is cut; it must never set flap poses to simulate opening.

The bottom cutter and initial marked parking pad will reuse the guarded
tool from the validated unboxing task, but its geometry/controller have not
yet been integrated into this draft. Carton placement and safe turnover need
robot reach and self-collision checks before the setup is frozen.

## Proposed score

- 0.25: every seam/end-fold cell cut validly.
- 0.50: all four bottom flaps physically opened to at least 150 degrees.
- 1.00: all eight flaps remain at least 150 degrees open, every cardboard
  vertex lies within a 24 mm horizontal slab resting on the table (minimum
  height −2 to +8 mm, maximum height 30 mm), carton speed below 10 mm/s,
  cutter parked and hands clear for one second.

Any crease separation over 4 mm, forced sealed outer flap, nonfinite state,
missing control samples or carton drop more than 30 mm below the tabletop
invalidates the trial. Breaking panels off cannot earn credit. Final pose
orientation and choice of collapse direction are unrestricted.

The 24 mm slab is a provisional engineering tolerance for multiple 3 mm
layers, not demonstrated feasibility. Numeric limits must be checked against
native contacts and a real carton before submission. Proposed allowance is
3,600 control steps at 20 Hz; set the final limit from a successful demo.

## Checks and remaining work

```sh
python3 -m unittest discover -s tasks/break-down-taped-carton -p 'test_*.py' -v
# In the pinned Isaac environment, export only (does not prove physics):
python scene.py /tmp/recycling-carton.usda
```

Next: native closed-loop stability, finite-thickness folding/corner clearance,
free-carton turnover, cutter contacts and live pose readback, tape rendering
and fracture coupling, a physical four-flap opening demo, collapse/release
tests, then a matching Dream trial. `scoring.py` currently accepts a measured
state schema; there is no robot adapter supplying those measurements yet.
No controller can set these scoring inputs directly in the eventual runtime.

## Native development probes

```bash
/data/IsaacLab-Arena/.venv/bin/python run.py --mode dynamics --out /path/to/new-probe
/data/IsaacLab-Arena/.venv/bin/python run.py --mode grip-probe --out /path/to/new-attempt
```

The carton has twelve genuinely free rigid panels and twelve physical creases.
The stability probe kept crease errors below 0.06 mm. The first robot grip
attempt remained intact but failed to lift: its fingers met the outward top
flaps before reaching the rims. Top flaps now allow a real fold-back motion to
270 degrees with a 3 mm finite crease offset outside the wall. A geometric
regression checks that the folded flap clears the outer wall; the next native
grasp test still has to establish that this fixes access.

Probe forces and `--unsealed` starting conditions are explicitly diagnostic,
with no task score. A completed task still requires robot turnover, measured
blade cuts, four bottom flaps physically opened, intact collapse and released
flatness. Every probe freezes its sources; `error.json` invalidates it even if
Kit returns exit code 0. See `VALIDATION.json` for recorded limitations.

Scoring clarification: the robot must first open all four bottom flaps through
at least150 degrees after cutting all three tape paths. This is recorded from
measured hinge angles. During subsequent flattening, the flaps return to a
wall-coplanar90/270-degree fold; requiring150-degree angles at the flat finish
would physically contradict the24mm total-cardboard slab criterion. Final
credit requires every flap within15 degrees of its wall plane, all cardboard
vertices within the slab, intact creases, parked cutter and released hands.

## Feedback cutter and flap diagnostics

The cutter controller retains the ordinary seven-second pickup prefix, then
calibrates the measured TCP/tool transform after checking native cutter height,
finger opening and hand distance. Cutting uses the rotated TCP-to-blade offset:
turning the tool also changes the required TCP translation. Separate staging,
orientation, hover, lowering, cutting and lifting phases advance only when the
actual blade follows the current command and settles at the endpoint. Tool
travel pauses above 6 mm tracking error or 0.07 rad orientation error. Elapsed
time can cause an explicit failure; it cannot advance the cut to the next path.
The scorer still counts only actual native blade sweeps.

In the earlier cut005 trace the timed seam started while the blade was still
162 mm from its start; at 20 s it remained 129 mm behind the moving target.
The same trace later reached 0.23 mm error on the front fold. A CPU FK check
also found the old diagonal seam hover intrinsically unreachable by about
25 mm. The revised seam uses the opposite tool direction, keeping the TCP on
the reachable side, and a 20 mm blade clearance rather than that high hover.
These observations diagnose tracking/endpoint problems; they do not establish
whether native inter-arm or carton collisions occurred. That trace omitted the
actual arm joints needed to reconstruct all robot collision meshes.

The flap gripper basis puts its Y axis along the edge and its X closing axis
across it. Approach and entry now require actual pose alignment; pinching needs
a measured 2.3–15 mm finger gap at the edge. Rotation must produce at least
5 degrees of actual flap movement and keep the acquired TCP/flap offset;
measured slipping or stalled motion fails the diagnostic. No grasp weld,
object-pose write or automatic flap opening is used.

Every new trace records normalized fourteen-dimensional actions, native arm and
finger joints, and FK TCP positions/rotations for both arms. Cutter reports
include actual/commanded/endpoint blade positions, orientation error and path
progress. The cut probe has at most 3,600 controls (180 s), stopping early on
controller failure or completion of its cutting/parking attempt. Completion of
this probe is not a full carton-breakdown demonstration.

Twenty-three CPU tests pass with NumPy available:

```bash
/private/tmp/robocurve-media-env/bin/python -m unittest discover -s tasks/break-down-taped-carton -p 'test_*.py' -v
python3 -m compileall -q tasks/break-down-taped-carton
```

An ideal attached-tool FK dry run reached every revised cutting/parking phase
in 63.8 simulated seconds without an IK failure. It assumes perfect joint
tracking and rigid tool retention and includes no contacts; it is not native
physics evidence. Native grip retention, blade alignment under load, inter-arm
clearance and all four physical flap grasps remain to be tested.
