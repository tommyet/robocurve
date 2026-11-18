# Remove trapped hair from a hairbrush

**Development draft. No full-score demo, Dream baseline or submission yet.**

Use the pin-tail comb to lift the trapped hair out of the brush. Leave the brush clear and its pins intact.

The procedural scene is in `geometry.py`; native contacts and passive material responses are used. `model.py` defines provisional outcome checks. These files are under active validation and must not be treated as accepted or submission-ready.

In the pinned Isaac/YAM environment, from the repository root:

```sh
python tasks/clear-hair-from-a-hairbrush/run.py --mode hold --steps 40 --out /tmp/clear-hair-from-a-hairbrush-reset
```

All geometry is original procedural work under the included MIT license. `ENVIRONMENT.json` pins the external runtime. Paid diagnostics and source snapshots are retained privately; `VALIDATION.json` must be completed before submission.

## Development commands

From the repository root in the pinned environment, use a new output folder:

```sh
python tasks/clear-hair-from-a-hairbrush/run.py --mode demo --out /tmp/clear-hair-from-a-hairbrush-demo
python tasks/clear-hair-from-a-hairbrush/rescore.py /tmp/clear-hair-from-a-hairbrush-demo
```

The deterministic layout has no jitter or random seed. Source files and native
state are saved with each run. Rescoring verifies their hashes and re-evaluates
the recorded states on CPU. Diagnostics with `--capture-every` greater than1
are not submission recordings. Dream must use the same final scene and hardware.
