# Five household tasks — submission record

## Latest review status — 16 November, 09:12 UTC

Bracelet2187, pram2190, wrapping2197 and knot-removal2211 are still waiting for
review. **Wax2192 was finally rejected at 06:41 UTC**: reviewers consider hair
removal and skin handling central to waxing, so the hairless practice-form
strip task fails importance and construct validity. It cannot be revised;
a human-review request is permitted within 48 hours of that decision.
[Decision](https://github.com/robocurve/benchmark-tasks/pull/2192#issuecomment-6909398366).
No appeal has been posted. The validation/submission record below is historical.

User authorized implementation, paid validation, media upload and one PR per
task on 15 November 2026. Use proportionate, disclosed material models and
plain descriptions. No submission until a full-score ordinary-action demo
and the required genuine Dream attempt have been recorded and inspected.

| Task | Current state |
|---|---|
| Fasten a bracelet | Final native demo007 1.0, Dream007 0.0; independent replay and visual review passed. Media M-S6J36D uploaded; [PR2187](https://github.com/robocurve/benchmark-tasks/pull/2187) received as TK-ZVS8SJ; waiting for review. |
| Wrap a present | Native demo015 1.0, Dream012 0.0; independent replay and visual review passed. Media M-R4FZXS; [PR2197](https://github.com/robocurve/benchmark-tasks/pull/2197) received as TK-R879EX. Exact draw-only source difference is disclosed and verified inactive in the baseline. |
| Rock a pram smoothly | Final native demo007 scores 1.0 with carrycot/doll collision shells; ten cycles and released stop. Dream007 0.0; replay and visual review passed. Media M-6UKL98; [PR2190](https://github.com/robocurve/benchmark-tasks/pull/2190) received as TK-LGTDUX; waiting for review. |
| Genuine knot removal | Final native demo020 **1.0**, 1,710 actions; Dream018 **0.0**, 1,800 actions. Both independent native-trace and compact public CPU replays agree. Initial overhand is fed out, cord freed from the finger, then both ends spread, laid down and released for 6.2 seconds with zero crossings. Media M-DZMUEU; [PR2211](https://github.com/robocurve/benchmark-tasks/pull/2211) received as TK-KHZLE4; waiting for review. |
| Apply, smooth and peel a wax strip | Flexible strip on silicone leg form; native006 revealed a fingertip geometry and capture issue. Corrected native008 scores 1.0; replay agrees, visible peel completes in 0.6 s. Dream008 0.0; source-matched, rescored and visually checked. Media M-SSD6AZ; [PR2192](https://github.com/robocurve/benchmark-tasks/pull/2192) received as TK-AGWK73. No hair-removal claim. |

All five PRs were checked at **01:44 UTC on 16 November**: received, open and
waiting for review. Each contains only its own task folder; none includes shared
team notes or private artifacts. All five demos score **1.0**; all five genuine
Dream baselines score **0.0**. These are submissions, not acceptance decisions.

Fresh board check found no direct matches. Prior comparison and adjacent
accepted/rejected tasks: [research](task-ideas-followup-2026-11-15.md).
Development branch: `codex/five-household-tasks-2026-11-15`.
Private runs and cloud lifecycle records: ignored
`artifacts/five-household-2026-11-15/`. One A40 Pod `vmtb7b46hnozdv` started at 22:01:58 UTC, $0.59/hour, no persistent volume. The Pod was confirmed EXITED at 01:41:09 UTC on 16 November, before its 01:45 watchdog deadline. Fresh paginated inventory showed no active Runpod Pods and no persistent mounts on this rental. All final archives are saved locally; the temporary Dream credential was removed before shutdown. Whole-rental estimate: 3.653 hours at $0.59/hour = $2.155 compute, plus about $0.051 temporary disk, **$2.21 for the batch excluding Dream API charges**. This is a rate-based estimate, not an invoice. Lifecycle and cost evidence are in the ignored batch directory. The teammate’s separate Brev VM was not touched.

Batch GPU work after useful CPU preparation; one separately supervised stop
deadline per rental. Save evidence locally and verify shutdown. Each competition
branch must start from fresh upstream/main and contain only its task folder.

Native pram004: 940 actions / 47 s; 385.71 wall seconds, score 1.0. Front/rear setup and four motion/release frames inspected; complete video and source archive saved locally. Native bracelet002 failed due to close arm approach;004 reached the clasp but missed insertion. These are development trials, not successful submission evidence. The public v21 prompt URL now returns 404; do not reuse the corrupt older decoded file as guidance.
