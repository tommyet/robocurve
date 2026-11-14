# Six-task batch: submission status

Updated 2026-11-14 23:03 UTC. One PR per task is authorized.
**Cake is awaiting review. The other five are not ready to submit.**

| Task | Current result | Submission blocker |
| --- | --- | --- |
| [Cake PR1919](https://github.com/robocurve/benchmark-tasks/pull/1919) | Demo1.0, Dream0.0; anonymous media and judging complete. Requested category/context revision received as **TK-LE2FKY** at22:50 UTC. | Await organizer review. Do not change the pending submission. |
| [Wheel](../tasks/true-a-bicycle-wheel/README.md) | Robot turns a nipple, but withdrawal undoes the adjustment. | Retained repair, released full revolution and final measurement. |
| [T-shirt](../tasks/peg-out-a-tshirt/README.md) | Flexible hem pickup; peg manipulation still fails. | Both clips must capture the garment and line, followed by released retention. |
| [Staple](../tasks/remove-a-staple/README.md) | Remover lifts away without extracting the staple. The clinch also changes before robot contact. | Correct and verify the passive reset before another extraction attempt. |
| [Seam](../tasks/unpick-a-seam/README.md) | One thread cut; second feed exceeds the flexible-panel model's supported aperture. | Remove all six stitches while preserving the fabric. |
| [Necktie](../tasks/tie-a-necktie/README.md) | Wide-tip pickup works; narrow strip slips during repositioning. | Reliable moving grip, actual threading/tightening and released wearable fit. |

No new PRs were opened for the five failed demonstrations. No task score is
claimed for them. Reconstructed checkpoints save iteration time but cannot be
spliced into submission demonstrations. Each still needs a complete full-score
fresh-start demo, matching Dream run, independent judging and anonymous media.

## Compute and evidence

Both A40 Pods are confirmed **EXITED** after local archive verification.
This batch used approximately **$3.25** in elapsed compute at$0.59/hour per
Pod. The cumulative working estimate is **$26.95**, including the earlier
$23.70 subtotal. Storage and Dream charges are excluded; this is not a bill or
remaining balance. No new Dream calls were made for the unfinished tasks.
Stopped Pods retain their disks.

Exact lifecycle records and SHA256-verified result/source archives are in the
ignored local `artifacts/submission-fresh-2026-11-14/` and
`artifacts/submission-materials-2026-11-14/` directories. Detailed findings and
reusable evidence locations are in [TEAM_LEARNINGS.md](../TEAM_LEARNINGS.md).

## Submission workflow

Keep each submission on a separate branch from fresh upstream/main containing
only its validated task folder. Keep shared notes and private evidence out of
the upstream PR. User approval to submit is already in place. Refresh novelty
and ownership before submission; the22:52 title screen found no matching titles
for these five, but it is not an exhaustive novelty guarantee.

The ten additional ideas remain deferred until this submission batch is done,
as requested. No GPU or Dream compute has been used on them.
