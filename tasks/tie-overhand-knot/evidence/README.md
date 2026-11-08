# Development evidence

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
