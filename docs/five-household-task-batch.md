# Five household tasks — development record

User authorized implementation, paid validation, media upload and one PR per
task on 15 November 2026. Use proportionate, disclosed material models and
plain descriptions. No submission until a full-score ordinary-action demo
and the required genuine Dream attempt have been recorded and inspected.

| Task | Current state |
|---|---|
| Fasten a bracelet | Final native demo007 1.0, Dream007 0.0; independent replay and visual review passed. Media M-S6J36D uploaded; [PR2187](https://github.com/robocurve/benchmark-tasks/pull/2187) received as TK-ZVS8SJ; waiting for review. |
| Wrap a present | Pre-cut, pre-creased cross-shaped paper, four folding flaps and two tape strips. CPU007 full score; native010 tests the corrected tape pickup clearance, finger-pad holding contact and true edge-bridging tape bond. |
| Rock a pram smoothly | Final native demo007 scores 1.0 with carrycot/doll collision shells; ten cycles and released stop. Dream007 0.0; replay and visual review passed. Media M-6UKL98; [PR2190](https://github.com/robocurve/benchmark-tasks/pull/2190) opened. |
| Genuine knot removal | A 1.075 m, 10 mm polyester cord with a loose overhand. Native eight-second settling probe retains the knot. Native008 support grasp works but free-end grasp closes along the cord and slips. Native011 grasps and briefly unthreads it, but returns through the loop. Native014 moves the loop aside before withdrawing the free end. |
| Apply, smooth and peel a wax strip | Flexible strip on silicone leg form; native006 revealed a fingertip geometry and capture issue. Corrected native008 scores 1.0; replay agrees, visible peel completes in 0.6 s. Dream008 0.0; source-matched, rescored and visually checked. Media M-SSD6AZ; [PR2192](https://github.com/robocurve/benchmark-tasks/pull/2192) received as TK-AGWK73. No hair-removal claim. |

Fresh board check found no direct matches. Prior comparison and adjacent
accepted/rejected tasks: [research](task-ideas-followup-2026-11-15.md).
Development branch: `codex/five-household-tasks-2026-11-15`.
Private runs and cloud lifecycle records: ignored
`artifacts/five-household-2026-11-15/`. One A40 Pod `vmtb7b46hnozdv` started at 22:01:58 UTC, $0.59/hour, no persistent volume. Independent stop watchdog deadline extended under supervision to 01:03:44 UTC on 16 November; current paid run uses the same Pod. All lifecycle state is in the ignored batch directory. Never stop the teammate’s separate Brev VM.

Batch GPU work after useful CPU preparation; one separately supervised stop
deadline per rental. Save evidence locally and verify shutdown. Each competition
branch must start from fresh upstream/main and contain only its task folder.

Native pram004: 940 actions / 47 s; 385.71 wall seconds, score 1.0. Front/rear setup and four motion/release frames inspected; complete video and source archive saved locally. Native bracelet002 failed due to close arm approach;004 reached the clasp but missed insertion. These are development trials, not successful submission evidence. The public v21 prompt URL now returns 404; do not reuse the corrupt older decoded file as guidance.
