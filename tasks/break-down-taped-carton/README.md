# Cut the bottom tape, unfold the flaps and flatten a used carton

Engineering draft. Twelve local checks pass, including hinge-anchor geometry
and scorer outcomes. There is no native physics rollout, robot demo, Dream
score or video yet. The exported carton is not a validated working scene.

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
