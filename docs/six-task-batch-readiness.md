# Six-task batch: submission status

Updated 2026-11-16, after the necktie reproducibility revision. All six have
been submitted. Four await review, including the received necktie revision, and
two are closed, with a correction request posted for staple removal. An open
PR or ingestion receipt is not acceptance.

| Task | PR / current outcome | Note |
|---|---|---|
| Cake border | [#1919](https://github.com/robocurve/benchmark-tasks/pull/1919), pending TK-LE2FKY | Category/context revision received. |
| Bicycle wheel | [#2091](https://github.com/robocurve/benchmark-tasks/pull/2091), final rejection | Reviewer found the specialist repair did not meet the selected relevance domain. |
| Peg out a T-shirt | [#2126](https://github.com/robocurve/benchmark-tasks/pull/2126), pending TK-T6ZGSF | Flexible garment demo and matching baseline submitted. |
| Staple removal | [#2093](https://github.com/robocurve/benchmark-tasks/pull/2093), closed after duplicate rejection | The bot created two task IDs for one PR. A correction requesting human review is posted; no reply yet. |
| Unpick a seam | [#2113](https://github.com/robocurve/benchmark-tasks/pull/2113), pending TK-QM5PG5 | Completed demo and matching baseline submitted. |
| Fit a loose necktie | [#2168](https://github.com/robocurve/benchmark-tasks/pull/2168), revision pending TK-HMYHKL | Specifies the Simple knot, threading diagram, both blade poses and reset. Demo 1.0; Dream 0.0. |

## Necktie scope and evidence

Use [`tasks/fit-a-loose-necktie`](../tasks/fit-a-loose-necktie/README.md).
The earlier `tie-a-necktie` folder preserves failed full-cloth threading
experiments; it is not the submitted task.

The new task uses a disclosed fixed-topology model with idealized geometric
grasp capture and relative sliding. It preserves material length, allows
loosening and missed/slipped grasps, and requires a released final fit. It does
not resolve full cloth contact, internal folds or material reaction forces.

Final native YAM demo: 1.0 after 580 actions / 29 seconds, including 7.55 seconds
released. Matching Dream: 0.0 after all 1,200 actions, 146 requests, one session.
Both use identical runtime code. The earlier Dream wording refusal is recorded
separately; the final instruction explicitly names a plastic form with no person.
Original media M-YCTY75 was received as TK-KYVRXZ, then returned for a clearer
threading/reset specification. Revision commit115c231 adds this specification
and a labelled diagram. Media **M-HUSZ3C** retains the same videos with an
expanded setup image. Source hashes match; five CPU tests and both saved-run
scores pass. No additional GPU or Dream compute was used.
The revision was received at 09:33:27 UTC on 16 November as **TK-HMYHKL**,
a revision of TK-KYVRXZ. It is waiting for review, not accepted.

## Compute and retained evidence

At the original necktie completion on 15 November, all ten listed Runpod Pods
were confirmed EXITED at 20:12:55 UTC; no active
Pods or persistent mounts were present. The finishing session lasted about
56 minutes, estimated at $0.5505 compute plus $0.0130 temporary container disk.
Dream charges are separate. These are rental-time estimates, not an invoice.

Through that stop, the reconciled cumulative estimate is about **$37.26 Runpod
compute**, or **$37.90 including temporary disk**, excluding Dream, taxes and
account adjustments. The key lacks billing-read access. Older subtotals and
claims that Runpod container disks remain retained were incorrect; use the
dated accounting in [TEAM_LEARNINGS.md](../TEAM_LEARNINGS.md).

Verified raw recordings, source snapshots and lifecycle records are local in
ignored `artifacts/necktie-finish-2026-11-15/` and the earlier evidence folders.
The repository contains curated numeric evidence and reproducible task code.

## Next work

The later bracelet, pram, present-wrapping, untying and waxing submissions are
tracked in [the five-task batch](five-household-task-batch.md). Use the latest
dated team notes for subsequent compute totals and review decisions.

Pending submissions are frozen. Do not push changes expecting another review
until feedback arrives. New competition submissions must start from fresh
upstream/main and contain only their own validated task folder.
