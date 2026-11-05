# Four brick tasks: packaging review

Final packaging reviewed 2026-11-04 (Pacific time), with evidence finalized on
November 5 UTC. This is a development review outside any single-task submission.
The [short review](brick-batch-review.md) links all eight local videos.

## Completed checks

- Four standalone task folders contain the scene, controller, scorer, printable
  CAD, exact reproduction commands, measured environment versions and curated
  anonymous evidence. Each is below the observed 25 MB code limit.
- All four final robot demonstrations score 1.0. All four fresh Dream trials
  complete the 1,200-action limit and score 0.0. Independent replay agrees with
  every score. The audit checks source hashes, full telemetry, executed action
  limits, complete frame counts and video encoding; the shared scorer passes
  54 unit tests. No result is inferred from a planned controller motion.
- Full videos and setup images are local; media IDs remain empty because no
  upload has been requested. Task scores include actual Dream recovery counts.
  Fidelity text is 365 characters and score text is below 300 characters.
- Task text and curated numeric evidence contain no team identity or private
  paths. Sampled video frames and setup views show no team/account identifiers.
  Visual review sampled key times; timing and every-frame completeness were
  checked independently. This is not a claim that every frame was watched.
- All final traces contain conservative envelopes for all nine collision links
  of each arm. The unsupported lift requires the whole robot to clear blue,
  followed by stable release. Final scores use the final state, not a historical
  maximum. Boundary failures and malformed evidence have explicit handling.
- The four demonstrations visibly show pickup, the intended assembly,
  unsupported retention and release. The offset join's known grid and half-width
  displacement establish the two engaged studs even when one unused stud is
  occluded. Judging instructions explain that inference and do not require
  seeing inside the sockets.
- The precise 1 mm alignment and 0.75 mm seating checks use part dimensions,
  body edges, ruler/calipers and orthogonal views. An arbitrary oblique frame
  alone cannot prove a hidden submillimetre gap. Numeric telemetry supports
  the simulation evidence; it does not remove this manual measurement limit.
- Both STL files have matching geometry/source hashes and validation records.
  Each is one watertight connected body. Model masses are rounded solid-PLA
  volume estimates, not measurements of prints. No official LEGO compatibility
  or calibrated insertion/retention force is claimed.
- The builder reads results only from completed validation records and preserves
  the distinction between tested simulation, user review and submission. The
  final records include actual wall times and installed source revisions.

## Remaining decisions before submission

1. **Importance and duplication.** The bounded check below found direct prior
   DUPLO ideas and an existing two-brick benchmark. Four separate acceptances
   should not be assumed. Refresh the board before choosing what to submit.
2. **Physical fidelity.** Contact compliance and friction produce retained joins
   in simulation, with negative controls, but print tolerances, insertion force,
   pull-out force and breakage have not been calibrated against real parts.
3. **Model-run interpretation.** All four Dream runs used standard recovery for
   expired sessions. Request/session counts are disclosed. The effect on model
   performance is unknown, so these are not uninterrupted inference baselines.
4. **User review and submission.** No new upload or upstream PR is authorized.
   Review the local videos, then choose the tasks. Any later submission needs
   its own media ID and one-task branch/PR; shared notes, this review and
   `brick_workbench/` stay outside that competition diff. The die PR is unchanged.

## Bounded novelty check — 2026-11-04

This check used the authorized saved board response
`artifacts/roll-a-die-v3/board-status-2026-11-04.json`: 246 entries, comprising
156 pending tasks and 90 previous-cohort plans. The newest listed submission
was at 07:43:31 UTC on November 4. The older `board-preflight.json` has 128
entries and is not the current snapshot. A live refresh was not obtained during
this bounded audit, so these findings do not establish current availability.

The saved [Robocurve board](https://tasks.robocurve.org/board) interface explicitly
says that previous-cohort plans have not been submitted or reviewed, but new
tasks should differ from them too. They are relevant prior ideas, not evidence
of acceptance or a current submission hold. These are the closest matches:

| Board task | Snapshot status | Relationship to this family |
|---|---|---|
| `TK-KVRZSQ` — Build a DUPLO structure from an image | Planned, previous cohort | Broader brick assembly with image interpretation and assembly-order planning; basic joining is a constituent action. |
| `TK-V7WF4F` — Build a DUPLO overhang | Planned, previous cohort | Staggered construction with one arm stabilizing the upper section while the other attaches a brick; closest to the offset two-stud target. |
| `TK-RHLLE6` — Build a DUPLO bridge | Planned, previous cohort | Aligning a movable pillar and connecting a spanning brick to two pillars; different topology, but the same construction domain. |
| `TK-G9QH74` — Close a snap-fit case lid | Pending | Aligning and pressing a lid until two latches engage while stabilizing a light case; related contact/retention mechanics. |
| `TK-2K8E9N` — Plug a keyed connector into a loose socket block | Pending | Alignment, insertion and latching while controlling a loose base; related manipulation skill, different part function. |

A search of all saved task text found only the three planned DUPLO entries
explicitly naming LEGO or DUPLO. That is a limited keyword finding, not proof
that all other tasks differ meaningfully.

[WorkBenchMark](https://workbenchmark.github.io/) is a direct external comparison:
its first tier includes two-brick DUPLO assemblies. Its
[official dataset](https://github.com/WorkBenchMark/dataset) lists 100 two-block
tasks and uses 2×2 and 4×2 bricks; the project page also covers overhangs in more
complex assemblies. The documented task is to build the target and leave it
free of robot contact. Our explicit unsupported lift tests retention beyond
that stated completion rule. This is a defensible scoring distinction, not
evidence that basic two-brick joining is new.

For a named competition comparison, RoboDojo's official
[stack-blocks implementation](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/main/task/RoboDojo/tasks/stack_blocks.py)
scores a three-block stack with open grippers, and its
[tower implementation](https://github.com/RoboDojo-Benchmark/RoboDojo/blob/main/task/RoboDojo/tasks/build_tower.py)
checks a wooden block/board structure. Neither inspected task specifies an
unsupported press-fit retention proof. This was a targeted comparison, not an
exhaustive audit of LIBERO, RoboCasa, SimplerEnv, BEHAVIOR or DataCenterBench.

**Assessment:** there is substantial near-duplicate risk in submitting all four
as separate tasks. The four-contact join, small single-contact pair, mixed-size
single-contact join and offset two-contact join differ mechanically, but share
the same pickup, press, unsupported lift and release objective. The 1×1 version
has the weakest standalone novelty case if its main distinction is size. The
mixed version adds an asymmetric load and the offset version an overhang, but
these remain variations of the same connection test; the offset version also
has the closest board match.

Keep all four as a useful learning and evaluation family. For submission,
prioritize the instance with the clearest demonstrated retention behavior and
explain that capability precisely. Four folders and four successful demos do
not establish four materially distinct tasks. Do not claim novelty merely from
custom CAD, colours, stud count, or a different simulator. Acceptance remains
the reviewers' decision.

The final controlled build regenerated the four task packages from the frozen
shared implementation and recorded evidence. No upload or new submission was
made during this work.
