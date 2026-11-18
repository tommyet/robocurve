# Change the fuse in an unplugged UK plug

**Development draft. No full-score demo, Dream baseline or submission yet.**

Replace the fuse in the unplugged plug with the spare of the same rating, and refit its fuse carrier securely.

The procedural scene is in `geometry.py`; native contacts and passive material responses are used. `model.py` defines provisional outcome checks. These files are under active validation and must not be treated as accepted or submission-ready.

In the pinned Isaac/YAM environment, from the repository root:

```sh
python tasks/change-a-plug-fuse/run.py --mode hold --steps 40 --out /tmp/change-a-plug-fuse-reset
```

All geometry is original procedural work under the included MIT license. `ENVIRONMENT.json` pins the external runtime. Paid diagnostics and source snapshots are retained privately; `VALIDATION.json` must be completed before submission.

## Development commands

From the repository root in the pinned environment, use a new output folder:

```sh
python tasks/change-a-plug-fuse/run.py --mode demo --out /tmp/change-a-plug-fuse-demo
python tasks/change-a-plug-fuse/rescore.py /tmp/change-a-plug-fuse-demo
```

The deterministic layout has no jitter or random seed. Source files and native
state are saved with each run. Rescoring verifies their hashes and re-evaluates
the recorded states on CPU. Diagnostics with `--capture-every` greater than1
are not submission recordings. Dream must use the same final scene and hardware.
