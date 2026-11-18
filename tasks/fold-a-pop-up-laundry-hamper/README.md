# Twist-fold a pop-up laundry hamper and secure it

**Unsubmitted development draft. No full-score fold or retaining-band demonstration exists.**

The current prototype uses native elastic surfaces for the four aggregated spring frames, sewn flexible mesh and retaining band. This replaces the coarse joint model that failed in diagnostic077. Material parameters are approximate and have not been calibrated to a retail hamper. No rest shape changes during a trial.

The intended outcome remains a packet no larger than220x220x60 mm, retained by its elastic band for3 seconds after release. `make_plan.py` currently authors a folding probe only; it does not yet place the retaining band.

Use the pinned Isaac/YAM environment:

```sh
python tasks/fold-a-pop-up-laundry-hamper/run.py --mode hold --steps 40 --out /tmp/hamper-reset
```

Original procedural geometry, MIT license. The original failed model is recoverable from shared main commit9bc7f6e. Final documentation, native demo, Dream baseline, rescoring and media remain outstanding.
