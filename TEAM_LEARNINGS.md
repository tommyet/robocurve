# Shared working notes

Last updated: 2026-11-03. Read this before starting work; update it when an
experiment changes what we know. This is a shared operating record for both
developers and their agents, not a competition submission document.

## Agreed workflow

- Commit and push completed work to this fork. Do not open a competition PR
  until the user explicitly asks. Prepare a submission branch containing only
  the relevant task folder; leave these notes and fork-specific instructions out.
- The user confirmed upload team `T-39`. The private `.env.robocurve` stores
  `ROBOCURVE_TEAM` and a single-quoted `ROBOCURVE_TOKEN`. Parse the quoted value
  without displaying it; do not mistake empty quotes for a configured token.
- Before eventual submission, complete fresh VM validation and rescore the final
  demo/Dream evidence with the final scorer. The existing v2 offline rescoring
  is already complete; it does not replace this remaining validation step.
- Reuse **one Brev VM**, currently `robocurve-dice`, while working daily.
  Prepare several tasks locally and batch their GPU trials in one session.
  Initially run simulator trials consecutively, rather than starting competing
  simulator processes on the same GPU.
- Before using the shared VM, check its live state and coordinate with the other
  developer. Record the operator, task/branch, intended runs and completion in a
  dated session entry here. Git notes are not a lock or a live status service;
  do not stop a VM while someone else's trial is running.
- Do scene design, scoring tests, trajectory analysis and documentation locally
  where possible. Start the GPU when a batch is ready. Download results, push
  code and confirm the VM reaches `STOPPED` when the session is finished.
- The user permits the **Dream API key on the team VM** when useful. Transfer it
  without displaying its contents; restrict file access and keep it outside Git,
  logs and artifacts. This approval does not require another confirmation next
  session. Direct Dream access should remove the Mac/SSH bridge dependency;
  its speed benefit has not yet been measured. No transfer has been made yet;
  the next restart attempts failed for regional capacity.
- Keep the five private reference/application PDFs, credentials, `.env*`,
  generated media and full trial artifact directories ignored. Curated anonymous
  numeric traces may be committed inside a task as review evidence after a
  content check; the die task now includes three such compressed traces. See
  [.gitignore](.gitignore).
  This repository is public: do not add account tokens or private application
  content to this log. Keep task text and submitted media anonymous.

## GPU cost and persistence

Observed on 2026-11-03: L40S, 48 GB VRAM, 256 GiB allocated disk. Running rate
**$3.28/hour**, comprising $3.23 compute and $0.05 storage. These are observed
rates for this instance, not guaranteed future prices.

| Quantity | Planning value | Meaning |
|---|---:|---|
| 10 minutes running | $0.55 | Elapsed instance time, including idle gaps; excludes separate Dream API charges. |
| $2 running budget | About 37 minutes | A target, not a user-imposed hard cap. |
| Storage while stopped | $1.20/day | The whole allocated disk, shared by all tasks on this VM; not per task. |
| Clean Dream trial | $0.18 | 197.996 seconds of measured runner wall time, prorated at $3.28/hour. |
| Initial cold installation | About 40 minutes | First environment installation/warmup; excluded from per-trial numbers. |

