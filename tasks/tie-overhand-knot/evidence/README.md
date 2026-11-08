# V4 development evidence

The revised free-cord task has no successful full demonstration yet.
`bimanual-pilots.json` records the physical loop probes, all scoring zero,
with source, trajectory and video hashes. `loop-001-crossing.json` is an
anonymous measured regression fixture for a crossing-search bug, not a knot.
The kinematic audits establish commanded robot reach and envelope separation;
they do not establish rope contacts or task feasibility.

# Historical v3 jig-task evidence

The old jig-task scripted demo independently scores **1.0**; its Dream-1 run
scores **0.0** under the old rubric. Neither validates the revised free-cord
task or its robot-only pull. The JSON audits contain measured extrema, executed-action checks,
source comparisons, certified replay results and video hashes. They are audit
summaries, not substitutes for the complete recordings.

The original full trajectories, videos, runtime files, actions and source
snapshots remain in the ignored local directories
`artifacts/rope-knot-development/demo-009/` and `dream-001/` at the repository
root. `final-runtimes.json` preserves their configuration and source hashes.
The final demo was rescored after the reporting/certificate fix; physics,
controller and geometric scoring code are unchanged. The postprocessing video
renderer was finalized after capture. Both final replay scores match.

Read `demo-velocity-spike.json` and the limitations in `demo-audit.json` before
making physical-fidelity claims. The demo proves one scored simulation outcome;
it does not calibrate a real cord or establish repeatability.

# Historical development traces

These recordings are **not successful knotting demonstrations**. Each scores
zero. The compressed traces contain measured geometry; the paired runtime
files preserve physical dimensions, configuration and source hashes.

- `diagnostic-retention`: an explicitly preformed knot survives the revised
  seating and load test. Its diagnostic flag permanently prevents task credit.
- `jig-idle`: the untied three-peg layout settles for 5.05 seconds.
- `straight-idle`: an unanchored straight cord settles for 5.05 seconds.

From the task directory, replay without a GPU:

```bash
python replay.py evidence/diagnostic-retention.jsonl.gz --runtime evidence/diagnostic-retention-runtime.json
python replay.py evidence/jig-idle.jsonl.gz --runtime evidence/jig-idle-runtime.json
python replay.py evidence/straight-idle.jsonl.gz --runtime evidence/straight-idle-runtime.json
```

The diagnostic retention trace reports `candidate_score: 1.0` solely to test
the assay implementation. Its actual `score` remains `0.0`. It must never be
used as the competition demonstration or relabelled as robot work.
