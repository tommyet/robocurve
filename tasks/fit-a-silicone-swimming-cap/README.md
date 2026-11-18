# Put a silicone swimming cap onto a headform

**Development draft. No full-score demo, Dream baseline or submission yet.**

Stretch the swimming cap over the headform. Cover the crown, leave the face clear, and release it without tearing the cap.

The procedural scene is in `geometry.py`; native contacts and passive material responses are used. `model.py` defines provisional outcome checks. These files are under active validation and must not be treated as accepted or submission-ready.

In the pinned Isaac/YAM environment, from the repository root:

```sh
python tasks/fit-a-silicone-swimming-cap/run.py --mode hold --steps 40 --out /tmp/fit-a-silicone-swimming-cap-reset
```

All geometry is original procedural work under the included MIT license. `ENVIRONMENT.json` pins the external runtime. Paid diagnostics and source snapshots are retained privately; `VALIDATION.json` must be completed before submission.

## Development commands

From the repository root in the pinned environment, use a new output folder:

```sh
python tasks/fit-a-silicone-swimming-cap/run.py --mode demo --out /tmp/fit-a-silicone-swimming-cap-demo
python tasks/fit-a-silicone-swimming-cap/rescore.py /tmp/fit-a-silicone-swimming-cap-demo
```

The deterministic layout has no jitter or random seed. Source files and native
state are saved with each run. Rescoring verifies their hashes and re-evaluates
the recorded states on CPU. Diagnostics with `--capture-every` greater than1
are not submission recordings. Dream must use the same final scene and hardware.
