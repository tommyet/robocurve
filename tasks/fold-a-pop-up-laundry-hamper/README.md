# Twist-fold a pop-up laundry hamper and secure it

**Unsubmitted development draft. No full-score fold or retaining-band demonstration exists.**

The current prototype uses native elastic surfaces for the four aggregated spring frames, sewn flexible mesh and retaining band. This replaces the coarse joint model that failed in diagnostic077. Material parameters are approximate and have not been calibrated to a retail hamper. No rest shape changes during a trial.

The intended outcome remains a packet no larger than220x220x60 mm, retained by its elastic band for3 seconds after release. `make_plan.py` currently authors a folding probe only; it does not yet place the retaining band.

Use the pinned Isaac/YAM environment:

```sh
python tasks/fold-a-pop-up-laundry-hamper/run.py --mode hold --steps 40 --out /tmp/hamper-reset
```

Original procedural geometry, MIT license. The original failed model is recoverable from shared main commit9bc7f6e. Final documentation, native demo, Dream baseline, rescoring and media remain outstanding.

## Development commands

From the repository root in the pinned environment, use a new output folder:

```sh
python tasks/fold-a-pop-up-laundry-hamper/run.py --mode demo --out /tmp/fold-a-pop-up-laundry-hamper-demo
python tasks/fold-a-pop-up-laundry-hamper/rescore.py /tmp/fold-a-pop-up-laundry-hamper-demo
```

The deterministic layout has no jitter or random seed. Source files and native
state are saved with each run. Rescoring verifies their hashes and re-evaluates
the recorded states on CPU. Diagnostics with `--capture-every` greater than1
are not submission recordings. Dream must use the same final scene and hardware.

Pinches use a disclosed native no-slip approximation once material is between closing finger faces. Each constraint starts at the measured pose, releases on opening, and breaks at 18 N or 0.36 Nm. Material deformation and collisions remain native; no object is teleported. Native validation is pending.

The 300 mm retaining loop has a 5 x 1 mm elastic section and weighs 4 g.
A native vertex pinch starts only when material is enclosed by the closing
fingers. It releases on opening, 8 mm slip or estimated 6 N tension; that
estimate is uncalibrated. Only incident contact triangles are filtered while
held. The robot still has to stretch the loop around the packet.

The reset requires the untwisted frame to span at least 30 x 48 cm, with less
than 10 cm vertical sag. A collapsed or pre-folded reset cannot be a trial.
## Validation status

Not submission-ready. The latest native diagnostic (`hamper-full-030`) stopped
at control 623 when the right frame grip slipped. The material remained intact
and the partial score was 0.25. A compact packet secured by the retaining loop,
a completed full-score demo and a Dream baseline remain unvalidated.

Current grip diagnostic: loss is detected when the binding leaves the actual pad faces (including the native2mm contact margin), not merely after8mm motion from the capture point. The18N/0.36Nm force/torque limits remain. This permits bounded tangential slip while contact remains; it never extends the pad or changes frame/cloth poses. The change still needs a complete native demonstration.

Clearance diagnostic041 uses80 ×26 ×2mm rigid finger extensions with silicone faces, ending207mm from the gripper origin and a195mm working point. Native geometry and planning use the same dimensions; the finite pinch still requires the central24mm contact region and retains18N/0.36Nm limits. This keeps the wrist clear of the folding loops; it does not prescribe a folded shape.

Diagnostic042 retains the long fingers and tests a30N finite frame pinch (within the40N per-finger actuator limit), with0.36Nm torque and the same actual-contact release gate. The18N diagnostic slipped sideways at action697; no material or scoring threshold changes. The friction estimate is uncalibrated.

Current draft reset: both hands already hold the opposite bound ends of the full 33 × 53 cm flattened, uncoiled hamper. Real opposing pad contact is checked before frame zero. The timer starts before lifting or twisting; no folded shape or loop placement is supplied. This removes pickup from the measured skill while retaining the complete twist-fold, loop stacking, securing and released retention test. Both arms use 50 mm risers and 100 mm steel finger extensions. The first 140 trajectory entries describe the pre-held reset and are excluded from timed execution.
