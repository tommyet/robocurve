# Secure a ponytail with a plain hair elastic

**Development draft. No full-score demo, Dream baseline or submission yet.**

Gather the loose hair into a ponytail and secure it with the plain elastic. Leave it held after both hands let go.

The procedural scene is in `geometry.py`; native contacts and passive material responses are used. `model.py` defines provisional outcome checks. These files are under active validation and must not be treated as accepted or submission-ready.

In the pinned Isaac/YAM environment, from the repository root:

```sh
python tasks/secure-a-ponytail/run.py --mode hold --steps 40 --out /tmp/secure-a-ponytail-reset
```

All geometry is original procedural work under the included MIT license. `ENVIRONMENT.json` pins the external runtime. Paid diagnostics and source snapshots are retained privately; `VALIDATION.json` must be completed before submission.
