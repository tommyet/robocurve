# Current table-method evidence

`table-pilots.json` preserves nineteen failed pilots and the first complete
table-method demo, trial 020, independently replayed at **1.0**. It starts with
an uncrossed free cord, forms the knot through robot contact, pulls both ends
together and retains the knot for five seconds after release. Matching Dream
trial 021 completes 150 seconds and independently scores **0.0**. Its 61 server
session expirations across 62 successful chunks confound interpretation as an
uninterrupted baseline; the full trace remains a valid unknot throughout.

The record includes scoring windows, source and video hashes, native-step
certification, transport continuity, and robot-clearance audits of every recorded
pose. Complete recordings remain
in the ignored `artifacts/rope-knot-table-session/` directory and on the retained
VM. These summaries support review; they do not replace the recordings or
establish calibration, repeatability or geometry between recorded frames.

`bimanual-pilots.json` contains five earlier high-lift loop probes, all scoring
zero. `loop-001-crossing.json` is a measured regression fixture for a crossing
search bug. The older kinematic audits establish commanded reach, not successful
rope manipulation.

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
