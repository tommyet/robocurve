# Six-task batch: submission status

Updated 13 November 2026, 23:11 UTC. The user has authorized one PR per task.
**Cake is submitted. The other five are not submission-ready.**

| Task | Current evidence | What prevents submission |
| --- | --- | --- |
| [Cake](https://github.com/robocurve/benchmark-tasks/pull/1919) | Full robot demo scores 1.0; Dream scores 0.0; independent rescoring, media and setup checks complete. Received as TK-XPE4K7. | Awaiting review; no acceptance or revision decision yet. |
| [Wheel](../tasks/true-a-bicycle-wheel/README.md) | Native wrench engagement and partial nipple rotation. A new ordinary left-hand rim-bracing plan passes all 1,182 commanded-pose collision checks. | The latest native trial loses its wrench grip during the first turn. The bracing candidate is untested. Full repair, released rotation and numeric judging are absent. |
| [T-shirt](../tasks/peg-out-a-tshirt/README.md) | Flexible garment, physical spring pegs, native pickup and one-hand retention diagnostics. | Retained cloth has a 0.367 mm triangle overlap with a finger. A finer mesh settles clearly but its fresh pickup was stopped for runtime before reaching the grasp. No complete two-peg hang exists. |
| [Staple](../tasks/remove-a-staple/README.md) | Plastic steel bending and flexible, punctured paper; real remover contact. | Paper panels separate beyond the declared continuity limit before extraction. Higher solver iteration counts and a smaller timestep have not resolved this. |
| [Seam](../tasks/unpick-a-seam/README.md) | Flexible panels, real thread loops and contact-qualified cutting. | Loaded blade contact causes excessive fabric strain or thread/fabric crossing before a valid cut. A stationary short control passes, but this does not establish cutting. |
| [Necktie](../tasks/tie-a-necktie/README.md) | Adult collar drape, wide-end transfer and narrow-end pickup. A refined 40-action contact diagnostic passes five sampled robot, fixture and transverse self-crossing checks. | No complete physical knot, wearable adjustment or released retention. The short test reconstructs a recorded state and is not demonstration evidence. |

## Compute and saved work

All Runpod GPUs are stopped. A fully paginated account check at **23:11 UTC**
found six Pods and **zero active Pods**. The last GPU stopped at 23:10 UTC.
All final trial archives were downloaded and SHA-256 checked before shutdown.
Stopped Pods retain their disks; this is a GPU shutdown, not disk deletion.

Estimated cumulative compute is **$23.70**, compared with the original **$18**
batch target. This uses recorded elapsed rental time and API hourly rates. It
excludes storage and Dream charges and is neither an invoice nor a remaining
account balance. No additional Dream runs were made for the five blocked tasks.

Code and current validation records are on `codex/six-task-completion-2026-11-13`.
Detailed findings and reproducible evidence locations are in
[TEAM_LEARNINGS.md](../TEAM_LEARNINGS.md). Full recordings and private lifecycle
records remain in ignored local `artifacts/` folders. The cake PR contains only
its validated task folder, from a separate fresh-upstream submission branch.

## Required before the other PRs

1. Resolve the defining interaction without hidden attachments, state animation,
   invalid material crossings or weakened scoring conditions.
2. Record one complete fresh-start full-score robot demo. Short reconstructed
   diagnostics cannot be joined together or promoted into a task episode.
3. Run Dream with the same reset and physics, then independently rescore and
   inspect both videos. Disclose extra state used by any feasibility controller;
   Dream must receive its ordinary policy observations.
4. Refresh ownership/novelty checks, finalize concise setup and fidelity text,
   upload anonymous media and submit only that task folder.

The latest board check at 22:20 UTC covered 599 tasks and found no new direct
title match for the five unfinished tasks. This is a dated screen, not a claim
reservation or assurance of acceptance.

The ten additional ideas requested after this batch remain unbuilt and
unresearched. Their investigation has not started because the requested PR stage
is incomplete. No compute has been used on them.
