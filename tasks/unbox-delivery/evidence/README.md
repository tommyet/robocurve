# Validation evidence

The handle-free, wrapped-tape scene has two sealed-start scripted demonstrations
scoring 1.0. `full-004-audit.json` and `full-005-audit.json` record independent
replay, source hashes,
action checks, final state and complete three-camera frame counts.
`full-demo.jsonl.gz` contains only anonymous measured scorer inputs from that
run; it excludes stored score claims and controller text.

Replay from the task directory without Isaac:

```bash
gzip -dc evidence/full-demo.jsonl.gz > /tmp/unbox-full-demo.jsonl
python3 replay.py /tmp/unbox-full-demo.jsonl
python3 -m unittest -v test_scoring
```

`VALIDATION.json` distinguishes original, curated and compressed trace hashes.
`dream-001-audit.json` records the genuine Dream-1 run: 0.0 after 3,600 actions,
with 3,601 frames per camera, identical setup/runtime, and normal action-limit
termination. `dream-run.jsonl.gz` contains its anonymous scorer inputs. Replay
it with the same command pattern above; expected score is 0.0.

Full videos, source snapshots and raw trial evidence are kept in ignored local
artifacts; no media has been submitted. The pre-cut opening diagnostic earns
zero task credit and is not this sealed-start demonstration.

Earlier successful demonstrations used grasp tabs and a top-only tape seam.
Their trace and audits are archived under `tabbed-v1/`; use that folder's
versioned replay instructions. They do not validate the revised scene.
