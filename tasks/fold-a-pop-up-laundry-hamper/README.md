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
