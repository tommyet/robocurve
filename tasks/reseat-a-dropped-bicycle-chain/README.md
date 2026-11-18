# Put a dropped bicycle chain back on its chainring

**Development draft. No full-score demo, Dream baseline or submission yet.**

Put the dropped chain back on the chainring, then turn the crank backwards through one full revolution without the chain dropping or jamming.

The procedural scene is in `geometry.py`; native contacts and passive material responses are used. `model.py` defines provisional outcome checks. These files are under active validation and must not be treated as accepted or submission-ready.

In the pinned Isaac/YAM environment, from the repository root:

```sh
python tasks/reseat-a-dropped-bicycle-chain/run.py --mode hold --steps 40 --out /tmp/reseat-a-dropped-bicycle-chain-reset
```

All geometry is original procedural work under the included MIT license. `ENVIRONMENT.json` pins the external runtime. Paid diagnostics and source snapshots are retained privately; `VALIDATION.json` must be completed before submission.
