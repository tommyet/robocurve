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

The retaining ribbon has eight small native contact patches, each 10 x 5 x 1 mm,
attached only to nearby elastic vertices. They represent finger contact with
the thin ribbon. The ribbon plus patches still weighs 4 g; they do not attach
to the packet or prescribe a wrapping motion. Attachment separation over 5 mm
is an integrity failure. This extension has passed only a CPU geometry check
and still requires native validation.