The actual build configuration is VM mode (`environment.build.vm`, with an
`on_create_script`). Legacy API flags such as `vmOnlyMode` were misleading.
According to [Brev's launchable documentation](https://docs.nvidia.com/brev/concepts/launchables),
the VM setup script does not automatically rerun on restart. The retained
installation should therefore be reusable; boot and simulator initialization
still recur. **A successful restart and cache reuse have not yet been measured.** Two
restart attempts at 13:08 and 13:11 UTC failed because no GPU capacity was
available in the existing region. Stopped data remained inaccessible; local
backups allowed scoring work to continue. Retaining a disk does not reserve a GPU.

Stopping ends compute charges but retains storage. Deleting ends the instance's
charges and removes its data and installation. Copying files locally does not
cancel the allocated disk. See [Brev lifecycle and persistence](https://docs.nvidia.com/brev/concepts/gpu-instances).
Keep the VM between daily sessions as agreed; reconsider retention for longer
gaps. Do not delete it as a routine cleanup step.

Code, final videos, setup images and measured trajectories are already local.
The original raw camera arrays and installed simulator remain on the VM. Before
any later deletion, identify and back up anything still needed. A fresh VM needs
setup again; restoring a full archived environment has not been tested.

Billing snapshot at 12:24 UTC on 2026-11-03: $196.95 of the initial $200 remained
($3.05 posted spend). Billing may lag. Creation through confirmed shutdown at the
displayed running rate gives a conservative **$4.43 estimate**, not an invoice.
Do not add overlapping per-run estimates to this total. Dream API dollars were
not reported by the SDK and remain unknown.

## What the first task taught us

The implementation and run commands are in
[tasks/roll-a-die/README.md](tasks/roll-a-die/README.md); the candid submission
assessment is [docs/roll-a-die-review.md](docs/roll-a-die-review.md).

| Finding | Evidence | Reusable lesson |
|---|---|---|
| Full gripper closure caused vibration around the 16 mm cube. | Trial 001: score 0. | Check contact behaviour visually; reachable poses alone do not prove a grasp. |
| A gentle 15 mm target jaw gap enabled stable pickup. | Trials 002 onward. | Tune grasp pressure/closure before adding a dynamic release. |
| Rotation about the jaw-closing axis transferred little tumble. | Trial 003: 30.274 degrees, score 0.25. | The wrist rotation axis relative to the grasp matters. |
| An upward stroke, world-X rotation and delayed opening produced a roll. | Trial 004: 164.434 degrees, score 1.0 in 9.30 simulated seconds. | Use measured release and object motion, not intended actions, as evidence. |
| A second simulator startup encountered a shader-cache miss. | Trial 004 wall time 321.206 s; earlier short trials 46–73 s. | Start serially initially; measure concurrency before assuming it saves money. |
| Per-tick remote bridge traffic caused Dream session expiry. | First Dream attempt: 49 attempts, 25 sessions, 24 expiries. | A completed evaluation can still be infrastructure-confounded. Inspect sessions and retries. |
| Batching observations fixed that transport problem. | Clean baseline: 25 requests, one session, zero retries; score 0.0. | Use the clean result, preserve the failed attempt as development evidence. |

The batched bridge preserves observation order, timestamps, states, prompt and
the model's frame window. Ten bridge tests, including real HTTP transport and
comparison with the Dream client, passed. The original version also passed twenty-two scorer tests.
Tests do not establish physical realism, repeatability or acceptance.

The runner records cube position, quaternion, linear/angular velocity and
measured hand state every **50 ms**; physics runs at 240 Hz. Scores can be
replayed from `trajectory.jsonl` without a GPU. Keep the final score, rather than
the best historical score, so later violations erase credit. Record source
snapshots, versions, seed, setup image, final videos and runtime for each trial.
Use a new artifact directory for every attempt; do not overwrite evidence.

The scene uses seed 0, no object jitter and a fixed scripted demonstration.
This establishes a simulated manipulation example, not a random/fair die or a
measured repeat-success rate. Numerical differences remain possible; exact
determinism has not been tested. No face value is assigned to the blank cube.

## Open findings and next checks

- **Scoring gap fixed in v2 on 2026-11-03:** v1 could reward repeated small
  rocking. V2 requires at least 90 degrees maximum tilt excursion from the first
  verified free-flight reference, rather than cumulative rotation. Eleven new
  adversarial/boundary tests cover rocking, thresholds, complete revolutions,
  reference poses, pending flight and slow turns; all 46 tests pass (33 scorer, 10 bridge, 3 recorded-evidence replay).
  Offline replay of the unchanged demo is 1.0 (133.207 degrees max excursion),
  partial demo 003 is 0.25 and clean Dream is 0.0. Original logs remain intact;
  `tasks/roll-a-die/VALIDATION.json` identifies these as rescoring, not fresh runs.
- [JUDGING.md](tasks/roll-a-die/JUDGING.md) now describes the reviewer package,
  comparisons, exact rubric and ordinary-video/ruler cross-check. Exact
  acceleration, tiny jaw-clearance thresholds and a blank symmetric cube remain
  limits of manual verification; better close-up footage is desirable. A
  documented cross-check does not itself prove exact manual equivalence.
- Measure the first retained-VM restart and direct-on-VM Dream run. Check that
  `/data/` environment files and caches survived before assuming warm timings.
- At the next approved GPU batch, repeat the frozen demonstration and inspect
  sensitivity to small pose/release changes separately from official fixed-layout
  evaluation. Fresh validation and final rescoring are required before submission.
  One successful final run is not a reliability estimate.
- November 3 refresh: no direct dice-roll duplicate among 40 live upstream PRs
  or the supplied 119-entry board snapshot. No upstream PR was merged. The
  telescoping-lamp template is illustrative; cable-task PRs #12/#13 are pending,
  not accepted precedents. The authenticated live board and wider task sets
  still need a final novelty check before a submission decision.
- Media is prepared locally; `task.json` has no uploaded media ID yet. A private
  task-board token is needed for upload. This is separate from the Dream key.
  Upload completion is not permission to open a PR.

## Dated session log

### 2026-11-03 — scoring v2 correction; GPU batch blocked by capacity

- Operator: repository agent; branch `roll-a-die`. User authorized scoring fixes
  and everything needed for readiness, while retaining the no-PR instruction.
- Shared branch fetched; VM confirmed stopped before requesting restart at
  13:07:55 UTC. Both that attempt and the 13:11 retry failed for regional GPU
  capacity. The planned two repeated demos and direct Dream run did not execute.
  VM confirmed STOPPED at 13:15:58 UTC; no key transfer or environment change.
  Posted credit was $196.16 ($3.84 total spend since the initial $200); billing
  lag/storage prevent attributing the change to these attempts.
- Scorer v2 requires a 90-degree maximum excursion from the verified release
  reference; accumulated rocking no longer earns roll credit. Historical
  trajectories were independently replayed; no evidence was overwritten.
  Results/hashes: `artifacts/die-v2-rescore-001/` and task `VALIDATION.json`.
  Three anonymous compressed trajectories are committed under the task
  `evidence/` directory so other agents/reviewers can reproduce scores offline;
  original raw media and local artifacts remain ignored.
  The demo's first v2 full-score time remains 9.30 s, matching its original
  termination, so no post-termination motion is needed for the corrected score.
- Media-token slot remains empty; user is looking for the Robocurve token.

### 2026-11-03 — first die task and operating agreement

- Code: initial validated implementation `6d38530`, branch `roll-a-die`.
- VM stopped at 12:21:26 UTC; verified stopped at 12:24 UTC. The stop request
  took about eight minutes to finish. Read the live state next session.
- Agreed to reuse one VM daily, develop locally in parallel and batch GPU work.
- User approved Dream-key transfer to the team VM when beneficial; not done yet.
- Recorded the scoring concern above; no task/scorer changes or new GPU trials
  were made during this documentation review. No competition PR is authorized.

For each new entry, record **date, operator/agent, branch/commit, question,
measured result, evidence path, cost basis, decision and remaining uncertainty**.
Update the working guidance when evidence changes it; preserve earlier dated
results and mark superseded conclusions explicitly. Pull the latest notes before
editing, merge both agents' findings, and commit/push the update with the work.
