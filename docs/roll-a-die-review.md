# Pick up and roll a die — task review

Assessment date: 2026-11-03. Current scorer: `roll-a-die-v2`; original physics recordings from the first task implementation.

**Verdict:** the concrete scoring loophole is fixed and the source, test suite,
reviewer guide and recorded evidence are prepared. **Required media upload is
still pending the team token**, so the submission package is not yet complete.
The corrected scorer re-evaluates the original measured trajectories; it does
not claim fresh physics runs. Regional GPU capacity blocked two restart attempts
for additional repeats. Acceptance remains uncertain, principally because of
novelty/significance, the blank-cube abstraction and manual auditability. No PR
has been opened or authorized.

## What we built

The robot must pick up a small blue cube, release it so it tumbles like a die,
and leave it untouched until it stops. The intended application is assisting
with tabletop games; category: **Societal relevance**.

| Item | Specification |
|---|---|
| Robot and simulator | Calibrated two-arm YAM station; Isaac Sim 6.1 / Isaac Lab-Arena. |
| Die surrogate | One blue, unmarked, sharp-edged 16 × 16 × 16 mm cube; mass 5 g. |
| Table | 1.10 × 1.30 m; surface z = 0.7475 m, centre x = 0.36 m, y = 0. |
| Initial cube pose | Centre (0.20, 0.16, 0.7555) m; identity orientation. |
| Trial settings | Fixed layout, seed 0, no object jitter; 20 Hz actions/audit, 240 Hz physics. |
| Allowance | 1,200 actions / 60 simulated seconds per episode. |
| Fidelity | Primitive collision/friction defaults; no rounded edges, pips, numbered outcome or calibrated physical-die friction. |

The scorer awards **0.25** for a verified pickup held at least 30 mm above the
table for 0.20 s; **0.5** for verified release and a maximum tilt excursion of at
least 90 degrees from the verified free-flight reference; **1.0** for that roll
followed by one second of stable rest on a face. Cumulative motion is diagnostic
only: repeated small rocking no longer earns roll credit.
Falls outside the table bounds or renewed hand proximity after release erase
credit. Pure vertical-axis spin and rotation while held earn no roll credit.
Exact speed, clearance and rest predicates are in
[scoring.py](../tasks/roll-a-die/scoring.py) and
[task.json](../tasks/roll-a-die/task.json).

## What actually happened

| Evaluation | Result | Simulated time | Runner wall time |
|---|---|---:|---:|
| Scripted demo, trial 004 | **1.0** under v2 replay; pickup at 4.60 s, release at 8.00 s, 133.207° maximum tilt excursion, 164.434° cumulative motion and 1.00 s rest. | 9.30 s | 321.206 s, including shader compilation. |
| Dream-1 clean baseline | **0.0** under v2 replay; no verified pickup; 25 requests in one session, no retries. | 60.00 s | 197.996 s |

The demonstration commands only robot joints/gripper; it does not teleport the
cube. V2 replay preserves both scores and the demo's 9.30-second termination;
input hashes and results are in [VALIDATION.json](../tasks/roll-a-die/VALIDATION.json).
Joint speeds stayed within published limits and the videos were visually
reviewed. All **46 tests passed** (33 scorer, 10 bridge and 3 recorded-evidence checks), including 11 new regression and
boundary cases. The earlier Dream run suffered repeated session expiry and is
excluded as the baseline. Development attempts changed the demonstration;
there is only **one successful run of the final version**, not a measured success
rate or a real-robot demonstration.

At the observed Brev rate, the clean Dream run estimates $0.18 and the final
demo $0.29, excluding separate Dream API charges. Initial setup and debugging
are additional. At 12:24 UTC the first-session snapshot had $3.05 posted spend
and a conservative $4.43 elapsed-time estimate. The later 13:15 snapshot had
$3.84 total posted spend; billing lag and retained storage prevent assigning
that difference to the failed restart attempts. These are not settled invoices. See [shared cost notes](../TEAM_LEARNINGS.md).

## Is it a roll, and is it random?

**Yes, it demonstrates the simulated robot picking up, freely tumbling and
settling a die-shaped object.** The 164.434 degrees is accumulated tumble, not a
complete revolution; net orientation change relative to vertical from release
to rest was 103.204 degrees. An earlier attempt managed only 30.274 degrees.

**Randomness is not tested or deliberately introduced.** With the same initial
state and scripted motion, we expect similar results, but have not tested exact
repeatability. Numerical physics differences may occur. The cube has no face
labels, and no evidence establishes varying outcomes, equal face probabilities
or fairness. Those would require a separately designed repeated-trial study.

## Acceptance assessment

The competition requires importance, construct validity, simple unambiguous
scoring, reproducibility and feasibility; see [AGENTS.md](../AGENTS.md).

| Criterion | Current assessment |
|---|---|
| Importance / novelty | Plausible tabletop-assistance relevance. Prior November 3 checks found no direct duplicate; coverage was limited and must be refreshed. A generic small-object toss may be judged insufficiently distinctive. |
| Construct validity | The recorded motion supports a tumbling release. The claim must remain physical manipulation, without implying random/fair dice play. Physical friction and grip realism remain uncalibrated. |
| Scoring | **Corrected in v2:** small rocking fails even after accumulating many revolutions of angular travel. A true ≥90° excursion qualifies, including a full revolution returning to the release pose. The exact telemetry checks remain harder to reproduce manually than a simple placement score. |
| Reproducibility / clarity | Fixed dimensions, pose, seed, versions and numeric logs are strong. [JUDGING.md](../tasks/roll-a-die/JUDGING.md) provides a camera/ruler cross-check and explicitly discloses where ordinary footage cannot resolve exact telemetry predicates. |
| Feasibility | One full-score simulated demo supports feasibility within the allowance. Repeated success, sensitivity and physical-robot performance remain untested. |

To complete the required package, upload the prepared Dream/demo videos and
setup image and put the returned media ID in `task.json`. The corrected
simulation scores are supported by recorded-state replay; extra GPU repetitions
would add confidence but have not occurred. Refresh the authenticated live-board
novelty check before any eventual PR. Do not submit without the user's explicit
instruction.

Comparable **Societal relevance** tasks are the official
[telescoping-lamp template](https://github.com/robocurve/benchmark-tasks/blob/main/examples/task.json)
and pending [cable identification](https://github.com/robocurve/benchmark-tasks/pull/12)
and [cable uncrossing](https://github.com/robocurve/benchmark-tasks/pull/13)
submissions. None is an accepted precedent. Reviewers receive the task text,
setup screenshot, full Dream and demo videos, and source/README; assessment uses
all five criteria above. [JUDGING.md](../tasks/roll-a-die/JUDGING.md) gives details.

Run commands and full implementation details:
[task README](../tasks/roll-a-die/README.md). Local, git-ignored evidence:
`artifacts/die-debug-004/`, `artifacts/die-dream-002/` and final media in
`artifacts/roll-a-die/`. Those full local folders are not downloaded with a Git
clone; the three anonymous compressed trajectories in the task
[`evidence/`](../tasks/roll-a-die/evidence/) directory are included for offline verification.
