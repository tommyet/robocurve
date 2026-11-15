# Submission readiness — 2026-11-15

A genuine model attempt is required. Dream-1 may score zero; a full-score scripted/teleoperated demo must establish feasibility if the model does not finish. Partial scores alone do not make a submission ready.

| Task | Current evidence | Submission blockers |
|---|---|---|
| Spray | Fresh clock-only native1.0;779 commands audited; actual Dream camera attempt crashed before actions and is disclosed | SubmittedPR2171/mediaM-Q4X9HF; receivedTK-6QV5KK, awaiting review |
| Carton breakdown | Native0.25; all158 tape cells cut and cutter parked | Full opening and collapse demo; genuine Dream attempt; novelty relative to existing carton tasks |
| Carton packing | Original native0; current offline placement rescore0.25; isolated tape material coupon | Robot peel/apply/cut/seal-retention demo; genuine Dream attempt; accepted tape-gun task overlap |
| Hair drying | Old swivelling-head native0; fixed-head source5d1e685 passes42CPU/USDtests | Native fixed-head switch/coverage/full-drying demo and genuine Dream attempt |
| Ethernet | Scored release0; isolated prepress and unscored grasp probes | Full crowded clip release/transfer/reinsert demo; genuine Dream attempt; pending Ethernet-task overlap |

## Media provenance

The five review clips are in `submission-review-videos/`. Their filenames/labels distinguish full teacher replay, partial, old geometry, and unscored probes. None is silently promoted to a new model run.

The planned spray demo export renders actual recorded native body poses and paint updates from the fresh clock-only episode. It will be clearly labelled as offline physics replay, with trace/source and per-frame audit. It is not native RTX camera footage. Current public repository instructions require a demo video but do not explicitly prohibit this rendering method; reviewer acceptance remains uncertain. The state-only run flags remain unchanged. Dream itself must receive real camera observations.

Spray is submitted asPR2171/mediaM-Q4X9HF and receivedTK-6QV5KK; no other task is submitted. The earlier unboxingPR1953 was finally rejected as a duplicate, not accepted.
