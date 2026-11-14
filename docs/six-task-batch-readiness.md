# Six-task batch: submission status

Updated 14 November 2026, 22:23 UTC. The user has authorized one PR per task.
**Cake has a PR. The other five still need complete demonstrations.**

| Task | Latest evidence | Remaining work |
| --- | --- | --- |
| [Cake PR1919](https://github.com/robocurve/benchmark-tasks/pull/1919) | Demo1.0 and Dream0.0; uploaded media and independent judging complete. Revised category/context after the jobs-importance rejection. | The board returned an ingestion server error twice. No revised receipt yet. Keep the same PR. |
| [Wheel](../tasks/true-a-bicycle-wheel/README.md) | The first turn unwinds during withdrawal. No retained repair yet. | Finish the adjustment, release/spin the wheel, and measure the final result. |
| [T-shirt](../tasks/peg-out-a-tshirt/README.md) | The first-clip continuation still loses the grip or carries a closed peg; a shorter pickup correction is running. | Complete both clips, released retention, then a full fresh-start episode. |
| [Staple](../tasks/remove-a-staple/README.md) | The latest stop was an overly conservative wire-endpoint check; actual steel boxes still overlap. The solid-geometry audit is corrected. | Complete extraction, released hold and independent judging; full193 is running. |
| [Seam](../tasks/unpick-a-seam/README.md) | One cut and clean reverse withdrawal completed in327 actions, with no reported damage. Full six-cut191 is running. | Verify removal and fabric preservation using actual panel/contact geometry, then finish all six stitches. |
| [Necktie](../tasks/tie-a-necktie/README.md) | Adult collar drape, physical handoffs and ordinary wrapping motions. | The narrow-end grip slips during repositioning. A deeper pinch is being tested; no knot or released fit yet. |

These are development results, not acceptance claims. Reconstructed checkpoints
save iteration time but cannot be spliced into submission demonstrations.

## Compute

Two A40 Pods are currently active at$0.59/hour each. Their independent shutdown
watchdogs read current deadlines from the lifecycle files below. Trials have
separate process caps; stop early after collecting completed evidence.
Lifecycle records are in ignored local folders:

- `artifacts/submission-fresh-2026-11-14/`
- `artifacts/submission-materials-2026-11-14/`

The earlier cumulative compute estimate was$23.70, excluding storage and Dream.
Add this session's elapsed rental cost after shutdown. This is not an invoice or
remaining balance. No new Dream calls have been made for the unfinished tasks.
Stopped older Pods still retain their disks.

## Submission requirements

Use one complete full-score demonstration, a Dream run on the same setup,
independent scoring, anonymous media and concise reproducible instructions.
Numerical and material approximations must be explicit and preserve the defining
skill. Accepted tasks provide useful examples of practical approximations; they
do not remove the need to demonstrate the actual task.

Refresh ownership/novelty before each submission. Create a separate branch from
fresh upstream/main containing only the validated task folder. Keep shared notes
and private evidence out of the upstream PR. User authorization to submit is
already in place.

Current code is on `codex/six-task-completion-2026-11-13`; detailed findings and
reproducible evidence locations are in [TEAM_LEARNINGS.md](../TEAM_LEARNINGS.md).
The ten additional ideas remain deferred until this PR batch and GPU shutdown,
as requested. No compute has been used on them.
